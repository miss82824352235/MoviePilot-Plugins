import re
import time
import threading
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

from app.helper.downloader import DownloaderHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType, NotificationType
from app.core.config import settings

from .cleaner import cleanup_by_hash
from .constants import CONFIG_DEFAULTS, DEFAULT_PATTERNS, PLUGIN_VERSION, TITLE_HINTS
from .downloader import get_file_names_from_chain, get_file_names_from_chain_with_retry
from .matcher import compile_patterns, match_raw_disc
from .notifier import build_download_style_notice, detect_format, notification_type, safe_format_hint
from .status import STATUS_COLOR_PROP, STATUS_TEXT_CLASS, build_check_status
from .utils import clean_line, display_title, format_size, format_time, notice_image, short_name, site_name, suspect_name, value_of


class QBRawGuard(_PluginBase):
    """
    ============================================================
    原盘通知 v2.8.3 — 事件驱动秒级拦截 · 基于媒体管理系统彻底清理
    ============================================================
    事件驱动（DownloadAdded）：新种子秒级响应，不受标题预检限制
    快速拦截（Fast）：标题预检 → 文件结构正则匹配 → 命中处理
    彻底清理：基于媒体管理系统查找并删除所有关联痕迹（转移记录、下载历史、媒体库文件）
    ============================================================
    """
    plugin_name = "原盘通知"
    plugin_desc = "智能拦截 BDVM / ISO / DVD 原盘种子，事件驱动秒级响应；命中后基于媒体管理系统彻底清理所有关联痕迹，杜绝 Emby 无法播放的媒体污染。"
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
            "methods": ["GET"],
            "auth": "apikey",
            "summary": "测试原盘通知发送",
            "description": "发送一条测试通知到 Telegram，验证通知通道是否正常",
        }, {
            "path": "/manual_rescan",
            "endpoint": self._manual_rescan_api,
            "methods": ["GET"],
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

    # ═══════════════════════════════════════════════════════════
    # 类级懒加载工具（避免每次扫描/回扫重复实例化）
    # ═══════════════════════════════════════════════════════════

    @property
    def _sc(self):
        """懒加载 StorageChain 实例，线程安全（只读操作）。"""
        if not hasattr(self, "__sc"):
            from app.chain.storage import StorageChain
            self.__sc = StorageChain()
        return self.__sc

    @property
    def _to(self):
        """懒加载 TransferHistoryOper 实例。"""
        if not hasattr(self, "__to"):
            from app.db.transferhistory_oper import TransferHistoryOper
            self.__to = TransferHistoryOper()
        return self.__to

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
        return services

    def _run_fast_scan(self):
        self._run_locked("_fast_running", self._scan, "fast")

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
        is_fast = mode == "fast"
        label = "快速拦截" if is_fast else "全量兜底"
        start = time.time()
        total = checked = hits = 0
        hit_names: List[str] = []
        try:
            services_dict = self._services()
            if not services_dict:
                self._add_oplog(label, 0, 0, 0, 0, err="无可用下载器")
                logger.warning(f"{self.plugin_name} {label} 无可用 QB 下载器")
                return
            for downloader, service in services_dict.items():
                torrents, err = service.instance.get_torrents()
                if err:
                    logger.warning(f"{self.plugin_name} 获取 {downloader} 种子列表失败：{err}")
                    continue
                for torrent in torrents or []:
                    h = self._val(torrent, "hash", "hashString")
                    name = self._val(torrent, "name", "title") or ""
                    if not h or self._skip(torrent):
                        continue
                    with self._lock:
                        if self._processed_ok(h, present=True):
                            continue
                    total += 1
                    if is_fast and not self._suspect_name(name):
                        continue
                    if not is_fast:
                        with self._lock:
                            if str(h).lower() in self._survivors:
                                continue
                    checked += 1
                    try:
                        files = self._file_names(service, h, downloader)
                        if not files:
                            logger.debug(f"{self.plugin_name} {label} 跳过文件列表未就绪任务：{self._short_name(name)}")
                            continue
                        matched = self._match(files)
                        if matched:
                            hits += 1
                            self._hit(downloader, service, torrent, matched)
                            hit_names.append(name)
                        else:
                            with self._lock:
                                self._mark_nonsuspect(h, name)
                    except Exception as e:
                        logger.error(f"{self.plugin_name} {label} 异常 [{self._short_name(name)}]: {e}")
        except Exception as e:
            logger.error(f"{self.plugin_name} {label} 严重异常：{e}")
        finally:
            elapsed = time.time() - start
            self._add_oplog(label, total, checked, hits, elapsed,
                            err="" if total > 0 else "无待检任务",
                            hit_names=hit_names if hit_names else None)

    # ═══════════════════════════════════════════════════════════
    # 事件驱动
    # ═══════════════════════════════════════════════════════════

    def on_download_added(self, event):
        if not self.enabled:
            return
        h = event.event_data.get("hash")
        if not h:
            return
        with self._lock:
            if self._processed_ok(h, present=True):
                return
        downloader = event.event_data.get("downloader")
        service = self._get_service(downloader)
        if not service:
            return
        try:
            files = self._file_names_with_retry(service, h, downloader)
            if not files:
                logger.debug(f"{self.plugin_name} 事件触发后文件列表仍未就绪，等待定时扫描兜底：{h[:8]}")
                return
            matched = self._match(files)
            if not matched:
                return
            torrents, err = service.instance.get_torrents(ids=h)
            if err or not torrents:
                return
            self._hit(downloader, service, torrents[0], matched)
        except Exception as e:
            logger.error(f"{self.plugin_name} 事件处理异常：{e}")

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

    @staticmethod
    def _file_names(self, service: Any, h: str, downloader: str) -> List[str]:
        """通过 MoviePilot Chain 读取下载器真实文件列表；原盘判定不得直接使用种子名。"""
        return get_file_names_from_chain(self.chain, h, downloader)

    @staticmethod
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
        h = str(self._val(torrent, "hash", "hashString") or "").lower()
        name = self._val(torrent, "name", "title") or h
        with self._lock:
            if h in self._cleaning:
                return
            self._cleaning.add(h)
        if self.action == "delete":
            self._record(h, downloader, name, matched, False)
            self._full_cleanup(downloader, h, name, matched)
        else:
            ok = bool(self.chain.stop_torrents(hashs=[h], downloader=downloader))
            if self.tag:
                try:
                    self.chain.set_torrents_tag(hashs=[h], tags=[self.tag], downloader=downloader)
                except Exception:
                    pass
            self._record(h, downloader, name, matched, ok)
            with self._lock:
                self._cleaning.discard(h)
        if self.notify:
            self._notify(downloader, name, matched, torrent)

    # ═══════════════════════════════════════════════════════════
    # 四件套
    # ═══════════════════════════════════════════════════════════

    def _full_cleanup(self, downloader: str, h: str, name: str, matched: List[str]):
        """彻底清理：复用 MP Chain 与整理记录删除语义清理关联痕迹。"""
        try:
            # 先暂停，降低整理链路继续处理原盘任务的概率。
            try:
                self.chain.stop_torrents(hashs=[h], downloader=downloader)
            except Exception as err:
                logger.debug(f"{self.plugin_name} 删除前暂停任务失败：{err}")

            # MP 侧只按 hash 精确清理，目标媒体库文件和转移记录走 MP 整理记录删除语义；
            # 源文件交给 remove_torrents(delete_file=True)，避免重复删除。
            clean_result = cleanup_by_hash(h, delete_src=False, delete_dest=True, eventmanager=self.eventmanager)
            media_deleted = clean_result.total
            logger.info(
                f"{self.plugin_name} MP侧清理：转移记录 {clean_result.transfer_records}，"
                f"媒体库文件 {clean_result.dest_files}，下载历史 {clean_result.download_histories}，"
                f"下载文件记录 {clean_result.download_files}"
            )
            for err in clean_result.errors[:3]:
                logger.warning(f"{self.plugin_name} MP侧清理异常：{err}")

            # 下载器任务和源文件删除统一走 MoviePilot 下载器 Chain。
            try:
                self.chain.remove_torrents(hashs=[h], delete_file=True, downloader=downloader)
            except Exception as err:
                logger.warning(f"{self.plugin_name} 删除下载器任务异常：{err}")

            time.sleep(2)
            deleted = self._torrent_gone(downloader, h)
            if not deleted:
                logger.warning(f"{self.plugin_name} 删除后任务仍存在，将保留失败状态等待下次重试：{self._short_name(name)}")

            with self._lock:
                if h in self.processed:
                    self.processed[h]["ok"] = deleted and not clean_result.errors
                    self.processed[h]["media_deleted"] = media_deleted
                    self.processed[h]["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if not deleted:
                        self.processed[h]["err"] = "删除后任务仍在下载器中"
                    elif clean_result.errors:
                        self.processed[h]["err"] = "; ".join(clean_result.errors[:2])
                    else:
                        self.processed[h].pop("err", None)
                    self.save_data("processed", self.processed)
                self._cleaning.discard(h)
                self._add_oplog("彻底清理", 0, 0, 0, media_deleted, sample=self._short_name(name))
        except Exception as e:
            logger.error(f"{self.plugin_name} 彻底清理异常 [{self._short_name(name)}]: {e}")
            with self._lock:
                self._cleaning.discard(h)

    def _torrent_gone(self, downloader: str, h: str) -> bool:
        """确认任务是否已从下载器消失，避免误把删除失败标记为成功。"""
        try:
            torrents = self.chain.list_torrents(hashs=[h], downloader=downloader, include_all_tags=True)
            return not torrents
        except Exception as e:
            logger.warning(f"{self.plugin_name} 删除结果确认异常：{e}")
            return False

    def _clean_one(self, history, h: str, name: str, storage_chain, oper):
        """兼容旧入口：单条整理历史清理已由 cleaner.py 承担。"""
        result = cleanup_by_hash(getattr(history, "download_hash", "") or h, delete_src=True, delete_dest=True, eventmanager=self.eventmanager)
        return result.total

    def _collect_media_items(self, hash: str, name: str) -> dict:
        """兼容旧入口：只按 hash 收集可自动清理的 MP 关联记录。"""
        try:
            from app.db.transferhistory_oper import TransferHistoryOper
            from app.db.downloadhistory_oper import DownloadHistoryOper
            return {
                "transfer_records": TransferHistoryOper().list_by_hash(hash) or [],
                "download_records": [h for h in [DownloadHistoryOper().get_by_hash(hash)] if h],
                "library_files": [],
            }
        except Exception as e:
            logger.warning(f"{self.plugin_name} 收集媒体项目异常：{e}")
            return {"transfer_records": [], "download_records": [], "library_files": []}

    def _extract_core_name(self, torrent_name: str) -> str:
        """提取种子名核心英文名"""
        if not torrent_name:
            return ""
        
        # 移除站点前缀 [MT], [HDS], [HDSky] 等
        import re
        name = re.sub(r'^\[[^\]]+\]', '', torrent_name)
        
        # 移除常见的质量/编码标记
        patterns_to_remove = [
            r'\b(1080p|720p|2160p|4k|uhd|bluray|blu-ray|remux|avc|hevc|h264|h265|x264|x265|'
            r'truehd|dts|ddp|aac|ac3|atmos|dovi|dv|hdr|sdr|10bit|8bit|'
            r'complete\.bluray|complete\.blu-ray|complete_uhd|'
            r'bdmv|certificate|video_ts|audio_ts|hvdvd_ts|'
            r'\.iso|\.img|\.nrg|\.mdf|\.mds|\.cue|\.bin|'
            r'-mteam|-hds|-hdsky|-chdbits|-52pt|-pter|'
            r'thor@hds|pete@hds|blu-ray\.diy|bluray\.diy|'
            r'blu-ray\.avc|bluray\.avc|bluray\.remux|blu-ray\.remux)\b',
            r'\.(mkv|mp4|ts|m2ts|iso|img|nrg|mdf|mds|cue|bin|srt|ass|ssa|sub|idx)$',
            r'\[.*?\]',  # 移除所有方括号内容
            r'\(.*?\)',  # 移除所有圆括号内容
        ]
        
        for pattern in patterns_to_remove:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # 清理多余空格和特殊字符
        name = re.sub(r'[._-]+', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        # 提取连续的英文单词（至少2个字母）
        words = re.findall(r'\b[a-z]{2,}\b', name.lower())
        if words:
            return ' '.join(words).title()
        
        return ""

    def _extract_year(self, torrent_name: str) -> str:
        """提取年份"""
        import re
        match = re.search(r'\b(19\d{2}|20\d{2})\b', torrent_name)
        return match.group(1) if match else ""

    def _delete_media_items(self, media_items: dict):
        """兼容旧入口：清理逻辑已迁移到 cleaner.py，避免按标题猜测删除媒体库文件。"""
        deleted_count = 0
        for record in media_items.get("transfer_records", []):
            h = getattr(record, "download_hash", "")
            if h:
                result = cleanup_by_hash(h, delete_src=True, delete_dest=True, eventmanager=self.eventmanager)
                deleted_count += result.total
        for record in media_items.get("download_records", []):
            try:
                from app.db.downloadhistory_oper import DownloadHistoryOper
                DownloadHistoryOper().delete_history(record.id)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"{self.plugin_name} 删除下载历史失败 id={getattr(record, 'id', '?')}：{e}")
        return deleted_count
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

    def _build_notice_text(self, name: str, matched: List[str], downloader: str = "QB",
                           site: str = "未知", seeders: str = "未知", tags: str = "原盘拦截",
                           subtitle: str = "", fmt: str = "", action: str = "", extra: str = "") -> str:
        """兼容旧调用，内部转为下载通知融合样式。"""
        return self._build_download_style_notice(
            name=name, matched=matched, downloader=downloader,
            torrent={"name": subtitle or name, "site": site, "num_seeds": seeders, "tags": tags},
            extra=extra, fmt=fmt,
        )

    @staticmethod
    @staticmethod
    def _detect_format(matched: List[str]) -> str:
        """根据命中文件名归纳原盘格式。"""
        return detect_format(matched)

    @staticmethod
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
    @staticmethod
    def _clean_line(value: Any) -> str:
        """清理通知单行文本。"""
        return clean_line(value)

    @staticmethod
    @staticmethod
    def _fmt_size(value: Any) -> str:
        """格式化文件大小。"""
        return format_size(value)

    @staticmethod
    @staticmethod
    def _fmt_time(value: Any) -> str:
        """格式化时间戳。"""
        return format_time(value)

    @staticmethod
    @staticmethod
    def _site_name(value: Any) -> str:
        """提取站点显示名。"""
        return site_name(value)

    @staticmethod
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
    @staticmethod
    def _short_name(name: str) -> str:
        """返回适合日志展示的短名称。"""
        return short_name(name)

    @staticmethod
    @staticmethod
    def _val(obj: Any, *keys: str) -> Any:
        """按字段名从 dict 或对象中读取值。"""
        return value_of(obj, *keys)

    # ═══════════════════════════════════════════════════════════
    # 集成仪表盘 get_page()
    #  Apple Liquid Glass 风格 · 统计 + 健康检查 + 操作
    # ═══════════════════════════════════════════════════════════

    def _glass_card_style(self, blur: int = 14, opacity: float = 0.55) -> str:
        """液态玻璃卡片 CSS（半透明 + 毛玻璃模糊 + 微妙边框）。"""
        return (
            f"background: rgba(var(--v-theme-surface), {opacity}); "
            f"backdrop-filter: blur({blur}px); "
            f"-webkit-backdrop-filter: blur({blur}px); "
            f"border: 1px solid rgba(var(--v-theme-on-surface), 0.06);"
        )

    # ═══════════════════════════════════════════════════════════
    # 首页（get_page）：统计概览 + 健康检查 + 可交互操作按钮
    # ═══════════════════════════════════════════════════════════

    def get_page(self) -> List[dict]:
        checks = self._check_status()
        icon = self.plugin_icon or ""
        return [
            {"component": "VCard", "props": {
                "variant": "flat", "elevation": "0", "rounded": "xl", "class": "mb-4 pa-4",
                "style": self._glass_card_style(blur=18, opacity=0.5),
            }, "content": [
                {"component": "VRow", "props": {"align": "center", "no-gutters": True}, "content": [
                    {"component": "VAvatar", "props": {"color": "primary", "variant": "tonal", "rounded": "lg", "size": 44},
                     "content": [
                        {"component": "VImg", "props": {"src": icon, "width": 28, "height": 28}}
                    ]},
                    {"component": "VCol", "props": {"class": "ml-3"}, "content": [
                        {"component": "div", "props": {"class": "text-h6 font-weight-bold"},
                         "text": f"原盘通知 v{self.plugin_version}"},
                        {"component": "div", "props": {"class": "text-body-2 text-medium-emphasis"},
                         "text": "BDMV / ISO / DVD 原盘拦截 · 事件驱动 + 定时扫描 + 延迟回扫"},
                    ]},
                    {"component": "VSpacer"},
                    {"component": "VChip", "props": {
                        "color": "success" if self.enabled else "grey", "variant": "flat", "size": "small",
                        "prepend-icon": "mdi-play-circle" if self.enabled else "mdi-pause-circle",
                        "text": "运行中" if self.enabled else "已停用"
                    }},
                ]},
            ]},
            self._stats_row(),
            {"component": "div", "props": {"class": "text-subtitle-2 font-weight-medium mb-2 mt-4"},
             "text": "系统健康检查"},
            self._health_row(checks),
            {"component": "VRow", "props": {"class": "mt-3"}, "content": [
                {"component": "VCol", "props": {"cols": 12, "md": 6}, "content": [
                    self._action_button("发送模拟拦截测试通知", "mdi-send", "warning", "test_notify")
                ]},
                {"component": "VCol", "props": {"cols": 12, "md": 6}, "content": [
                    self._action_button(f"手动回扫孤儿入库（队列 {len(self._rescan_queue)}）",
                                        "mdi-broom", "error", "manual_rescan")
                ]},
            ]},
            {"component": "VAlert", "props": {
                "type": "info", "variant": "tonal", "density": "compact", "class": "mt-3",
                "text": "点击右上角「设置」进入完整配置：拦截参数、通知通道、测试字段、识别规则。",
            }},
        ]

    # ═══════════════════════════════════════════════════════════
    # 设置页（3 Tab 分页：基本设置 / 通知与测试 / 高级规则）
    # ═══════════════════════════════════════════════════════════

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        try:
            opts = [{"title": c.name, "value": c.name} for c in self.downloader_helper.get_configs().values()
                    if "qb" in f"{getattr(c, 'type', '')}{c.name}".lower()]
        except Exception:
            opts = []
        form = [{"component": "VForm", "content": [
            *self._form_tabs(opts),
        ]}]
        defaults = {
            "enabled": False, "fast_scan_enabled": True, "full_scan_enabled": False,
            "downloaders": [], "interval": 2, "full_interval": 0,
            "action": "stop", "notify": True, "notify_type": "Agent", "tag": "原盘拦截",
            "include_completed": True, "retry_failed": True,
            "alert_image": "https://cdn-icons-png.flaticon.com/512/564/564619.png",
            "test_message": "站点：馒头\n质量：UHD HDR10 DoVi 2160p\n大小：92.61G\n种子：Avatar Fire and Ash 2025 2160p UHD Blu-ray DoVi HDR10 HEVC TrueHD 7.1-Thor@HDSky\n发布时间：2026-06-02 06:03:02\n做种数：111\n促销：50%\nHit&Run：否\n标签：中字 4k 中配 hdr10 DoVi\n描述：阿凡达：火与烬 / 阿凡达3 / 阿凡达3：带种者 / 阿凡达3：火与灰 / 阿凡达3：火与烬 【UHD原盘 DIY国语DTS配音 官译简繁粤/双语字幕】",
            "test_title": "阿凡达：火与烬 (2025)",
            "test_subtitle": "Avatar Fire and Ash 2025 2160p UHD Blu-ray DoVi HDR10 HEVC TrueHD 7.1-Thor@HDSky",
            "test_site": "馒头", "test_seeders": "111",
            "test_tags": "中字 4k 中配 hdr10 DoVi",
            "test_format": "光盘镜像文件",
            "patterns": self.DEFAULT_PATTERNS,
        }
        return form, defaults

    # ── Tab 分页容器（3 Tab）────────────────────────────────

    def _form_tabs(self, downloader_opts: list) -> List[dict]:
        titles = ["基本设置", "通知与测试", "高级规则"]
        icons = ["mdi-tune", "mdi-bell-ring", "mdi-regex"]
        windows = [
            self._tab_basic(downloader_opts),
            self._tab_notify(),
            self._tab_advanced(),
        ]
        tab_items = [{"component": "VTab", "props": {"value": i, "prepend-icon": icons[i]}, "text": t}
                     for i, t in enumerate(titles)]
        win_items = [{"component": "VWindowItem", "props": {"value": i}, "content": w}
                     for i, w in enumerate(windows)]
        return [
            {"component": "VTabs", "props": {"model": "_tab", "grow": True},
             "content": tab_items},
            {"component": "VWindow", "props": {"model": "_tab", "style": "padding-top: 16px"},
             "content": win_items},
        ]

    # ── Tab 0：基本设置 ───────────────────────────────────────

    def _tab_basic(self, downloader_opts: list) -> list:
        return [
            self._field_row(
                self._switch("enabled", "启用插件"),
                self._switch("fast_scan_enabled", "快速拦截", "标题预检→文件匹配，低开销优先命中"),
                self._switch("full_scan_enabled", "全量兜底", "低频补漏，事件驱动已覆盖所有新任务"),
            ),
            self._field_row(
                self._number("interval", "快速间隔（分钟）", min_val=1),
                self._number("full_interval", "全量间隔（分钟）", min_val=5, hint="留空=自动（快速×5）"),
                self._select("action", "命中动作", [
                    {"title": "停止下载", "value": "stop"},
                    {"title": "删除并联动清理", "value": "delete"},
                ], hint="删除会联动清理文件/入库/记录"),
                self._switch("include_completed", "检查已完成", "避免间隔期内任务漏检"),
            ),
            self._field_row(
                {"component": "VCol", "props": {"cols": 12, "md": 6}, "content": [
                    {"component": "VSelect", "props": {
                        "multiple": True, "chips": True, "model": "downloaders",
                        "label": "QB 下载器", "items": downloader_opts,
                        "hint": "留空 = 全部 QB 下载器", "persistent-hint": True,
                    }}
                ]},
                self._text("tag", "命中标签"),
                self._switch("retry_failed", "失败重试"),
            ),
        ]

    # ── Tab 1：通知与测试 ─────────────────────────────────────

    def _tab_notify(self) -> list:
        return [
            # 卡片 1：通知配置
            {"component": "VCard", "props": {
                "variant": "tonal", "elevation": "0", "rounded": "lg", "class": "mb-4 pa-4",
            }, "content": [
                {"component": "div", "props": {"class": "text-subtitle-2 font-weight-medium mb-3"},
                 "text": "通知配置"},
                self._field_row(
                    self._switch("notify", "发送通知"),
                    self._select("notify_type", "通知场景", [
                        {"title": "智能体", "value": "Agent"},
                        {"title": "插件", "value": "Plugin"},
                        {"title": "资源下载", "value": "Download"},
                        {"title": "整理入库", "value": "Organize"},
                        {"title": "其它", "value": "Other"},
                    ], hint="借用 MP 对应通知频道发送"),
                    self._text("alert_image", "报警图地址", hint="留空自动恢复默认图标"),
                ),
            ]},
            # 卡片 2：模拟通知测试字段
            {"component": "VCard", "props": {
                "variant": "tonal", "elevation": "0", "rounded": "lg", "class": "mb-4 pa-4",
            }, "content": [
                {"component": "div", "props": {"class": "text-subtitle-2 font-weight-medium mb-3"},
                 "text": "模拟通知字段"},
                self._field_row(
                    self._text("test_title", "测试标题", md=6),
                    self._text("test_subtitle", "测试种子名/副标题", md=6),
                ),
                self._field_row(
                    self._text("test_site", "测试站点"),
                    self._text("test_seeders", "测试做种数"),
                    self._text("test_tags", "测试标签"),
                ),
                self._field_row(
                    {"component": "VCol", "props": {"cols": 12}, "content": [
                        {"component": "VTextField", "props": {
                            "model": "test_format", "label": "判定格式",
                            "hint": "只写格式依据，不暴露路径/hash", "persistent-hint": True,
                        }}
                    ]},
                ),
                self._field_row(
                    {"component": "VCol", "props": {"cols": 12}, "content": [
                        {"component": "VTextarea", "props": {
                            "model": "test_message", "label": "下载通知字段（多行）",
                            "rows": 4, "hint": "按 MP 下载通知格式逐行填写", "persistent-hint": True,
                        }}
                    ]},
                ),
            ]},
        ]

    # ── Tab 2：高级规则 ───────────────────────────────────────

    def _tab_advanced(self) -> list:
        return [
            {"component": "VAlert", "props": {
                "type": "warning", "variant": "tonal", "density": "compact", "class": "mb-3",
                "text": "一般不需修改。规则过宽可能误杀正常任务，建议先用默认规则在小范围验证后再调整。",
            }},
            {"component": "VRow", "content": [
                {"component": "VCol", "props": {"cols": 12}, "content": [
                    {"component": "VTextarea", "props": {
                        "model": "patterns", "label": "原盘识别正则（每行一条）",
                        "rows": 8, "hint": "以 # 开头的行为注释；留空自动恢复内置默认规则",
                        "persistent-hint": True,
                    }}
                ]},
            ]},
        ]

    # ── 表单字段工厂（3 列栅格，md=4）────────────────────────────

    def _field_row(self, *cols: dict) -> dict:
        """多个 VCol 包入一个 VRow。"""
        return {"component": "VRow", "content": list(cols)}

    def _switch(self, key: str, label: str, hint: str = "") -> dict:
        return self._col(4, "VSwitch", {"model": key, "label": label,
                          "hint": hint, "persistent-hint": bool(hint)})

    def _text(self, key: str, label: str, hint: str = "", md: int = 4) -> dict:
        return self._col(md, "VTextField", {"model": key, "label": label,
                          "hint": hint, "persistent-hint": bool(hint)})

    def _number(self, key: str, label: str, min_val: int = 1, hint: str = "", md: int = 4) -> dict:
        return self._col(md, "VTextField", {"model": key, "label": label, "type": "number",
                          "min": min_val, "hint": hint, "persistent-hint": bool(hint)})

    def _select(self, key: str, label: str, items: list, hint: str = "", md: int = 4) -> dict:
        return self._col(md, "VSelect", {"model": key, "label": label, "items": items,
                          "hint": hint, "persistent-hint": bool(hint)})

    @staticmethod
    def _col(cols: int, component: str, props: dict) -> dict:
        return {"component": "VCol", "props": {"cols": 12, "md": cols},
                "content": [{"component": component, "props": props}]}

    # ── 液态玻璃卡片组件工厂（Tab 2 运行状态 / 顶部标题卡复用）─────

    def _stats_row(self) -> dict:
        """构建顶部统计卡片行（液态玻璃）。"""
        hits = sum(1 for v in (self.processed or {}).values() if v.get("matched"))
        stats = [
            ("mdi-alert-octagon", "累计拦截", f"{hits} 次", "error"),
            ("mdi-shield-search", "幸存缓存", f"{len(self._survivors)} 个", "info"),
            ("mdi-timer-sand", "回扫队列", f"{len(self._rescan_queue)} 个",
             "warning" if self._rescan_queue else "success"),
            ("mdi-database-check", "处理记录", f"{len(self.processed or {})} 条", "primary"),
        ]
        return {"component": "VRow", "content": [
            {"component": "VCol", "props": {"cols": 6, "md": 3},
             "content": [self._metric_card(icon, label, value, color)]}
            for icon, label, value, color in stats
        ]}

    def _health_row(self, checks: List[dict]) -> dict:
        """构建健康检查卡片行。"""
        return {"component": "VRow", "content": [
            {"component": "VCol", "props": {"cols": 6, "md": 3}, "content": [self._status_card(item)]}
            for item in checks
        ]}

    def _action_button(self, text: str, icon: str, color: str, endpoint: str) -> dict:
        """操作按钮（MP 原生 tonal + rounded-lg + 紫色系）。"""
        return {"component": "VBtn", "props": {
            "color": color, "variant": "tonal", "rounded": "lg", "block": True,
            "prepend-icon": icon, "class": "text-none",
        }, "text": text, "events": {
            "click": {"api": f"plugin/QBRawGuard/{endpoint}?apikey={settings.API_TOKEN}", "method": "get"}
        }}

    def _metric_card(self, icon: str, label: str, value: str, color: str = "primary") -> dict:
        """统计指标卡片（MP 原生 tonal + 苹果液态玻璃 backdrop-filter）。"""
        return {"component": "VCard", "props": {
            "variant": "tonal", "elevation": "0", "rounded": "lg",
            "style": "backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);",
        }, "content": [
            {"component": "VCardText", "props": {"class": "d-flex align-center pa-3"}, "content": [
                {"component": "VAvatar", "props": {
                    "color": color, "variant": "tonal", "rounded": "lg", "size": 44, "class": "me-3"
                }, "content": [
                    {"component": "VIcon", "props": {"size": 22}, "content": icon}
                ]},
                {"component": "div", "content": [
                    {"component": "div", "props": {"class": "text-caption text-medium-emphasis"}, "text": label},
                    {"component": "div", "props": {"class": "text-h6 font-weight-bold"}, "text": value},
                ]}
            ]}
        ]}

    def _status_card(self, item: dict) -> dict:
        """健康检查卡片（MP 原生 tonal + 苹果液态玻璃）。"""
        status = item.get("status", "default")
        color_prop = self._STATUS_COLOR_PROP.get(status, "grey")
        text_class = self._STATUS_TEXT_CLASS.get(status, "text-medium-emphasis")
        return {"component": "VCard", "props": {
            "variant": "tonal", "elevation": "0", "rounded": "lg",
            "style": "backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);",
        }, "content": [
            {"component": "VCardText", "props": {"class": "pa-3"}, "content": [
                {"component": "div", "props": {"class": "d-flex align-center mb-1"}, "content": [
                    {"component": "VIcon", "props": {"size": 18, "class": "me-1", "color": color_prop},
                     "content": item.get("icon") or "mdi-information"},
                    {"component": "span", "props": {"class": "text-caption text-medium-emphasis"},
                     "text": item.get("label", "状态")},
                ]},
                {"component": "div", "props": {"class": f"text-body-2 font-weight-medium {text_class}"},
                 "text": item.get("text", "")},
            ]}
        ]}

    def _glass_card_style(self, blur: int = 14, opacity: float = 0.55) -> str:
        """液态玻璃卡片 CSS（半透明 + 毛玻璃模糊 + 微妙边框）。"""
        return (
            f"background: rgba(var(--v-theme-surface), {opacity}); "
            f"backdrop-filter: blur({blur}px); "
            f"-webkit-backdrop-filter: blur({blur}px); "
            f"border: 1px solid rgba(var(--v-theme-on-surface), 0.06);"
        )
