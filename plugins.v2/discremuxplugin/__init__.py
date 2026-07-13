from datetime import datetime, timedelta
import json
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app import schemas
from app.core.config import settings
from app.chain.transfer import TransferChain
from app.core.event import eventmanager, Event
from app.db.downloadhistory_oper import DownloadHistoryOper
from app.db.transferhistory_oper import TransferHistoryOper
from app.helper.mediaserver import MediaServerHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import ChainEventType, EventType, MediaType

from .disc_remuxer import DiscRemuxer
from .track_normalizer import TrackNormalizer


class DiscRemuxPlugin(_PluginBase):
    """蓝光原盘重封装插件。"""

    plugin_name = "蓝光原盘重封装"
    plugin_desc = "只从源文件目录查找 ISO/BDMV 原盘，重封装为 MKV 后通过 MoviePilot 硬链接整理入库，并规范音轨/字幕轨道标题。"
    plugin_icon = "https://raw.githubusercontent.com/the-bruz/MoviePilot-Plugins/main/icons/discremuxplugin.png"
    plugin_version = "2.4.1"
    plugin_author = "bruz"
    author_url = "https://github.com/the-bruz"

    plugin_config_prefix = "discremux_"
    plugin_order = 10
    auth_level = 1

    _DATA_KEY = "processed_histories"
    _history_enabled = False
    _library_scan_enabled = False
    _intercept_enabled = False
    _message = "插件尚未初始化"
    _stop_event = threading.Event()
    _scheduler: Optional[BackgroundScheduler] = None
    _remuxer: Optional[DiscRemuxer] = None
    _remuxer_lock = threading.Lock()
    _remuxers = set()
    _intercept_lock = threading.Lock()
    _active_intercepts = set()

    def init_plugin(self, config: dict = None):
        """根据当前配置初始化插件。"""
        config = config or {}
        changed = False
        if "history_enabled" not in config and "enabled" in config:
            config["history_enabled"] = bool(config.get("enabled"))
            changed = True
        if "normalize_tracks" not in config:
            config["normalize_tracks"] = True
            changed = True
        if "reset_video_language" not in config:
            config["reset_video_language"] = True
            changed = True
        if changed:
            self.update_config(config)
        if "library_scan_enabled" not in config:
            config["library_scan_enabled"] = False
            changed = True
        if "library_root" not in config:
            config["library_root"] = "/PT/mp/硬链接"
            changed = True
        if "source_root" not in config:
            config["source_root"] = "/PT/mp/源文件"
            changed = True
        if "source_roots" not in config:
            config["source_roots"] = config.get("source_root") or "/PT/mp/源文件"
            changed = True
        if "library_scan_run_once" not in config:
            config["library_scan_run_once"] = False
            changed = True
        if "library_scan_cron" not in config:
            config["library_scan_cron"] = "30 3 * * *"
            changed = True
        if "library_scan_max_items" not in config:
            config["library_scan_max_items"] = 50
            changed = True
        if "source_disc_action" not in config:
            config["source_disc_action"] = "delete" if bool(config.get("delete_download_source")) else "keep"
            changed = True
        if "library_disc_action" not in config:
            legacy_bdmv_action = config.get("bdmv_action") or "ignore"
            config["library_disc_action"] = "delete" if legacy_bdmv_action == "delete_bdmv" else ("ignore" if legacy_bdmv_action == "ignore" else "keep")
            changed = True
        if changed:
            self.update_config(config)
        self._history_enabled = bool(config.get("history_enabled", config.get("enabled")))
        self._library_scan_enabled = bool(config.get("library_scan_enabled"))
        self._intercept_enabled = bool(config.get("intercept_enabled"))
        self._message = config.get("message") or "插件初始化完成，等待任务执行。"
        self._stop_event = threading.Event()
        self._active_intercepts = set()
        self._remuxers = set()
        self._remuxer = None

        if self._library_scan_enabled and config.get("library_scan_run_once"):
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            logger.info("蓝光原盘重封装服务启动，立即扫描已入库原盘一次")
            self._scheduler.add_job(
                self.library_scan_remux,
                "date",
                run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                name="扫描已入库原盘重封装",
            )
            self._scheduler.start()
            config["library_scan_run_once"] = False
            self.update_config(config)

        if self._history_enabled and config.get("run_once"):
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            logger.info("蓝光原盘重封装服务启动，立即运行一次")
            self._scheduler.add_job(
                self.history_remux,
                "date",
                run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                name="蓝光原盘重封装",
            )
            self._scheduler.start()
            config["run_once"] = False
            self.update_config(config)

    def get_state(self) -> bool:
        """返回插件当前是否启用。"""
        return self._history_enabled or self._library_scan_enabled or self._intercept_enabled

    def get_service(self) -> List[Dict[str, Any]]:
        """注册后台定时任务。"""
        config = self.get_config() or {}
        services = []
        if self._history_enabled:
            cron_str = config.get("cron_schedule") or "0 3 * * *"
            services.append(
                {
                    "id": f"{self.__class__.__name__}.history_remux",
                    "name": "定时重封装最近整理的蓝光原盘",
                    "trigger": CronTrigger.from_crontab(cron_str),
                    "func": self.history_remux,
                    "kwargs": {},
                }
            )
        if self._library_scan_enabled:
            cron_str = config.get("library_scan_cron") or "30 3 * * *"
            services.append(
                {
                    "id": f"{self.__class__.__name__}.library_scan_remux",
                    "name": "定时扫描已入库蓝光原盘并从源文件重封装",
                    "trigger": CronTrigger.from_crontab(cron_str),
                    "func": self.library_scan_remux,
                    "kwargs": {},
                }
            )
        return services

    def stop_service(self):
        """停止正在执行的重封装任务。"""
        self._stop_event.set()
        logger.info("收到停用信号，正在终止 MakeMKV 重封装任务...")
        if self._scheduler:
            try:
                self._scheduler.shutdown(wait=False)
                self._scheduler = None
            except Exception as e:
                logger.warning(f"关闭一次性调度器失败: {e}")
        with self._remuxer_lock:
            remuxers = list(self._remuxers)
        for remuxer in remuxers:
            try:
                remuxer.terminate()
            except Exception as e:
                logger.error(f"尝试终止 MakeMKV 进程时发生异常: {e}")

    def _register_remuxer(self, remuxer: DiscRemuxer) -> None:
        with self._remuxer_lock:
            self._remuxers.add(remuxer)
            self._remuxer = remuxer

    def _unregister_remuxer(self, remuxer: DiscRemuxer) -> None:
        with self._remuxer_lock:
            self._remuxers.discard(remuxer)
            self._remuxer = next(iter(self._remuxers), None)

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        json_path = Path(__file__).parent / "form_ui.json"
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                form_ui = json.load(f)
        except Exception as e:
            logger.error(f"加载表单配置失败: {json_path} | 错误详情: {e}")
            raise RuntimeError(f"插件 UI 配置加载失败: {e}") from e

        default_config = {
            "history_enabled": False,
            "run_once": False,
            "library_scan_enabled": False,
            "library_scan_run_once": False,
            "library_scan_cron": "30 3 * * *",
            "source_root": "/PT/mp/源文件",
            "source_roots": "/PT/mp/源文件\n/PT/ms/源文件",
            "library_root": "/PT/mp/硬链接",
            "library_scan_max_items": 50,
            "recent_days": 7,
            "min_mkv_size_gb": 5,
            "movies_only": True,
            "source_disc_action": "keep",
            "library_disc_action": "delete",
            "refresh_media_server": True,
            "cron_schedule": "0 3 * * *",
            "intercept_enabled": False,
            "intercept_transfer_mkv": True,
            "normalize_tracks": True,
            "reset_video_language": True,
        }
        return form_ui, default_config

    def get_page(self) -> List[dict]:
        """返回详情页 JSON。"""
        histories = self._get_processed_histories()[:20]
        headers = [
            {"title": "模式", "key": "mode", "sortable": True},
            {"title": "状态", "key": "status", "sortable": True},
            {"title": "标题", "key": "title", "sortable": True},
            {"title": "来源", "key": "source", "sortable": False},
            {"title": "输出", "key": "output", "sortable": False},
            {"title": "下载源", "key": "source_cleanup", "sortable": False},
            {"title": "后处理", "key": "post_action", "sortable": False},
            {"title": "时间", "key": "time", "sortable": True},
        ]
        items = [
            {
                "mode": self._format_history_mode(item),
                "status": self._format_history_status(item),
                "title": item.get("title") or "-",
                "source": self._format_history_source(item),
                "output": (item.get("remux") or {}).get("output") or item.get("output") or "-",
                "source_cleanup": self._format_source_cleanup(item),
                "post_action": self._format_history_post_action(item),
                "time": item.get("finished_at") or item.get("time") or "-",
            }
            for item in histories
        ]
        page = [
            {
                "component": "VRow",
                "props": {"style": {"overflow": "hidden"}},
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VAlert",
                                "props": {"type": "info", "variant": "tonal", "text": self._message},
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VAlert",
                                "props": {
                                    "type": "secondary",
                                    "variant": "tonal",
                                    "text": (
                                        f"插件数据目录：{self.get_data_path()}；如需重跑，可清空已处理历史。"
                                        "目标 MKV 已存在或旧 BDMV 有 .ignore 时仍会按配置跳过。插件不会修改 MP 整理记录状态。"
                                    ),
                                },
                            }
                        ],
                    },
                ],
            }
        ]
        if histories:
            page[0]["content"].append(
                {
                    "component": "VCol",
                    "props": {"cols": 12},
                    "content": [
                        {
                            "component": "VDataTableVirtual",
                            "props": {
                                "class": "text-sm",
                                "headers": headers,
                                "items": items,
                                "height": "30rem",
                                "density": "compact",
                                "fixed-header": True,
                                "hide-no-data": True,
                                "hover": True,
                            },
                        }
                    ],
                },
            )
        else:
            page[0]["content"].append(
                {
                    "component": "VCol",
                    "props": {"cols": 12},
                    "content": [
                        {
                            "component": "div",
                            "text": "暂无已处理历史记录。",
                            "props": {"class": "text-center"},
                        }
                    ],
                }
            )
        page[0]["content"].append(
            {
                "component": "VCol",
                "props": {"cols": 12},
                "content": [
                    {
                        "component": "VBtn",
                        "props": {
                            "color": "warning",
                            "variant": "tonal",
                        },
                        "content": [
                            {
                                "component": "span",
                                "text": "清空已处理历史",
                            }
                        ],
                        "events": {
                            "click": {
                                "api": "plugin/DiscRemuxPlugin/clear_processed",
                                "method": "post",
                            }
                        },
                    }
                ],
            }
        )
        return page

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "/clear_processed",
                "endpoint": self.clear_processed_histories,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "清空已处理历史",
                "description": "清空插件记录的 processed history id，用于允许重新处理整理历史。",
            },
            {
                "path": "/library_scan_preview",
                "endpoint": self.library_scan_preview,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "预览已入库原盘扫描任务",
                "description": "只扫描源文件和硬链接库中的 BDMV 候选，不执行重封装、整理、删除或媒体库刷新。",
            },
        ]

    def clear_processed_histories(self) -> schemas.Response:
        self.save_data(self._DATA_KEY, [])
        self._message = "已清空已处理历史，下次运行会重新评估整理记录。"
        logger.info(self._message)
        return schemas.Response(success=True, message=self._message)

    def _get_processed_histories(self) -> List[dict]:
        data = self.get_data(self._DATA_KEY)
        return data if isinstance(data, list) else []

    @staticmethod
    def _now_str() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _format_history_mode(item: dict) -> str:
        mode = item.get("mode")
        if mode == "intercept":
            return "截断整理"
        if mode == "post_transfer":
            return "整理后"
        if mode == "library_scan":
            return "源文件扫描"
        return mode or "-"

    @staticmethod
    def _format_history_status(item: dict) -> str:
        status = item.get("status")
        return {
            "running": "运行中",
            "success": "成功",
            "failed": "失败",
            "skipped": "跳过",
            "waiting": "等待",
        }.get(status, status or "-")

    @staticmethod
    def _format_history_source(item: dict) -> str:
        source = item.get("source") or {}
        if item.get("mode") == "intercept":
            return source.get("download_hash") or source.get("input") or "-"
        if item.get("mode") == "library_scan":
            return source.get("input") or source.get("library_hint") or "-"
        return str(source.get("transfer_history_id") or item.get("id") or "-")

    @staticmethod
    def _format_history_post_action(item: dict) -> str:
        post_action = item.get("post_action") or {}
        parts = []
        library_action = post_action.get("library_bdmv_action")
        if library_action and library_action != "none":
            parts.append(f"旧入库原盘:{library_action}")
        if post_action.get("triggered_transfer"):
            new_history_id = post_action.get("new_transfer_history_id")
            parts.append(f"整理MKV#{new_history_id}" if new_history_id else "整理MKV")
        return "；".join(parts) or "-"

    @staticmethod
    def _format_source_cleanup(item: dict) -> str:
        source_cleanup = (item.get("post_action") or {}).get("source_cleanup")
        return "已删除" if source_cleanup and source_cleanup != "none" else "保留"

    @staticmethod
    def _history_value(download_history, key: str, default=None):
        if isinstance(download_history, dict):
            return download_history.get(key, default)
        return getattr(download_history, key, default)

    @classmethod
    def _download_history_snapshot(cls, download_history) -> dict:
        keys = [
            "path",
            "type",
            "title",
            "year",
            "tmdbid",
            "doubanid",
            "downloader",
            "download_hash",
            "episode_group",
        ]
        return {key: cls._history_value(download_history, key) for key in keys}

    def _save_history_record(self, record: dict) -> None:
        histories = [
            item for item in self._get_processed_histories()
            if item.get("dedupe_key") != record.get("dedupe_key")
        ]
        histories.insert(0, record)
        self.save_data(self._DATA_KEY, histories[:200])

    def _update_history_record(self, dedupe_key: str, **updates) -> None:
        histories = self._get_processed_histories()
        for item in histories:
            if item.get("dedupe_key") != dedupe_key:
                continue
            for key, value in updates.items():
                if isinstance(value, dict) and isinstance(item.get(key), dict):
                    item[key].update(value)
                else:
                    item[key] = value
            self.save_data(self._DATA_KEY, histories[:200])
            return

    def _save_processed_history(
            self,
            history,
            output_file: Path,
            source_cleanup: str = "none",
            library_bdmv_action: str = "none",
    ) -> None:
        record = {
            "id": str(uuid.uuid4()),
            "dedupe_key": f"post_transfer:{history.id}",
            "mode": "post_transfer",
            "status": "success",
            "title": history.title or Path(str(history.dest or "")).name,
            "media_type": history.type,
            "tmdbid": history.tmdbid,
            "doubanid": history.doubanid,
            "source": {
                "transfer_history_id": history.id,
                "download_hash": history.download_hash,
                "downloader": history.downloader,
                "input": history.dest,
                "input_location": "library",
                "disc_type": "bdmv",
            },
            "remux": {
                "output": output_file.as_posix(),
            },
            "post_action": {
                "source_cleanup": source_cleanup,
                "transfer_history_cleanup": "none",
                "library_bdmv_action": library_bdmv_action,
                "triggered_transfer": False,
                "new_transfer_history_id": None,
            },
            "finished_at": self._now_str(),
            # 兼容旧详情页字段。
            "output": output_file.as_posix(),
            "time": self._now_str(),
        }
        self._save_history_record(record)

    def _is_processed(self, history_id: int) -> bool:
        return any(
            item.get("dedupe_key") == f"post_transfer:{history_id}"
            or str(item.get("id")) == str(history_id)
            for item in self._get_processed_histories()
        )

    @staticmethod
    def _is_valid_bdmv_dir(path: Optional[Path]) -> bool:
        if not path or not path.exists() or not path.is_dir():
            return False
        try:
            marker_files = {item.name.lower() for item in path.iterdir() if item.is_file()}
        except OSError:
            return False
        return "index.bdmv" in marker_files or "movieobject.bdmv" in marker_files

    @staticmethod
    def _is_disc_image_file(path: Optional[Path]) -> bool:
        """判断路径是否为支持的光盘镜像文件。"""
        return bool(path and path.exists() and path.is_file() and path.suffix.lower() in {".iso", ".img"})

    @classmethod
    def _is_valid_disc_source(cls, path: Optional[Path]) -> bool:
        """判断源文件目录或镜像是否为可处理的原盘输入。"""
        if not path:
            return False
        if cls._is_disc_image_file(path):
            return True
        return path.exists() and path.is_dir() and cls._is_valid_bdmv_dir(path / "BDMV")

    @classmethod
    def _disc_type(cls, path: Optional[Path]) -> str:
        """返回原盘来源类型。"""
        if cls._is_disc_image_file(path):
            return path.suffix.lower().lstrip(".")
        if path and cls._is_valid_bdmv_dir(path / "BDMV"):
            return "bdmv"
        return "unknown"

    @staticmethod
    def _parse_path_list(value: Any, fallback: str = "") -> List[Path]:
        """解析多行或逗号分隔的路径配置。"""
        raw = value if value not in (None, "") else fallback
        if isinstance(raw, (list, tuple)):
            parts = [str(item) for item in raw]
        else:
            parts = str(raw or "").replace(",", "\n").splitlines()
        paths: List[Path] = []
        for part in parts:
            text = part.strip()
            if not text:
                continue
            try:
                path = Path(text).resolve()
            except Exception:
                path = Path(text)
            if path not in paths:
                paths.append(path)
        return paths

    @staticmethod
    def _is_relative_to(path: Path, root: Path) -> bool:
        """兼容 Python 版本判断 path 是否位于 root 下。"""
        try:
            path.resolve().relative_to(root.resolve())
            return True
        except Exception:
            return False

    @classmethod
    def _under_any_source_root(cls, path: Path, source_roots: List[Path]) -> bool:
        """判断候选是否位于任一源文件根目录下。"""
        return any(cls._is_relative_to(path, root) for root in source_roots)

    @staticmethod
    def _output_for_disc_source(source_path: Path) -> Path:
        """根据源文件原盘路径生成同目录 MKV 输出路径。"""
        if source_path.is_file():
            return source_path.with_suffix(".mkv")
        return source_path / f"{source_path.name}.mkv"

    @staticmethod
    def _resolve_movie_dir(dest: str) -> Path:
        dest_path = Path(dest)
        if dest_path.name.upper() == "BDMV":
            return dest_path.parent
        if dest_path.exists() and dest_path.is_file():
            return dest_path.parent
        if dest_path.suffix:
            return dest_path.parent
        return dest_path

    @classmethod
    def _resolve_old_bdmv_dir(cls, dest: str, movie_dir: Path) -> Optional[Path]:
        dest_path = Path(dest)
        parts = list(dest_path.parts)
        for index, part in enumerate(parts):
            if part.upper() == "BDMV":
                bdmv_dir = Path(*parts[: index + 1])
                return bdmv_dir if cls._is_valid_bdmv_dir(bdmv_dir) else None
        candidate = movie_dir / "BDMV"
        return candidate if cls._is_valid_bdmv_dir(candidate) else None

    @classmethod
    def _is_bdmv_history(cls, history) -> bool:
        if not history or not history.dest:
            return False
        movie_dir = cls._resolve_movie_dir(history.dest)
        old_bdmv_dir = cls._resolve_old_bdmv_dir(history.dest, movie_dir)
        return cls._is_valid_bdmv_dir(old_bdmv_dir)

    @staticmethod
    def _target_mkv_exists(output_file: Path, min_size_gb: float) -> bool:
        min_size = int(min_size_gb * 1024 * 1024 * 1024)
        return output_file.exists() and output_file.is_file() and output_file.stat().st_size > min_size

    @staticmethod
    def _has_ignore_file(old_bdmv_dir: Optional[Path]) -> bool:
        return bool(old_bdmv_dir and (old_bdmv_dir / ".ignore").exists())

    @staticmethod
    def _touch_ignore_file(old_bdmv_dir: Optional[Path]) -> None:
        if not old_bdmv_dir or not old_bdmv_dir.exists() or not old_bdmv_dir.is_dir():
            logger.warning(f"旧 BDMV 目录不存在，无法创建 .ignore: {old_bdmv_dir}")
            return
        (old_bdmv_dir / ".ignore").touch(exist_ok=True)

    @staticmethod
    def _delete_old_bdmv(movie_dir: Path, old_bdmv_dir: Optional[Path]) -> None:
        for target in [old_bdmv_dir, movie_dir / "CERTIFICATE"]:
            if target and target.exists() and target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
                logger.info(f"已删除旧媒体库原盘目录: {target}")

    @classmethod
    def _apply_library_disc_action(cls, library_movie_dir: Optional[Path], action: str) -> str:
        """在新 MKV 成功入库后处理硬链接库旧原盘残留。"""
        if not library_movie_dir:
            return "none"
        old_bdmv_dir = library_movie_dir / "BDMV"
        action = action or "keep"
        if cls._is_valid_bdmv_dir(old_bdmv_dir):
            if action == "delete":
                cls._delete_old_bdmv(library_movie_dir, old_bdmv_dir)
                return "delete_bdmv"
            if action == "ignore":
                cls._touch_ignore_file(old_bdmv_dir)
                return "ignore"
            return "keep"
        for image in list(library_movie_dir.glob("*.iso")) + list(library_movie_dir.glob("*.img")):
            if cls._is_disc_image_file(image):
                if action == "delete":
                    image.unlink(missing_ok=True)
                    logger.info(f"已删除旧媒体库原盘镜像: {image}")
                    return "delete_image"
                if action == "ignore":
                    ignore_file = image.with_name(image.name + ".ignore")
                    ignore_file.touch(exist_ok=True)
                    logger.info(f"已为旧媒体库原盘镜像创建 ignore 标记: {ignore_file}")
                    return "ignore_image"
                return "keep"
        return "none"

    @staticmethod
    def _source_disc_action(config: dict) -> str:
        """读取源文件原盘处理策略，并兼容旧删除源文件开关。"""
        action = config.get("source_disc_action")
        if action in {"keep", "delete"}:
            return action
        return "delete" if bool(config.get("delete_download_source")) else "keep"

    @staticmethod
    def _library_disc_action(config: dict) -> str:
        """读取旧入库原盘处理策略，并兼容旧 BDMV 动作。"""
        action = config.get("library_disc_action")
        if action in {"keep", "ignore", "delete"}:
            return action
        legacy = config.get("bdmv_action") or "ignore"
        if legacy == "delete_bdmv":
            return "delete"
        if legacy == "ignore":
            return "ignore"
        return "keep"

    @staticmethod
    def _media_type(history) -> Optional[MediaType]:
        if history.type == MediaType.MOVIE.value:
            return MediaType.MOVIE
        if history.type == MediaType.TV.value:
            return MediaType.TV
        return None

    def _cleanup_download_source(self, history, delete_source: bool) -> None:
        if delete_source and history.src_fileitem:
            src_fileitem = schemas.FileItem(**history.src_fileitem)
            self._delete_local_source_fileitem(src_fileitem)
            DownloadHistoryOper().delete_file_by_fullpath(Path(src_fileitem.path).as_posix())
            logger.info(f"已删除下载源: history_id={history.id}, src={history.src}")

    @staticmethod
    def _delete_local_source_fileitem(fileitem: schemas.FileItem) -> None:
        if fileitem.storage and fileitem.storage != "local":
            raise RuntimeError(f"仅支持静默删除本地下载源，不支持存储类型: {fileitem.storage}")

        source_path = Path(fileitem.path)
        if len(source_path.parts) <= 2:
            raise RuntimeError(f"拒绝删除根目录或一级目录: {source_path}")
        if not source_path.exists() and not source_path.is_symlink():
            logger.info(f"下载源已不存在，跳过删除: {source_path}")
            return

        if source_path.is_dir() and not source_path.is_symlink():
            shutil.rmtree(source_path)
            return
        source_path.unlink()

    def _refresh_media_server(self, history, output_file: Path) -> None:
        refresh_target = output_file.parent
        item = schemas.RefreshMediaItem(
            title=history.title,
            year=history.year,
            type=self._media_type(history),
            category=history.category,
            target_path=refresh_target,
        )
        services = MediaServerHelper().get_services()
        if not services:
            logger.info("未获取到媒体服务器实例，跳过媒体库刷新。")
            return

        for name, service in services.items():
            instance = service.instance
            if not instance:
                logger.warning(f"媒体服务器实例为空，跳过刷新: name={name}")
                continue
            if hasattr(instance, "is_inactive") and instance.is_inactive():
                logger.warning(f"媒体服务器未连接，跳过刷新: name={name}")
                continue

            try:
                if hasattr(instance, "refresh_library_by_items"):
                    result = instance.refresh_library_by_items([item])
                    logger.info(
                        f"已尝试刷新媒体服务器条目: name={name}, target_path={refresh_target}, "
                        f"output={output_file}, result={result}"
                    )
                elif hasattr(instance, "refresh_root_library"):
                    result = instance.refresh_root_library()
                    logger.info(
                        f"媒体服务器不支持按条目刷新，已尝试刷新根库: name={name}, "
                        f"target_path={refresh_target}, result={result}"
                    )
                else:
                    logger.warning(f"媒体服务器不支持刷新: name={name}")
            except Exception as e:
                logger.warning(
                    f"刷新媒体服务器失败: name={name}, target_path={refresh_target}, "
                    f"output={output_file}, error={e}"
                )



    @staticmethod
    def _path_is_relative_to(path: Path, root: Path) -> bool:
        """判断路径是否位于指定根目录下。"""
        try:
            path.resolve().relative_to(root.resolve())
            return True
        except Exception:
            return False

    @staticmethod
    def _safe_relative_path(path: Path, root: Path) -> Optional[Path]:
        """返回路径相对根目录的安全相对路径。"""
        try:
            return path.resolve().relative_to(root.resolve())
        except Exception:
            return None

    @classmethod
    def _iter_bdmv_movie_dirs(cls, root: Path, max_items: int) -> List[Path]:
        """扫描根目录下包含有效 BDMV 的影片目录。"""
        movie_dirs: List[Path] = []
        if not root.exists() or not root.is_dir():
            logger.warning(f"原盘扫描根目录不存在或不可读: {root}")
            return movie_dirs
        for bdmv_dir in root.rglob("BDMV"):
            if len(movie_dirs) >= max_items:
                break
            if not bdmv_dir.is_dir() or not cls._is_valid_bdmv_dir(bdmv_dir):
                continue
            if (bdmv_dir / ".ignore").exists():
                logger.info(f"跳过带 .ignore 的 BDMV: {bdmv_dir}")
                continue
            movie_dirs.append(bdmv_dir.parent)
        return movie_dirs

    @staticmethod
    def _first_existing_path(paths: List[Path]) -> Optional[Path]:
        """返回候选路径中的第一个现存路径。"""
        for path in paths:
            if path and path.exists():
                return path
        return None

    def _find_related_transfer_history(self, library_movie_dir: Optional[Path], source_movie_dir: Path):
        """尽量根据硬链接库目录或源文件目录查找关联整理历史。"""
        oper = TransferHistoryOper()
        candidates = []
        if library_movie_dir:
            candidates.extend([
                library_movie_dir.as_posix(),
                (library_movie_dir / "BDMV").as_posix(),
                (library_movie_dir / "BDMV" / "index.bdmv").as_posix(),
                (library_movie_dir / "BDMV" / "MovieObject.bdmv").as_posix(),
            ])
        candidates.extend([
            source_movie_dir.as_posix(),
            (source_movie_dir / "BDMV").as_posix(),
            (source_movie_dir / "BDMV" / "index.bdmv").as_posix(),
            (source_movie_dir / "BDMV" / "MovieObject.bdmv").as_posix(),
        ])
        for dest in candidates:
            try:
                history = oper.get_by_dest(dest)
                if history:
                    return history
            except Exception:
                continue
        try:
            histories = oper.get_by(dest=library_movie_dir.as_posix()) if library_movie_dir else []
            if histories:
                return histories[0]
        except Exception:
            pass
        return None

    def _transfer_source_mkv(self, output_file: Path, history=None) -> Tuple[bool, Any]:
        """调用 MoviePilot 正常整理链路转移源文件目录中的 MKV。"""
        if not output_file.exists() or not output_file.is_file():
            return False, f"重封装 MKV 不存在: {output_file}"
        fileitem = schemas.FileItem(
            storage="local",
            path=output_file.as_posix(),
            type="file",
            name=output_file.name,
            basename=output_file.stem,
            extension=output_file.suffix.lstrip("."),
            size=output_file.stat().st_size,
        )
        return TransferChain().manual_transfer(
            fileitem=fileitem,
            tmdbid=getattr(history, "tmdbid", None) if history else None,
            doubanid=getattr(history, "doubanid", None) if history else None,
            mtype=self._media_type(history) if history else None,
            episode_group=getattr(history, "episode_group", None) if history else None,
            background=False,
            downloader=getattr(history, "downloader", None) if history else None,
            download_hash=getattr(history, "download_hash", None) if history else None,
            transfer_type="link",
            sync_extra_files=False,
        )

    def _save_library_scan_record(
            self,
            source_movie_dir: Path,
            library_movie_dir: Optional[Path],
            output_file: Path,
            history=None,
            status: str = "success",
            error: Optional[str] = None,
            library_bdmv_action: str = "none",
            new_transfer_history_id: Optional[int] = None,
    ) -> None:
        """保存已入库原盘扫描处理记录。"""
        now = self._now_str()
        record = {
            "id": str(uuid.uuid4()),
            "dedupe_key": f"library_scan:{source_movie_dir.as_posix()}",
            "mode": "library_scan",
            "status": status,
            "title": getattr(history, "title", None) or source_movie_dir.name,
            "media_type": getattr(history, "type", None) if history else None,
            "tmdbid": getattr(history, "tmdbid", None) if history else None,
            "doubanid": getattr(history, "doubanid", None) if history else None,
            "source": {
                "transfer_history_id": getattr(history, "id", None) if history else None,
                "download_hash": getattr(history, "download_hash", None) if history else None,
                "downloader": getattr(history, "downloader", None) if history else None,
                "input": source_movie_dir.as_posix(),
                "library_input": library_movie_dir.as_posix() if library_movie_dir else None,
                "input_location": "source_file",
                "disc_type": self._disc_type(source_movie_dir),
            },
            "remux": {
                "output": output_file.as_posix(),
                "started_at": now,
                "finished_at": now,
                "duration_seconds": None,
                "error": error,
            },
            "post_action": {
                "source_cleanup": "none",
                "transfer_history_cleanup": "none",
                "library_bdmv_action": library_bdmv_action,
                "triggered_transfer": bool(new_transfer_history_id),
                "new_transfer_history_id": new_transfer_history_id,
            },
            "started_at": now,
            "finished_at": now,
        }
        self._save_history_record(record)

    def _build_library_scan_tasks(
            self,
            source_root: Path,
            library_root: Path,
            max_items: int,
    ) -> Tuple[List[Path], List[Path], Dict[str, Tuple[Path, Optional[Path]]], List[str]]:
        """构建源文件原盘扫描任务，硬链接库仅作为线索，不作为处理源。"""
        config = self.get_config() or {}
        source_roots = self._parse_path_list(config.get("source_roots"), source_root.as_posix())
        if not source_roots:
            source_roots = [source_root]
        library_roots = self._parse_path_list(config.get("library_roots"), library_root.as_posix()) or [library_root]

        source_dirs: List[Path] = []
        library_dirs: List[Path] = []
        skipped: List[str] = []
        for root in source_roots:
            if not root.exists():
                skipped.append(f"源文件根目录不存在: {root}")
                continue
            for bdmv in root.rglob("BDMV"):
                movie_dir = bdmv.parent
                if self._is_valid_bdmv_dir(bdmv) and movie_dir not in source_dirs:
                    source_dirs.append(movie_dir)
                    if len(source_dirs) >= max_items:
                        break
            if len(source_dirs) < max_items:
                for image in list(root.rglob("*.iso")) + list(root.rglob("*.img")):
                    if self._is_disc_image_file(image) and image not in source_dirs:
                        source_dirs.append(image)
                        if len(source_dirs) >= max_items:
                            break
            if len(source_dirs) >= max_items:
                break

        for root in library_roots:
            if not root.exists():
                skipped.append(f"硬链接库根目录不存在，仅跳过线索扫描: {root}")
                continue
            for bdmv in root.rglob("BDMV"):
                movie_dir = bdmv.parent
                if self._is_valid_bdmv_dir(bdmv) and movie_dir not in library_dirs:
                    library_dirs.append(movie_dir)
                    if len(library_dirs) >= max_items:
                        break
            if len(library_dirs) >= max_items:
                break

        tasks: Dict[str, Tuple[Path, Optional[Path]]] = {}
        for source_path in source_dirs:
            if not self._under_any_source_root(source_path, source_roots):
                skipped.append(f"候选不在源文件根目录下，拒绝处理: {source_path}")
                continue
            tasks[source_path.resolve().as_posix()] = (source_path, None)

        for library_movie_dir in library_dirs:
            mapped = False
            for source in source_roots:
                rel_candidates = []
                for library in library_roots:
                    try:
                        rel_candidates.append(library_movie_dir.resolve().relative_to(library.resolve()))
                    except Exception:
                        continue
                for rel in rel_candidates:
                    source_movie_dir = source / rel
                    if self._is_valid_disc_source(source_movie_dir):
                        tasks.setdefault(source_movie_dir.resolve().as_posix(), (source_movie_dir, library_movie_dir))
                        mapped = True
                        break
                    iso_file = source_movie_dir.with_suffix(".iso")
                    img_file = source_movie_dir.with_suffix(".img")
                    for image in (iso_file, img_file):
                        if self._is_disc_image_file(image):
                            tasks.setdefault(image.resolve().as_posix(), (image, library_movie_dir))
                            mapped = True
                            break
                    if mapped:
                        break
                if mapped:
                    break
            if not mapped:
                skipped.append(f"硬链接库发现原盘但未映射到源文件，按用户约束跳过: {library_movie_dir}")

        limited = dict(list(tasks.items())[:max_items])
        return source_dirs, library_dirs, limited, skipped

    def _library_scan_task_preview(
            self,
            source_movie_dir: Path,
            library_movie_dir: Optional[Path],
            min_size_gb: float,
            movies_only: bool,
    ) -> dict:
        """生成单个已入库原盘任务的只读预览。"""
        history = self._find_related_transfer_history(library_movie_dir, source_movie_dir)
        output_file = self._output_for_disc_source(source_movie_dir)
        dedupe_key = f"library_scan:{source_movie_dir.as_posix()}"
        processed = any(item.get("dedupe_key") == dedupe_key for item in self._get_processed_histories())
        blocked_reasons = []
        if processed:
            blocked_reasons.append("插件已处理记录存在")
        if movies_only and history and history.type != MediaType.MOVIE.value:
            blocked_reasons.append(f"关联整理历史不是电影: {history.type}")
        if self._target_mkv_exists(output_file, min_size_gb):
            blocked_reasons.append(f"源文件 MKV 已存在且大于 {min_size_gb}GB")
        if not self._is_valid_bdmv_dir(source_movie_dir / "BDMV"):
            blocked_reasons.append("源文件 BDMV 不存在或无效")
        return {
            "source_dir": source_movie_dir.as_posix(),
            "library_dir": library_movie_dir.as_posix() if library_movie_dir else None,
            "output_file": output_file.as_posix(),
            "will_process": not blocked_reasons,
            "blocked_reasons": blocked_reasons,
            "history": {
                "id": getattr(history, "id", None) if history else None,
                "title": getattr(history, "title", None) if history else None,
                "type": getattr(history, "type", None) if history else None,
                "tmdbid": getattr(history, "tmdbid", None) if history else None,
                "download_hash": getattr(history, "download_hash", None) if history else None,
            },
        }

    def library_scan_preview(self) -> schemas.Response:
        """只读预览已入库原盘扫描任务。"""
        config = self.get_config() or {}
        source_root = Path(str(config.get("source_root") or "/PT/mp/源文件")).resolve()
        library_root = Path(str(config.get("library_root") or "/PT/mp/硬链接")).resolve()
        max_items = int(config.get("library_scan_max_items") or 50)
        min_size_gb = float(config.get("min_mkv_size_gb") or 5)
        movies_only = bool(config.get("movies_only", True))
        source_dirs, library_dirs, tasks, skipped = self._build_library_scan_tasks(
            source_root=source_root,
            library_root=library_root,
            max_items=max_items,
        )
        previews = [
            self._library_scan_task_preview(
                source_movie_dir=source_movie_dir,
                library_movie_dir=library_movie_dir,
                min_size_gb=min_size_gb,
                movies_only=movies_only,
            )
            for source_movie_dir, library_movie_dir in tasks.values()
        ]
        data = {
            "source_root": source_root.as_posix(),
            "library_root": library_root.as_posix(),
            "source_candidates": len(source_dirs),
            "library_candidates": len(library_dirs),
            "task_count": len(tasks),
            "processable_count": sum(1 for item in previews if item.get("will_process")),
            "skipped": skipped,
            "tasks": previews,
        }
        return schemas.Response(success=True, message="已完成只读扫描预览，未执行重封装或删除。", data=data)

    def library_scan_remux(self) -> bool:
        """扫描源文件和硬链接库中的 BDMV，并从源文件目录重封装后走 MP 正常整理。"""
        self._stop_event.clear()
        config = self.get_config() or {}
        source_root = Path(str(config.get("source_root") or "/PT/mp/源文件")).resolve()
        library_root = Path(str(config.get("library_root") or "/PT/mp/硬链接")).resolve()
        max_items = int(config.get("library_scan_max_items") or 50)
        min_size_gb = float(config.get("min_mkv_size_gb") or 5)
        movies_only = bool(config.get("movies_only", True))
        library_disc_action = self._library_disc_action(config)
        source_disc_action = self._source_disc_action(config)
        normalize_tracks = bool(config.get("normalize_tracks", True))
        reset_video_language = bool(config.get("reset_video_language", True))
        refresh_media_server = bool(config.get("refresh_media_server", True))

        source_dirs, library_dirs, tasks, _ = self._build_library_scan_tasks(
            source_root=source_root,
            library_root=library_root,
            max_items=max_items,
        )

        logger.info(
            "已入库原盘扫描完成: "
            f"source_candidates={len(source_dirs)}, library_candidates={len(library_dirs)}, tasks={len(tasks)}"
        )
        remuxer = DiscRemuxer()
        self._register_remuxer(remuxer)
        try:
            remuxer.validate_environment()
        except Exception:
            self._unregister_remuxer(remuxer)
            raise

        processed_count = 0
        for source_movie_dir, library_movie_dir in tasks.values():
            if self._stop_event.is_set():
                logger.info("任务已被中止。")
                break
            dedupe_key = f"library_scan:{source_movie_dir.as_posix()}"
            if any(item.get("dedupe_key") == dedupe_key for item in self._get_processed_histories()):
                logger.info(f"跳过已处理源文件原盘: source={source_movie_dir}")
                continue
            history = self._find_related_transfer_history(library_movie_dir, source_movie_dir)
            if movies_only and history and history.type != MediaType.MOVIE.value:
                logger.info(f"跳过非电影已入库原盘: source={source_movie_dir}, type={history.type}")
                continue
            output_file = self._output_for_disc_source(source_movie_dir)
            if self._target_mkv_exists(output_file, min_size_gb):
                logger.info(f"源文件 MKV 已存在且大于阈值，跳过重封装: output={output_file}")
                continue
            if not self._is_valid_disc_source(source_movie_dir):
                logger.warning(f"源文件原盘不存在或不支持，跳过: source={source_movie_dir}")
                continue
            try:
                logger.info(
                    "开始从源文件目录重封装已入库原盘: "
                    f"source={source_movie_dir}, library={library_movie_dir}, output={output_file}"
                )
                remuxer.remux_to_mkv(
                    source_root_path=source_movie_dir.as_posix(),
                    output_file_path=output_file.as_posix(),
                )
                if normalize_tracks:
                    self._normalize_mkv_tracks(output_file, reset_video_language=reset_video_language)
                state, errmsg = self._transfer_source_mkv(output_file, history=history)
                if not state:
                    raise RuntimeError(f"源文件 MKV 整理失败: {errmsg}")
                new_history = TransferHistoryOper().get_by_src(output_file.as_posix(), storage="local")
                library_action = self._apply_library_disc_action(library_movie_dir, library_disc_action)
                source_cleanup = self._cleanup_source_disc_after_success(
                    source_root=source_movie_dir,
                    source_disc_action=source_disc_action,
                    download_history=history,
                )
                self._save_library_scan_record(
                    source_movie_dir=source_movie_dir,
                    library_movie_dir=library_movie_dir,
                    output_file=output_file,
                    history=history,
                    status="success",
                    library_bdmv_action=library_action,
                    new_transfer_history_id=new_history.id if new_history else None,
                )
                if source_cleanup != "none":
                    self._update_history_record(
                        f"library_scan:{source_movie_dir.as_posix()}",
                        post_action={"source_cleanup": source_cleanup},
                    )
                if refresh_media_server and new_history:
                    self._refresh_media_server(new_history, output_file)
                processed_count += 1
            except subprocess.CalledProcessError as e:
                error = e.stderr or str(e)
                self._save_library_scan_record(
                    source_movie_dir=source_movie_dir,
                    library_movie_dir=library_movie_dir,
                    output_file=output_file,
                    history=history,
                    status="failed",
                    error=error,
                )
                logger.error(f"已入库原盘重封装失败: source={source_movie_dir}, error={error}")
            except Exception as e:
                self._save_library_scan_record(
                    source_movie_dir=source_movie_dir,
                    library_movie_dir=library_movie_dir,
                    output_file=output_file,
                    history=history,
                    status="failed",
                    error=str(e),
                )
                logger.error(f"已入库原盘处理失败: source={source_movie_dir}, error={e}", exc_info=True)

        self._unregister_remuxer(remuxer)
        self._message = f"已入库原盘扫描完成：任务 {len(tasks)} 个，成功处理 {processed_count} 个。"
        logger.info(self._message)
        return True


    def history_remux(self) -> bool:
        """兼容旧配置入口：不再从硬链接库直接重封装，只提示使用源文件扫描模式。"""
        self._message = (
            "整理历史模式已停用：按当前安全约束，插件只从源文件目录查找 ISO/BDMV，"
            "请使用源文件扫描模式或下载目录拦截模式。"
        )
        logger.warning(self._message)
        return True


    @eventmanager.register(ChainEventType.TransferIntercept)
    def intercept_transfer(self, event: Event):
        """拦截下载目录中的蓝光原盘整理，改由插件先重封装再整理 MKV。"""
        config = self.get_config() or {}
        if not bool(config.get("intercept_enabled")):
            return

        event_data = event.event_data
        if not event_data or getattr(event_data, "cancel", False):
            return

        fileitem = getattr(event_data, "fileitem", None)
        mediainfo = getattr(event_data, "mediainfo", None)
        if not fileitem:
            return

        source_root = Path(fileitem.path)
        source_roots = self._parse_path_list(config.get("source_roots"), config.get("source_root") or "/PT/mp/源文件")
        if source_roots and not self._under_any_source_root(source_root, source_roots):
            logger.info(f"拦截候选不在源文件根目录下，跳过: {source_root}")
            return
        if not self._is_valid_disc_source(source_root):
            return

        download_history = DownloadHistoryOper().get_by_path(source_root.as_posix())
        if not download_history:
            logger.info(f"跳过非 MoviePilot 下载历史原盘: {source_root}")
            return
        if bool(config.get("movies_only", True)) and download_history.type != MediaType.MOVIE.value:
            logger.info(f"跳过非电影下载原盘: {source_root}, type={download_history.type}")
            return

        download_history_snapshot = self._download_history_snapshot(download_history)
        downloader = self._history_value(download_history_snapshot, "downloader") or ""
        download_hash = self._history_value(download_history_snapshot, "download_hash") or source_root.as_posix()
        dedupe_key = f"intercept:{downloader}:{download_hash}"
        with self._intercept_lock:
            if dedupe_key in self._active_intercepts:
                event_data.cancel = True
                event_data.source = self.plugin_name
                event_data.reason = "蓝光原盘重封装任务已在运行，跳过原整理"
                logger.info(
                    "下载器原盘整理已存在接管任务，取消重复整理: "
                    f"source={source_root}, downloader={downloader}, hash={download_hash}"
                )
                return
            self._active_intercepts.add(dedupe_key)

        output_file = self._output_for_disc_source(source_root)
        min_size_gb = float(config.get("min_mkv_size_gb") or 5)
        output_exists = self._target_mkv_exists(output_file, min_size_gb)
        logger.info(
            "接管下载器原盘整理: "
            f"source={source_root}, output={output_file}, downloader={downloader}, "
            f"hash={download_hash}, media={download_history.title} ({download_history.year or '-'}), "
            f"tmdbid={download_history.tmdbid}, output_exists={output_exists}"
        )
        record = self._build_intercept_record(
            dedupe_key=dedupe_key,
            source_root=source_root,
            output_file=output_file,
            download_history=download_history_snapshot,
            mediainfo=mediainfo,
            status="skipped" if output_exists else "running",
            remux_error="目标 MKV 已存在，跳过 MakeMKV 重封装" if output_exists else None,
        )
        self._save_history_record(record)

        event_data.cancel = True
        event_data.source = self.plugin_name
        event_data.reason = (
            "蓝光原盘整理已由插件接管：下载目录 MKV 已存在，跳过原盘整理"
            if output_exists
            else "蓝光原盘整理已由插件接管：先在下载目录重封装 MKV，再对 MKV 发起整理"
        )

        worker = threading.Thread(
            target=self._run_intercept_remux if not output_exists else self._run_existing_intercept_output,
            kwargs={
                "dedupe_key": dedupe_key,
                "source_root": source_root,
                "output_file": output_file,
                "download_history": download_history_snapshot,
                "config": config,
            },
            daemon=True,
        )
        worker.start()
        logger.info(f"已启动下载目录原盘重封装后台任务: source={source_root}, output={output_file}")

    def _build_intercept_record(
            self,
            dedupe_key: str,
            source_root: Path,
            output_file: Path,
            download_history,
            mediainfo,
            status: str = "running",
            remux_error: Optional[str] = None,
    ) -> dict:
        now = self._now_str()
        return {
            "id": str(uuid.uuid4()),
            "dedupe_key": dedupe_key,
            "mode": "intercept",
            "status": status,
            "title": getattr(mediainfo, "title_year", None) or self._history_value(download_history, "title") or source_root.name,
            "media_type": self._history_value(download_history, "type"),
            "tmdbid": self._history_value(download_history, "tmdbid"),
            "doubanid": self._history_value(download_history, "doubanid"),
            "source": {
                "transfer_history_id": None,
                "download_hash": self._history_value(download_history, "download_hash"),
                "downloader": self._history_value(download_history, "downloader"),
                "input": source_root.as_posix(),
                "input_location": "source",
                "disc_type": self._disc_type(source_root),
            },
            "remux": {
                "output": output_file.as_posix(),
                "started_at": now,
                "finished_at": now if status == "skipped" else None,
                "duration_seconds": None,
                "error": remux_error,
            },
            "post_action": {
                "source_cleanup": "none",
                "transfer_history_cleanup": "none",
                "library_bdmv_action": "none",
                "triggered_transfer": False,
                "new_transfer_history_id": None,
            },
            "started_at": now,
            "finished_at": None,
        }

    def _run_existing_intercept_output(self, dedupe_key: str, source_root: Path, output_file: Path, download_history, config: dict) -> None:
        try:
            logger.info(f"下载目录 MKV 已存在，跳过 MakeMKV 并进入后处理: output={output_file}")
            if bool(config.get("normalize_tracks", True)):
                self._normalize_mkv_tracks(
                    output_file,
                    reset_video_language=bool(config.get("reset_video_language", True)),
                )
            triggered_transfer, new_transfer_history_id = self._post_process_intercept_output(
                output_file=output_file,
                download_history=download_history,
                config=config,
            )
            self._update_history_record(
                dedupe_key,
                status="success",
                post_action={
                    "source_cleanup": self._cleanup_intercept_source(source_root, config, download_history=download_history),
                    "triggered_transfer": triggered_transfer,
                    "new_transfer_history_id": new_transfer_history_id,
                },
                finished_at=self._now_str(),
            )
            logger.info(
                "已存在 MKV 后处理完成: "
                f"output={output_file}, triggered_transfer={triggered_transfer}, "
                f"new_transfer_history_id={new_transfer_history_id}"
            )
        except Exception as e:
            self._update_history_record(
                dedupe_key,
                status="failed",
                remux={"error": str(e), "finished_at": self._now_str()},
                finished_at=self._now_str(),
            )
            logger.error(f"处理已存在拦截 MKV 失败: source={source_root}, output={output_file}, error={e}", exc_info=True)
        finally:
            with self._intercept_lock:
                self._active_intercepts.discard(dedupe_key)

    def _run_intercept_remux(self, dedupe_key: str, source_root: Path, output_file: Path, download_history, config: dict) -> None:
        started_at = time.time()
        try:
            logger.info(f"开始下载目录原盘重封装: source={source_root}, output={output_file}")
            remuxer = DiscRemuxer()
            self._register_remuxer(remuxer)
            remuxer.validate_environment()
            remuxer.remux_to_mkv(
                source_root_path=source_root.as_posix(),
                output_file_path=output_file.as_posix(),
            )
            if bool(config.get("normalize_tracks", True)):
                self._normalize_mkv_tracks(
                    output_file,
                    reset_video_language=bool(config.get("reset_video_language", True)),
                )
            finished_at = self._now_str()
            self._update_history_record(
                dedupe_key,
                remux={
                    "finished_at": finished_at,
                    "duration_seconds": int(time.time() - started_at),
                    "error": None,
                },
                finished_at=finished_at,
            )
            logger.info(
                "下载目录原盘重封装完成: "
                f"source={source_root}, output={output_file}, duration={int(time.time() - started_at)}s"
            )

            triggered_transfer, new_transfer_history_id = self._post_process_intercept_output(
                output_file=output_file,
                download_history=download_history,
                config=config,
            )

            self._update_history_record(
                dedupe_key,
                status="success",
                post_action={
                    "source_cleanup": self._cleanup_intercept_source(source_root, config, download_history=download_history),
                    "triggered_transfer": triggered_transfer,
                    "new_transfer_history_id": new_transfer_history_id,
                },
                finished_at=self._now_str(),
            )
            self._message = f"下载目录原盘重封装完成: {output_file}"
            logger.info(
                "下载器拦截重封装流程完成: "
                f"source={source_root}, output={output_file}, triggered_transfer={triggered_transfer}, "
                f"new_transfer_history_id={new_transfer_history_id}"
            )
        except subprocess.CalledProcessError as e:
            error = e.stderr or str(e)
            self._update_history_record(
                dedupe_key,
                status="failed",
                remux={"error": error, "finished_at": self._now_str()},
                finished_at=self._now_str(),
            )
            logger.error(f"拦截重封装失败: source={source_root}, error={error}")
        except Exception as e:
            self._update_history_record(
                dedupe_key,
                status="failed",
                remux={"error": str(e), "finished_at": self._now_str()},
                finished_at=self._now_str(),
            )
            logger.error(f"拦截重封装处理失败: source={source_root}, error={e}", exc_info=True)
        finally:
            with self._intercept_lock:
                self._active_intercepts.discard(dedupe_key)
            if "remuxer" in locals():
                self._unregister_remuxer(remuxer)

    @staticmethod
    def _normalize_mkv_tracks(output_file: Path, reset_video_language: bool = True) -> None:
        """规范化 MKV 内部音轨和字幕轨标题。"""
        if not output_file.exists() or not output_file.is_file():
            logger.warning(f"重封装输出不存在，跳过轨道规范化: {output_file}")
            return
        if not TrackNormalizer.available():
            logger.warning("未检测到 mkvtoolnix，跳过 MKV 轨道规范化。")
            return
        edits = TrackNormalizer(reset_video_language=reset_video_language).normalize(output_file)
        logger.info(f"MKV 轨道规范化已应用 {len(edits)} 项修改: {output_file}")

    def _post_process_intercept_output(self, output_file: Path, download_history, config: dict) -> Tuple[bool, Optional[int]]:
        if not bool(config.get("intercept_transfer_mkv", True)):
            logger.info(f"配置为不整理重封装 MKV，跳过后续整理: output={output_file}")
            return False, None

        logger.info(
            "开始整理重封装 MKV: "
            f"output={output_file}, downloader={self._history_value(download_history, 'downloader')}, "
            f"hash={self._history_value(download_history, 'download_hash')}, "
            f"tmdbid={self._history_value(download_history, 'tmdbid')}"
        )
        state, errmsg = self._transfer_remuxed_mkv(output_file, download_history)
        if not state:
            raise RuntimeError(f"重封装后整理失败: {errmsg}")
        transfer_history = TransferHistoryOper().get_by_src(output_file.as_posix(), storage="local")
        logger.info(
            "重封装 MKV 整理完成: "
            f"output={output_file}, transfer_history_id={transfer_history.id if transfer_history else None}"
        )
        if transfer_history and bool(config.get("refresh_media_server", True)):
            self._refresh_media_server(transfer_history, output_file)
        return True, transfer_history.id if transfer_history else None

    def _cleanup_source_disc_after_success(self, source_root: Path, source_disc_action: str, download_history=None) -> str:
        """在新 MKV 成功入库后按策略处理源文件原盘，并绑定删除下载器原任务。"""
        if source_disc_action != "delete":
            logger.info(f"配置为保留源文件原盘: source={source_root}")
            return "keep"
        if not self._is_valid_disc_source(source_root):
            logger.info(f"源文件原盘已不存在，跳过源文件删除: source={source_root}")
            return "source_missing"
        download_hash = self._history_value(download_history, "download_hash") if download_history else None
        downloader = self._history_value(download_history, "downloader") if download_history else None
        if download_hash:
            try:
                result = self.chain.remove_torrents(hashs=[download_hash], delete_file=True, downloader=downloader)
                logger.info(f"已删除下载器原任务并请求删除源文件: downloader={downloader}, hash={download_hash}, result={result}")
                return "delete_source_and_torrent"
            except Exception as err:
                logger.warning(f"删除下载器原任务失败，将继续删除本地源文件: downloader={downloader}, hash={download_hash}, error={err}")
        self._delete_local_path_safely(source_root)
        logger.info(f"已删除源文件原盘: {source_root}")
        return "delete_source_only"

    def _cleanup_intercept_source(self, source_root: Path, config: dict, download_history=None) -> str:
        """兼容下载目录拦截流程的源文件原盘清理。"""
        return self._cleanup_source_disc_after_success(
            source_root=source_root,
            source_disc_action=self._source_disc_action(config),
            download_history=download_history,
        )

    @staticmethod
    def _delete_local_path_safely(source_path: Path) -> None:
        """安全删除本地源文件原盘路径。"""
        if len(source_path.parts) <= 3:
            raise RuntimeError(f"拒绝删除过浅路径: {source_path}")
        if not source_path.exists() and not source_path.is_symlink():
            return
        if source_path.is_dir() and not source_path.is_symlink():
            shutil.rmtree(source_path)
        else:
            source_path.unlink()

    @staticmethod
    def _media_type_from_download_history(download_history) -> Optional[MediaType]:
        try:
            return MediaType(DiscRemuxPlugin._history_value(download_history, "type"))
        except Exception:
            return None

    def _transfer_remuxed_mkv(self, output_file: Path, download_history) -> Tuple[bool, Any]:
        if not output_file.exists() or not output_file.is_file():
            return False, f"重封装 MKV 不存在: {output_file}"

        fileitem = schemas.FileItem(
            storage="local",
            path=output_file.as_posix(),
            type="file",
            name=output_file.name,
            basename=output_file.stem,
            extension=output_file.suffix.lstrip("."),
            size=output_file.stat().st_size,
        )
        return TransferChain().manual_transfer(
            fileitem=fileitem,
            tmdbid=self._history_value(download_history, "tmdbid"),
            doubanid=self._history_value(download_history, "doubanid"),
            mtype=self._media_type_from_download_history(download_history),
            episode_group=self._history_value(download_history, "episode_group"),
            background=False,
            downloader=self._history_value(download_history, "downloader"),
            download_hash=self._history_value(download_history, "download_hash"),
            transfer_type="link",
            sync_extra_files=False,
        )
