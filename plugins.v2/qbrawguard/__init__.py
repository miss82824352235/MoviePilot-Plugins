import re
import time
import threading
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

from app.helper.downloader import DownloaderHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType

from .constants import CONFIG_DEFAULTS, DEFAULT_PATTERNS, PLUGIN_VERSION, TITLE_HINTS
from .downloader import get_file_names_from_chain, get_file_names_from_chain_with_retry
from .matcher import compile_patterns, match_raw_disc
from .notifier import build_download_style_notice, detect_format, notification_type, safe_format_hint
from .orchestrator import full_cleanup, handle_download_added, hit, scan, torrent_gone
from .status import STATUS_COLOR_PROP, STATUS_TEXT_CLASS, build_check_status
from .ui import build_form, build_page
from .utils import clean_line, display_title, format_size, format_time, notice_image, short_name, site_name, suspect_name, value_of


class QBRawGuard(_PluginBase):
    """
    ============================================================
    原盘通知 v2.8.10 — 事件驱动秒级拦截 · 基于媒体管理系统彻底清理
    ============================================================
    事件驱动（DownloadAdded）：新种子秒级响应，不受标题预检限制
    快速拦截（Fast）：标题预检 → 文件结构正则匹配 → 命中处理
    彻底清理：基于媒体管理系统查找并删除所有关联痕迹（转移记录、下载历史、媒体库文件）
    ============================================================
    """
    plugin_name = "原盘通知"
    plugin_desc = "智能拦截 BDMV / ISO / DVD 原盘种子，事件驱动秒级响应；命中后基于媒体管理系统彻底清理所有关联痕迹，杜绝 Emby 无法播放的媒体污染。"
    plugin_icon = "https://raw.githubusercontent.com/miss82824352235/MoviePilot-Plugins/main/icons/QBRawGuard.png"
    plugin_version = PLUGIN_VERSION
    plugin_author = "MoviePilot Agent"
    author_url = "https://github.com/jxxghp/MoviePilot/pull/5687"
    plugin_config_prefix = "qbrawguard_"
    plugin_order = 29
    auth_level = 1

    TITLE_HINTS = TITLE_HINTS
    DEFAULT_PATTERNS = DEFAULT_PATTERNS
    CONFIG_DEFAULTS = CONFIG_DEFAULTS

    # ═══════════════════════════════════════════════════════════
    # 生命周期
    # ═══════════════════════════════════════════════════════════

    def init_plugin(self, config: dict = None):
        c = config or {}
        self.downloader_helper = DownloaderHelper()

        # 统一从 CONFIG_DEFAULTS 取字段，类型保持原样，不在每个字段上单独 bool/int 转换
        for k, default in self.CONFIG_DEFAULTS.items():
            v = c.get(k, default)
            if isinstance(default, bool):
                v = bool(v)
            elif isinstance(default, int) and not isinstance(default, bool):
                try:
                    v = int(v) if v is not None else default
                except (TypeError, ValueError):
                    v = default
            setattr(self, k, v)

        # 后置归一化与边界处理
        self.interval = max(self.interval, 1)
        if self.action not in ("stop", "delete"):
            self.action = "stop"
        if not self.alert_image:
            self.alert_image = self.CONFIG_DEFAULTS["alert_image"]
        if not self.patterns:
            self.patterns = self.DEFAULT_PATTERNS
        self.regex = self._compile(self.patterns)
        self._svc_cache = {"ts": 0.0, "items": {}}

        self.processed = self.get_data("processed") or {}
        self._survivors: set = set()
        self._fast_running = False
        self._full_running = False
        self._lock = threading.Lock()
        self._cleaning: set = set()
        self._oplog: list = self.get_data("oplog") or []
        self._rescan_queue: dict = self.get_data("rescan_queue") or {}
        # 状态检查缓存（避免 get_page 每次请求都查 DB）
        self._status_cache = {"ts": 0, "checks": None}

        self.eventmanager.register(EventType.DownloadAdded)(self.on_download_added)

        # 持久化时回写 patterns 当前值（可能是默认或用户自定义）
        self.update_config({k: getattr(self, k) for k in self.CONFIG_DEFAULTS})
        if self.enabled:
            logger.info(f"{self.plugin_name} v{self.plugin_version} 已启用")

    def get_state(self) -> bool:
        return self.enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return [{"cmd": "/test_raw_notify", "event": "TestRawNotify", "desc": "测试原盘通知"}]

    def get_api(self) -> List[Dict[str, Any]]:
        return [{
            "path": "/test_notify",
            "endpoint": self._test_notify,
            "methods": ["GET", "POST"],
            "auth": "apikey",
            "summary": "测试原盘通知发送",
            "description": "发送一条测试通知到所选 MoviePilot 通知场景，验证通知通道是否正常",
        }, {
            "path": "/manual_rescan",
            "endpoint": self._manual_rescan_api,
            "methods": ["POST"],
            "auth": "apikey",
            "summary": "手动彻底清理关联痕迹",
            "description": "对所有已拦截的种子，基于媒体管理系统查找并删除所有关联痕迹（转移记录、下载历史、媒体库文件）",
        }]

    def _test_notify(self) -> dict:
        """发送融合下载通知样式的模拟原盘拦截通知。"""
        try:
            title = f"{self.test_title} 原盘格式拦截"
            text = self._build_download_style_notice(
                name=self.test_title,
                matched=[self.test_format],
                downloader="QB",
                torrent={
                    "name": self.test_subtitle,
                    "tags": self.test_tags,
                    "num_seeds": self.test_seeders,
                    "site": self.test_site,
                },
                extra=self.test_message,
                fmt=self.test_format,
            )
            self.post_message(
                mtype=self._notification_type(),
                title=title,
                text=text,
                image=self._notice_image(),
            )
            logger.info(f"{self.plugin_name} 模拟拦截测试通知已发送")
            self._add_oplog("测试通知", 0, 0, 1, 0)
            return {"success": True, "message": "模拟原盘拦截通知已发送，请检查所选通知场景对应的接收端"}
        except Exception as e:
            logger.error(f"{self.plugin_name} 测试通知失败：{e}")
            return {"success": False, "message": f"发送失败：{e}"}

    def _manual_rescan_api(self) -> dict:
        """手动触发一次 MP 原生语义清理，只按 hash 精确清理关联记录。"""
        try:
            total_cleaned = 0
            errors = []
            for h, info in list(self.processed.items()):
                if info.get("action") != "delete":
                    continue
                # 手动回扫通常发生在下载器任务已处理后，允许清理残留源文件。
                result = cleanup_by_hash(h, delete_src=True, delete_dest=True, eventmanager=self.eventmanager)
                total_cleaned += result.total
                errors.extend(result.errors)
                if result.total > 0:
                    logger.info(f"{self.plugin_name} 手动清理 {self._short_name(info.get('name', ''))}：{result.total}项")

            if total_cleaned > 0:
                msg = f"手动彻底清理完成，删除 {total_cleaned} 项关联痕迹"
                logger.info(f"{self.plugin_name} {msg}")
            else:
                msg = "手动彻底清理完成，未发现关联痕迹"
            if errors:
                msg += f"，异常 {len(errors)} 项"

            self._add_oplog("手动清理", 0, 0, 0, total_cleaned, sample="manual", err="; ".join(errors[:2]))
            return {"success": not errors, "message": msg, "cleaned": total_cleaned, "errors": errors[:5]}
        except Exception as e:
            logger.error(f"{self.plugin_name} 手动彻底清理失败：{e}")
            return {"success": False, "message": f"手动彻底清理失败：{e}"}

    def stop_service(self):
        with self._lock:
            self._fast_running = False
            self._full_running = False

    # ═══════════════════════════════════════════════════════════
    # 类级懒加载工具（避免每次扫描/回扫重复实例化）
    # ═══════════════════════════════════════════════════════════



    # ═══════════════════════════════════════════════════════════
    # 调度器
    # ═══════════════════════════════════════════════════════════

    def get_service(self) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        services = []
        if self.fast_scan_enabled:
            services.append({
                "id": "QBRawGuardFast", "name": "QB原盘快速拦截", "trigger": "interval",
                "func": self._run_fast_scan,
                "kwargs": {"seconds": max(self.interval, 1) * 60},
            })
        if getattr(self, "full_scan_enabled", False):
            full_interval = int(getattr(self, "full_interval", 0) or 0)
            if full_interval <= 0:
                full_interval = max(self.interval, 1) * 5
            services.append({
                "id": "QBRawGuardFull", "name": "QB原盘全量兜底", "trigger": "interval",
                "func": self._run_full_scan,
                "kwargs": {"seconds": max(full_interval, 5) * 60},
            })
        return services

    def _run_fast_scan(self):
        self._run_locked("_fast_running", self._scan, "fast")

    def _run_full_scan(self):
        self._run_locked("_full_running", self._scan, "full")

    def _run_locked(self, flag: str, func, *args):
        """通用单例运行包装：避免同名任务并发执行。"""
        with self._lock:
            if getattr(self, flag, False):
                return
            setattr(self, flag, True)
        try:
            func(*args)
        finally:
            with self._lock:
                setattr(self, flag, False)

    # ═══════════════════════════════════════════════════════════
    # 核心扫描
    # ═══════════════════════════════════════════════════════════

    def _scan(self, mode: str = "fast"):
        """执行扫描，实际编排逻辑位于 orchestrator.py。"""
        return scan(self, mode)

    # ═══════════════════════════════════════════════════════════
    # 事件驱动
    # ═══════════════════════════════════════════════════════════

    def on_download_added(self, event):
        """处理下载添加事件，实际编排逻辑位于 orchestrator.py。"""
        return handle_download_added(self, event)

    # ═══════════════════════════════════════════════════════════
    # 下载器
    # ═══════════════════════════════════════════════════════════

    def _services(self) -> Dict[str, Any]:
        now = time.time()
        cache = getattr(self, "_svc_cache", {"ts": 0.0, "items": {}})
        if cache.get("items") and now - float(cache.get("ts") or 0) < 30:
            return cache.get("items") or {}
        services = (
            self.downloader_helper.get_services(name_filters=self.downloaders)
            if self.downloaders else self.downloader_helper.get_services()
        )
        items = {n: s for n, s in (services or {}).items()
                 if s and s.instance
                 and self.downloader_helper.is_downloader("qbittorrent", service=s)
                 and not s.instance.is_inactive()}
        self._svc_cache = {"ts": now, "items": items}
        return items

    def _get_service(self, name: str):
        if not name:
            return None
        try:
            svc = self.downloader_helper.get_service(name)
            if svc and svc.instance \
               and self.downloader_helper.is_downloader("qbittorrent", service=svc) \
               and not svc.instance.is_inactive():
                return svc
        except Exception:
            pass
        return None

    def _skip(self, torrent: Any) -> bool:
        if self.include_completed:
            return False
        state = str(self._val(torrent, "state") or "").lower()
        return float(self._val(torrent, "progress") or 0) >= 1 or \
            any(x in state for x in ("upload", "seed", "stalledup"))

    def _processed_ok(self, h: str, present: bool = False) -> bool:
        item = self.processed.get(str(h).lower()) or self.processed.get(h)
        if not item:
            return False
        if present and self.action == "delete" and item.get("ok"):
            logger.info(f"{self.plugin_name} 发现已标记成功但仍存在的任务，重新执行删除：{self._short_name(item.get('name') or h)}")
            return False
        return bool(item.get("ok") or not self.retry_failed)

    def _mark_nonsuspect(self, h: str, name: str = ""):
        hl = str(h).lower()
        self._survivors.add(hl)
        if len(self._survivors) > 5000:
            self._survivors = set(list(self._survivors)[-3000:])

    def _file_names(self, service: Any, h: str, downloader: str) -> List[str]:
        """通过 MoviePilot Chain 读取下载器真实文件列表；原盘判定不得直接使用种子名。"""
        return get_file_names_from_chain(self.chain, h, downloader)

    def _file_names_with_retry(self, service: Any, h: str, downloader: str) -> List[str]:
        """事件触发后通过 MoviePilot Chain 短轮询等待真实文件列表就绪。"""
        return get_file_names_from_chain_with_retry(self.chain, h, downloader, attempts=5, delay=1.5)

    # ═══════════════════════════════════════════════════════════
    # 匹配
    # ═══════════════════════════════════════════════════════════

    def _match(self, names: List[str]) -> List[str]:
        """基于下载器真实文件列表匹配原盘结构。"""
        return match_raw_disc(names, self.regex)

    @staticmethod
    def _compile(patterns: str) -> List[re.Pattern]:
        """编译原盘判定正则。"""
        return compile_patterns(patterns)

    # ═══════════════════════════════════════════════════════════
    # 命中
    # ═══════════════════════════════════════════════════════════

    def _hit(self, downloader: str, service: Any, torrent: Any, matched: List[str]):
        """处理命中动作，实际编排逻辑位于 orchestrator.py。"""
        return hit(self, downloader, service, torrent, matched)

    # ═══════════════════════════════════════════════════════════
    # 四件套
    # ═══════════════════════════════════════════════════════════

    def _full_cleanup(self, downloader: str, h: str, name: str, matched: List[str]):
        """彻底清理，实际编排逻辑位于 orchestrator.py。"""
        return full_cleanup(self, downloader, h, name, matched)

    def _torrent_gone(self, downloader: str, h: str) -> bool:
        """确认下载器任务是否已消失，实际逻辑位于 orchestrator.py。"""
        return torrent_gone(self, downloader, h)





    # ═══════════════════════════════════════════════════════════
    # 通知（修复：走系统通知通道）
    # ═══════════════════════════════════════════════════════════

    def _record(self, h: str, downloader: str, name: str, matched: List[str], ok: bool):
        self.processed[h] = {
            "downloader": downloader, "name": name,
            "matched": matched[:10], "action": self.action, "ok": ok,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if len(self.processed) > 1000:
            self.processed = dict(list(self.processed.items())[-1000:])
        self.save_data("processed", self.processed)

    def _notification_type(self):
        """返回当前配置对应的 MoviePilot 通知类型。"""
        return notification_type(self.notify_type)

    def _build_download_style_notice(self, name: str, matched: List[str], downloader: str = "QB",
                                     torrent: Any = None, extra: str = "", fmt: str = "") -> str:
        """构建接近 MoviePilot 下载通知的原盘拦截通知，不暴露 hash 和真实路径。"""
        return build_download_style_notice(
            name=name, matched=matched, action=self.action,
            torrent_info=self._torrent_notice_info(torrent, name),
            extra=extra, fmt=fmt, fallback_tag=self.tag,
        )


    @staticmethod
    def _detect_format(matched: List[str]) -> str:
        """根据命中文件名归纳原盘格式。"""
        return detect_format(matched)

    @staticmethod
    def _safe_format_hint(path: str) -> str:
        """只返回格式层面的脱敏命中依据，不暴露真实路径。"""
        return safe_format_hint(path)

    def _notify(self, downloader: str, name: str, matched: List[str], torrent: Any = None):
        info = self._torrent_notice_info(torrent, name)
        display_name = info.get("display_title") or self._display_title(name)
        text = self._build_download_style_notice(
            name=display_name, matched=matched, downloader=downloader, torrent=torrent
        )
        title = f"{display_name} 原盘格式拦截"
        try:
            self.post_message(
                mtype=self._notification_type(),
                title=title, text=text, image=self._notice_image(),
            )
            logger.info(f"{self.plugin_name} 通知已发送（系统通知通道）")
        except Exception as e:
            logger.warning(f"{self.plugin_name} 通知发送失败：{e}")
            self._add_oplog("通知", 0, 0, 0, 0, err=f"通知失败：{e}")

    # ═══════════════════════════════════════════════════════════
    # 健康检查
    # ═══════════════════════════════════════════════════════════

    # 状态→Vuetify 主题色 class 映射（自动跟随浅色/深色模式）
    _STATUS_TEXT_CLASS = STATUS_TEXT_CLASS
    _STATUS_COLOR_PROP = STATUS_COLOR_PROP

    def _check_status(self) -> List[dict]:
        """运行时状态检查，返回首页/设置页展示用检查项。"""
        return build_check_status(self, self._services, self._notification_type)

    # ═══════════════════════════════════════════════════════════
    # 操作日志
    # ═══════════════════════════════════════════════════════════

    def _add_oplog(self, mode: str, total: int, checked: int, hits: int,
                   elapsed: float, err: str = "", sample: str = "", hit_names: list = None):
        if err:
            detail = err
        elif mode in ("延迟回扫", "手动回扫"):
            detail = f"清理 {hits} 条孤儿"
            if sample and sample != "manual":
                detail += f"（{self._short_name(sample)}）"
        else:
            if hit_names:
                # 有具体命中列表：显示种子名和操作
                names_text = "、".join([self._short_name(n) for n in hit_names[:5]])
                suffix = f"... 等{len(hit_names)}个" if len(hit_names) > 5 else ""
                detail = f"命中 {names_text}{suffix}，已{'删除' if self.action == 'delete' else '停止'}"
            else:
                detail = f"扫描 {total} 个任务" + (f"（命中 {hits}）" if hits else "，无命中")
        entry = {
            "time": datetime.now().strftime("%m-%d %H:%M"),
            "mode": mode,
            "detail": detail,
            "elapsed": f"{elapsed:.1f}s" if isinstance(elapsed, (int, float)) else str(elapsed),
        }
        self._oplog.insert(0, entry)
        if len(self._oplog) > 100:
            self._oplog = self._oplog[:100]
        self.save_data("oplog", self._oplog)
        # 同时输出到系统日志（订阅助手风格：直接使用 logger.info）
        log_line = f"原盘通知 [{mode}] {detail}"
        if isinstance(elapsed, (int, float)) and elapsed > 0:
            log_line += f"（{elapsed:.1f}s）"
        logger.info(log_line)

    # ═══════════════════════════════════════════════════════════
    # 字符串工具
    # ═══════════════════════════════════════════════════════════

    def _torrent_notice_info(self, torrent: Any, fallback_name: str = "") -> Dict[str, str]:
        info = self._history_notice_info(torrent, fallback_name)
        torrent_title = self._val(torrent, "name", "title") or fallback_name
        if not info.get("torrent_title"):
            info["torrent_title"] = self._clean_line(torrent_title)
        if not info.get("tags"):
            info["tags"] = self._clean_line(self._val(torrent, "tags", "tag"))
        seeders = self._val(torrent, "num_seeds", "seeders", "seeds")
        if not info.get("seeders") and seeders not in (None, ""):
            info["seeders"] = str(seeders)
        site = self._val(torrent, "site", "site_name", "tracker")
        if not info.get("site"):
            info["site"] = self._site_name(site)
        size = self._val(torrent, "size", "total_size")
        if not info.get("size"):
            info["size"] = self._fmt_size(size)
        added = self._val(torrent, "added_on", "addition_date", "created_at")
        if not info.get("pubdate"):
            info["pubdate"] = self._fmt_time(added)
        if not info.get("promotion"):
            info["promotion"] = self._clean_line(self._val(torrent, "volume_factor", "promotion"))
        if not info.get("hit_and_run"):
            info["hit_and_run"] = self._clean_line(self._val(torrent, "hit_and_run", "hnr"))
        desc = self._val(torrent, "description", "subtitle", "comment")
        if not info.get("description"):
            info["description"] = self._clean_line(desc)
        return info

    def _history_notice_info(self, torrent: Any, fallback_name: str = "") -> Dict[str, str]:
        """优先从 MoviePilot 下载历史提取站点、质量、促销等下载通知元数据。"""
        history = self._download_history(torrent, fallback_name)
        if not history:
            return {}
        note = self._val(history, "note") or {}
        if not isinstance(note, dict):
            note = {}
        torrent_name = self._val(history, "torrent_name") or self._val(history, "title") or fallback_name
        title = self._val(history, "title") or ""
        year = self._val(history, "year") or ""
        seasons = self._val(history, "seasons") or ""
        display_title = f"{title} ({year}){seasons}" if title and year else ""
        return {
            "display_title": self._clean_line(display_title),
            "torrent_title": self._clean_line(torrent_name),
            "site": self._clean_line(self._val(history, "torrent_site") or note.get("site") or note.get("site_name")),
            "quality": self._clean_line(note.get("quality") or note.get("quality_name") or note.get("resource_pix") or note.get("resource_type")),
            "size": self._clean_line(note.get("size") or note.get("torrent_size")),
            "pubdate": self._clean_line(note.get("pubdate") or note.get("publish_time") or self._val(history, "date")),
            "seeders": self._clean_line(note.get("seeders") or note.get("num_seeds") or note.get("seeder")),
            "promotion": self._clean_line(note.get("promotion") or note.get("volume_factor") or note.get("free_state")),
            "hit_and_run": self._clean_line(note.get("hit_and_run") or note.get("hr") or note.get("hit_run")),
            "tags": self._clean_line(note.get("tags") or note.get("labels")),
            "description": self._clean_line(self._val(history, "torrent_description") or note.get("description") or note.get("subtitle")),
        }

    def _download_history(self, torrent: Any, fallback_name: str = "") -> Optional[Any]:
        """按 hash 优先反查下载历史，失败时按最近记录中的种子名做窄匹配。"""
        try:
            from app.db.downloadhistory_oper import DownloadHistoryOper
            oper = DownloadHistoryOper()
            h = self._val(torrent, "hash", "hashString", "download_hash")
            if h:
                history = oper.get_by_hash(str(h))
                if history:
                    return history
            torrent_name = self._clean_line(self._val(torrent, "name", "title") or fallback_name).lower()
            if not torrent_name:
                return None
            for history in (oper.list_by_page(page=1, count=50) or []):
                name = self._clean_line(self._val(history, "torrent_name") or "").lower()
                if name and (name == torrent_name or name in torrent_name or torrent_name in name):
                    return history
        except Exception as e:
            logger.debug(f"{self.plugin_name} 下载历史元数据查询失败：{e}")
        return None

    @staticmethod
    def _clean_line(value: Any) -> str:
        """清理通知单行文本。"""
        return clean_line(value)

    @staticmethod
    def _fmt_size(value: Any) -> str:
        """格式化文件大小。"""
        return format_size(value)

    @staticmethod
    def _fmt_time(value: Any) -> str:
        """格式化时间戳。"""
        return format_time(value)

    @staticmethod
    def _site_name(value: Any) -> str:
        """提取站点显示名。"""
        return site_name(value)

    @staticmethod
    def _display_title(name: str) -> str:
        """生成通知标题显示名。"""
        return display_title(name)

    def _suspect_name(self, name: str) -> bool:
        """标题预检：只用于快速拦截降噪，最终命中必须来自真实文件列表。"""
        return suspect_name(name, self.TITLE_HINTS)

    def _notice_image(self) -> str:
        """通知图片兜底。"""
        return notice_image(getattr(self, "alert_image", ""))

    @staticmethod
    def _short_name(name: str) -> str:
        """返回适合日志展示的短名称。"""
        return short_name(name)

    @staticmethod
    def _val(obj: Any, *keys: str) -> Any:
        """按字段名从 dict 或对象中读取值。"""
        return value_of(obj, *keys)

    # ═══════════════════════════════════════════════════════════
    # 集成仪表盘 get_page()
    #  Apple Liquid Glass 风格 · 统计 + 健康检查 + 操作
    # ═══════════════════════════════════════════════════════════


    # ═══════════════════════════════════════════════════════════
    # 首页（get_page）：统计概览 + 健康检查 + 可交互操作按钮
    # ═══════════════════════════════════════════════════════════

    def get_page(self) -> List[dict]:
        """返回插件详情页面。"""
        return build_page(self)

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """返回插件配置表单与默认值。"""
        return build_form(self)
