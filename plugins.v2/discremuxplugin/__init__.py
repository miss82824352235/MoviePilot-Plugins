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

from fastapi import Body

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
from .task_manager import TaskManager
from .track_normalizer import TrackNormalizer


class DiscRemuxPlugin(_PluginBase):
    """蓝光原盘重封装插件。"""

    plugin_name = "蓝光原盘重封装"
    plugin_desc = "处理源文件目录中的 ISO/BDMV 原盘，重封装为 MKV 后交给 MoviePilot 硬链接整理入库，并提供任务控制台。"
    plugin_icon = "https://raw.githubusercontent.com/the-bruz/MoviePilot-Plugins/main/icons/discremuxplugin.png"
    plugin_version = "2.7.2"
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
    _task_manager: Optional[TaskManager] = None

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
        if "library_scan_interval_minutes" not in config:
            # 源文件补漏扫描默认每 10 分钟；0 表示回退到 cron
            config["library_scan_interval_minutes"] = 10
            changed = True
        if "library_scan_max_items" not in config:
            config["library_scan_max_items"] = 50
            changed = True
        if "min_free_space_gb" not in config:
            config["min_free_space_gb"] = 120
            changed = True
        if "max_workers" not in config:
            config["max_workers"] = 2
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
        if self._task_manager is None:
            self._task_manager = TaskManager(self)
        else:
            # 重载后重建 worker，保留已加载快照
            self._task_manager.plugin = self
            self._task_manager.ensure_worker()

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
            try:
                interval_minutes = int(config.get("library_scan_interval_minutes") or 0)
            except Exception:
                interval_minutes = 0
            if interval_minutes > 0:
                from apscheduler.triggers.interval import IntervalTrigger
                services.append(
                    {
                        "id": f"{self.__class__.__name__}.library_scan_remux",
                        "name": "定时扫描源文件原盘补漏重封装",
                        "trigger": IntervalTrigger(minutes=max(1, interval_minutes)),
                        "func": self.library_scan_remux,
                        "kwargs": {},
                    }
                )
            else:
                cron_str = config.get("library_scan_cron") or "30 3 * * *"
                services.append(
                    {
                        "id": f"{self.__class__.__name__}.library_scan_remux",
                        "name": "定时扫描源文件原盘补漏重封装",
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
        if self._task_manager is not None:
            try:
                self._task_manager.stop()
            except Exception as e:
                logger.warning(f"停止任务管理器失败: {e}")
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
        """Vue 模式下返回默认配置模型。"""
        default_config = {
            "history_enabled": False,
            "run_once": False,
            "library_scan_enabled": False,
            "library_scan_run_once": False,
            "library_scan_cron": "30 3 * * *",
            "library_scan_interval_minutes": 10,
            "source_root": "/PT/mp/源文件",
            "source_roots": "/PT/mp/源文件\n/PT/ms/源文件",
            "library_root": "/PT/mp/硬链接",
            "library_roots": "/PT/mp/硬链接\n/PT/ms/硬链接",
            "library_scan_max_items": 50,
            "max_workers": 2,
            "recent_days": 7,
            "min_mkv_size_gb": 5,
            "min_free_space_gb": 120,
            "movies_only": True,
            "source_disc_action": "delete",
            "library_disc_action": "delete",
            "refresh_media_server": True,
            "cron_schedule": "0 3 * * *",
            "intercept_enabled": False,
            "intercept_transfer_mkv": True,
            "normalize_tracks": True,
            "reset_video_language": True,
        }
        return [], default_config

    def get_page(self) -> List[dict]:
        """Vue 模式下详情页由远程组件渲染。"""
        return []


    @staticmethod
    def get_render_mode() -> Tuple[str, str]:
        """声明插件使用 Vue 联邦组件渲染任务控制台。"""
        return "vue", "dist/assets"

    def get_sidebar_nav(self) -> List[Dict[str, Any]]:
        """侧栏入口：原盘重封装任务控制台。"""
        if not self.get_state():
            return []
        return [{
            "nav_key": "console",
            "title": "原盘重封装",
            "icon": "mdi-disc",
            "section": "organize",
            "permission": "manage",
            "order": 55,
        }]

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        bear = "bear"
        return [
            {
                "path": "/clear_processed",
                "endpoint": self.clear_processed_histories,
                "methods": ["POST"],
                "auth": bear,
                "summary": "清空已处理历史",
                "description": "清空插件记录的 processed history id，用于允许重新处理整理历史。",
            },
            {
                "path": "/library_scan_preview",
                "endpoint": self.library_scan_preview,
                "methods": ["POST"],
                "auth": bear,
                "summary": "预览已入库原盘扫描任务",
                "description": "只扫描源文件和硬链接库中的 BDMV 候选，不执行重封装、整理、删除或媒体库刷新。",
            },
            {
                "path": "/status",
                "endpoint": self.api_status,
                "methods": ["GET"],
                "auth": bear,
                "summary": "任务控制台状态",
            },
            {
                "path": "/tasks",
                "endpoint": self.api_tasks,
                "methods": ["GET"],
                "auth": bear,
                "summary": "任务列表",
            },
            {
                "path": "/task_control",
                "endpoint": self.api_task_control,
                "methods": ["POST"],
                "auth": bear,
                "summary": "任务控制（暂停/继续/跳过/终止）",
            },
            {
                "path": "/enqueue_scan",
                "endpoint": self.api_enqueue_scan,
                "methods": ["POST"],
                "auth": bear,
                "summary": "扫描源文件并入队重封装任务",
            },
            {
                "path": "/enqueue_paths",
                "endpoint": self.api_enqueue_paths,
                "methods": ["POST"],
                "auth": bear,
                "summary": "手动按源路径入队",
            },
        ]

    def _ensure_task_manager(self) -> TaskManager:
        if self._task_manager is None:
            self._task_manager = TaskManager(self)
        return self._task_manager

    def api_status(self) -> schemas.Response:
        tm = self._ensure_task_manager()
        data = tm.status()
        config = self.get_config() or {}
        data["plugin"] = {
            "version": self.plugin_version,
            "history_enabled": self._history_enabled,
            "library_scan_enabled": self._library_scan_enabled,
            "intercept_enabled": self._intercept_enabled,
            "source_roots": self._parse_path_list(config.get("source_roots") or config.get("source_root")),
            "min_free_space_gb": config.get("min_free_space_gb", 120),
            "max_workers": config.get("max_workers", 2),
            "message": self._message,
        }
        return schemas.Response(success=True, message="ok", data=data)

    def api_tasks(self) -> schemas.Response:
        tm = self._ensure_task_manager()
        return schemas.Response(success=True, message="ok", data={"tasks": tm.list_tasks(limit=100)})

    def api_task_control(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        payload = payload if isinstance(payload, dict) else {}
        action = str(payload.get("action") or "").strip().lower()
        task_ids = payload.get("task_ids") or []
        if isinstance(task_ids, str):
            task_ids = [x.strip() for x in task_ids.split(",") if x.strip()]
        select_all = bool(payload.get("select_all"))
        confirm = bool(payload.get("confirm"))
        if not action:
            return schemas.Response(success=False, message="缺少 action")
        tm = self._ensure_task_manager()
        result = tm.control(action=action, task_ids=task_ids, select_all=select_all, confirm=confirm)
        return schemas.Response(
            success=bool(result.get("success")),
            message=result.get("message") or "",
            data=result.get("data"),
        )

    def api_enqueue_scan(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        payload = payload if isinstance(payload, dict) else {}
        confirm = bool(payload.get("confirm"))
        if not confirm:
            return schemas.Response(
                success=False,
                message="扫描入队会创建真实重封装任务，请 confirm=true 后执行",
                data={"need_confirm": True},
            )
        max_items = payload.get("max_items")
        count = self.enqueue_library_scan_tasks(max_items=max_items)
        return schemas.Response(success=True, message=f"已入队 {count} 个任务", data={"enqueued": count})

    def api_enqueue_paths(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        payload = payload if isinstance(payload, dict) else {}
        confirm = bool(payload.get("confirm"))
        if not confirm:
            return schemas.Response(
                success=False,
                message="手动入队会创建真实重封装任务，请 confirm=true 后执行",
                data={"need_confirm": True},
            )
        paths = payload.get("paths") or []
        if isinstance(paths, str):
            paths = [x.strip() for x in paths.splitlines() if x.strip()]
        if not paths:
            return schemas.Response(success=False, message="未提供 paths")
        enqueued = []
        for p in paths:
            task = self.enqueue_source_path(p, mode="manual")
            if task:
                enqueued.append(task.id if hasattr(task, "id") else task.get("id"))
        return schemas.Response(success=True, message=f"已入队 {len(enqueued)} 个任务", data={"task_ids": enqueued})

    def enqueue_source_path(
        self,
        source_path: str,
        *,
        mode: str = "manual",
        library_path: Optional[str] = None,
        download_hash: Optional[str] = None,
        downloader: Optional[str] = None,
        tmdbid: Optional[int] = None,
        media_type: Optional[str] = None,
        transfer_history_id: Optional[int] = None,
        dedupe_key: Optional[str] = None,
        extra: Optional[dict] = None,
    ):
        source = Path(source_path)
        if not self._is_valid_disc_source(source):
            logger.warning(f"入队失败，源不是有效原盘: {source}")
            return None
        config = self.get_config() or {}
        roots = self._parse_path_list(config.get("source_roots") or config.get("source_root"))
        if roots and not self._under_any_source_root(source, roots):
            logger.warning(f"入队失败，源不在 source_roots 内: {source}")
            return None
        media_kind = self._source_media_kind(source, roots)
        output = self._output_for_disc_source(source)
        if media_kind == "tv":
            output = self._tv_episode_output_for_disc(source, self._tv_episode_start_for_disc(source))
        size = 0
        try:
            if source.is_file():
                size = source.stat().st_size
        except Exception:
            size = 0
        tm = self._ensure_task_manager()
        task_extra = dict(extra or {})
        task_extra["source_media_kind"] = media_kind
        if transfer_history_id:
            task_extra["transfer_history_id"] = transfer_history_id
        # 若调用方指定了 output_path，优先使用
        if task_extra.get("output_path"):
            output = Path(task_extra["output_path"])
        task = tm.enqueue(
            title=source.name,
            source_path=source.as_posix(),
            output_path=output.as_posix(),
            disc_type=self._disc_type(source),
            mode=mode,
            source_size=size,
            download_hash=download_hash,
            downloader=downloader,
            tmdbid=tmdbid,
            media_type=media_type,
            library_path=library_path,
            dedupe_key=dedupe_key or f"{mode}:{source.as_posix()}",
            extra=task_extra,
            start_worker=True,
        )
        return task

    def enqueue_library_scan_tasks(self, max_items: Optional[int] = None) -> int:
        config = self.get_config() or {}
        source_root = Path(str(config.get("source_root") or "/PT/mp/源文件")).resolve()
        library_root = Path(str(config.get("library_root") or "/PT/mp/硬链接")).resolve()
        limit = int(max_items or config.get("library_scan_max_items") or 50)
        source_dirs, library_dirs, tasks, _ = self._build_library_scan_tasks(
            source_root=source_root,
            library_root=library_root,
            max_items=limit,
        )
        logger.info(
            "扫描入队候选: "
            f"source_candidates={len(source_dirs)}, library_candidates={len(library_dirs)}, tasks={len(tasks)}"
        )
        count = 0
        for source_movie_dir, library_movie_dir in tasks.values():
            history = self._find_related_transfer_history(library_movie_dir, source_movie_dir)
            media_kind = self._source_media_kind(source_movie_dir, self._parse_path_list(config.get("source_roots") or config.get("source_root")))
            if media_kind == "unknown" and bool(config.get("movies_only", True)) and history and history.type != MediaType.MOVIE.value:
                continue
            output_file = self._output_for_disc_source(source_movie_dir)
            if media_kind == "tv":
                output_file = self._tv_episode_output_for_disc(source_movie_dir, self._tv_episode_start_for_disc(source_movie_dir))
            min_size_gb = float(config.get("min_mkv_size_gb") or 5)
            if self._target_mkv_exists(output_file, min_size_gb):
                continue
            task = self.enqueue_source_path(
                source_movie_dir.as_posix(),
                mode="library_scan",
                library_path=library_movie_dir.as_posix() if library_movie_dir else None,
                transfer_history_id=history.id if history else None,
                tmdbid=history.tmdbid if history else None,
                media_type=history.type if history else None,
                dedupe_key=f"library_scan:{source_movie_dir.as_posix()}",
            )
            if task:
                count += 1
        self._message = f"已扫描入队 {count} 个重封装任务。"
        return count

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

    @classmethod
    def _source_media_kind(cls, source_path: Path, source_roots: Optional[List[Path]] = None) -> str:
        """根据源文件一级类型目录判定电影或电视剧硬分流。"""
        path = source_path.resolve()
        for root in source_roots or []:
            try:
                rel = path.relative_to(root.resolve())
            except Exception:
                continue
            if rel.parts and rel.parts[0] == "电影":
                return "movie"
            if rel.parts and rel.parts[0] == "电视剧":
                return "tv"
        parts = path.parts
        if "电影" in parts:
            return "movie"
        if "电视剧" in parts:
            return "tv"
        return "unknown"

    @staticmethod
    def _disc_number_from_name(source_path: Path) -> Optional[int]:
        """从文件名中提取 DISC 序号。"""
        import re
        match = re.search(r"(?i)disc[ ._-]?(\d+)", source_path.name)
        if not match:
            return None
        try:
            return int(match.group(1))
        except Exception:
            return None

    @staticmethod
    def _season_number_from_name(source_path: Path) -> int:
        """从路径名中提取季号，默认第一季。"""
        import re
        match = re.search(r"(?i)S(\d{1,2})", source_path.as_posix())
        if not match:
            return 1
        try:
            return int(match.group(1))
        except Exception:
            return 1

    @classmethod
    def _tv_episode_start_for_disc(cls, source_path: Path, episode_count: int = 0) -> int:
        """根据 DISC 序号估算电视剧单集起始集号。"""
        disc = cls._disc_number_from_name(source_path)
        if not disc or disc <= 1:
            return 1
        return (disc - 1) * 3 + 1

    @classmethod
    def _tv_episode_output_for_disc(cls, source_path: Path, episode_number: int) -> Path:
        """生成电视剧单集 MKV 输出名，沿用 ISO 基础名并追加 SxxExx。"""
        import re
        season = cls._season_number_from_name(source_path)
        base = source_path.stem if source_path.is_file() else source_path.name
        base = re.sub(r"(?i)[ ._-]*disc[ ._-]?\d+.*$", "", base).strip(" ._-") or source_path.stem
        season_tag = f"S{season:02d}"
        if re.search(rf"(?i)(^|[ ._-]){season_tag}$", base):
            return source_path.parent / f"{base}E{episode_number:02d}.mkv"
        return source_path.parent / f"{base}.{season_tag}E{episode_number:02d}.mkv"

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

    def _transfer_source_mkv(self, output_file: Path, history=None, source_root: Optional[Path] = None) -> Tuple[bool, Any]:
        """调用 MoviePilot 正常整理链路转移源文件目录中的 MKV。"""
        if not output_file.exists() or not output_file.is_file():
            return False, f"重封装 MKV 不存在: {output_file}"
        download_hash = getattr(history, "download_hash", None) if history else None
        self._clear_stale_disc_transfer_histories(
            download_hash=download_hash,
            source_root=source_root or output_file.parent,
            output_file=output_file,
        )
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
            download_hash=download_hash,
            transfer_type="link",
            sync_extra_files=False,
            force=True,
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
        media_kind = self._source_media_kind(source_movie_dir, self._parse_path_list((self.get_config() or {}).get("source_roots") or (self.get_config() or {}).get("source_root")))
        if media_kind == "unknown" and movies_only and history and history.type != MediaType.MOVIE.value:
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
        """定时扫描源文件原盘并入队可视化任务队列（串行执行）。"""
        if self._stop_event.is_set():
            return False
        count = self.enqueue_library_scan_tasks()
        logger.info(f"library_scan_remux 入队完成: {count}")
        return True


    def history_remux(self) -> bool:
        """兼容旧配置入口：不再从硬链接库直接重封装，只提示使用源文件扫描模式。"""
        self._message = (
            "整理历史模式已停用：按当前安全约束，插件只从源文件目录查找 ISO/BDMV，"
            "请使用源文件扫描模式或下载目录拦截模式。"
        )
        logger.warning(self._message)
        return True


    @classmethod
    def _candidate_download_lookup_paths(cls, source_root: Path) -> List[str]:
        """构造下载历史/文件记录回溯候选路径。"""
        paths: List[str] = []
        try:
            resolved = source_root.resolve()
        except Exception:
            resolved = source_root
        for item in (source_root, resolved):
            text = item.as_posix()
            if text and text not in paths:
                paths.append(text)
        # ISO/IMG 可能记在父目录；BDMV 目录记在影片根目录
        parents = []
        if source_root.suffix.lower() in {".iso", ".img"} or source_root.is_file():
            parents.append(source_root.parent)
        if source_root.name.upper() == "BDMV":
            parents.append(source_root.parent)
        parents.append(source_root.parent)
        for parent in parents:
            if not parent or parent.as_posix() in {"/", "."}:
                continue
            text = parent.as_posix()
            if text not in paths:
                paths.append(text)
        return paths

    @classmethod
    def _resolve_intercept_download_history(cls, source_root: Path):
        """按文件记录、完整路径、父级内容路径和 hash 回溯 MoviePilot 下载归属。

        兼容 DownloadHistory.path 只记保存目录、而 fileitem 指向单文件 ISO/BDMV 的场景，
        避免“非 MoviePilot 下载历史”误跳过拦截。
        """
        downloadhis = DownloadHistoryOper()
        lookup_paths = cls._candidate_download_lookup_paths(source_root)

        for path_text in lookup_paths:
            try:
                download_hash = downloadhis.get_hash_by_fullpath(path_text)
            except Exception:
                download_hash = None
            if download_hash:
                history = downloadhis.get_by_hash(download_hash)
                if history:
                    return history

            try:
                download_files = downloadhis.get_files_by_fullpath(path_text) or []
            except Exception:
                download_files = []
            for download_file in download_files:
                if download_file and download_file.download_hash:
                    history = downloadhis.get_by_hash(download_file.download_hash)
                    if history:
                        return history

            try:
                download_file = downloadhis.get_file_by_fullpath(path_text)
            except Exception:
                download_file = None
            if download_file and download_file.download_hash:
                history = downloadhis.get_by_hash(download_file.download_hash)
                if history:
                    return history

            history = downloadhis.get_by_path(path_text)
            if history:
                return history

        # 保存目录级文件清单：同目录单 hash，或文件名精确匹配
        source_name = source_root.name
        source_posix = source_root.as_posix()
        for parent_path in list(source_root.parents)[:6]:
            parent_text = parent_path.as_posix()
            if parent_text in {"/", ""}:
                continue
            history = downloadhis.get_by_path(parent_text)
            if history:
                return history
            try:
                download_files = downloadhis.get_files_by_savepath(parent_text) or []
            except Exception:
                download_files = []
            if not download_files:
                continue
            matched_hashes = set()
            for item in download_files:
                if not item or not item.download_hash:
                    continue
                fullpath = item.fullpath or ""
                filepath = item.filepath or ""
                if (
                    fullpath == source_posix
                    or fullpath.endswith("/" + source_name)
                    or Path(fullpath).name == source_name
                    or Path(filepath).name == source_name
                    or (fullpath and Path(fullpath).parent == source_root.parent)
                    or (source_root.is_dir() and fullpath.startswith(source_posix.rstrip("/") + "/"))
                ):
                    matched_hashes.add(item.download_hash)
            if len(matched_hashes) == 1:
                history = downloadhis.get_by_hash(next(iter(matched_hashes)))
                if history:
                    return history
            # 整个保存目录只对应一个下载任务时，也视为归属该任务
            all_hashes = {item.download_hash for item in download_files if item and item.download_hash}
            if len(all_hashes) == 1:
                history = downloadhis.get_by_hash(next(iter(all_hashes)))
                if history:
                    return history

        return None

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

        download_history = self._resolve_intercept_download_history(source_root)
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
        """下载目录拦截后改为入队可视化任务，由 TaskManager 串行执行。"""
        try:
            logger.info(f"拦截原盘入队重封装: source={source_root}, output={output_file}")
            task = self.enqueue_source_path(
                source_root.as_posix(),
                mode="intercept",
                download_hash=self._history_value(download_history, "download_hash"),
                downloader=self._history_value(download_history, "downloader"),
                tmdbid=self._history_value(download_history, "tmdbid"),
                media_type=self._history_value(download_history, "type"),
                dedupe_key=dedupe_key,
                extra={
                    "output_path": output_file.as_posix(),
                },
            )
            if not task:
                raise RuntimeError("拦截任务入队失败")
            self._update_history_record(
                dedupe_key,
                status="waiting",
                remux={"queued_at": self._now_str(), "task_id": task.id if hasattr(task, "id") else None},
            )
            self._message = f"拦截原盘已入队: {source_root.name}"
        except Exception as e:
            self._update_history_record(
                dedupe_key,
                status="failed",
                remux={"error": str(e), "finished_at": self._now_str()},
                finished_at=self._now_str(),
            )
            logger.error(f"拦截重封装入队失败: source={source_root}, error={e}", exc_info=True)
        finally:
            with self._intercept_lock:
                self._active_intercepts.discard(dedupe_key)

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

        download_hash = self._history_value(download_history, "download_hash")
        source_hint = None
        try:
            history_path = self._history_value(download_history, "path")
            if history_path:
                source_hint = Path(history_path)
        except Exception:
            source_hint = None
        # 输出 MKV 同目录的 ISO/BDMV 也作为清理线索
        try:
            source_hint = source_hint or output_file.with_suffix(".iso")
        except Exception:
            pass
        self._clear_stale_disc_transfer_histories(
            download_hash=download_hash,
            source_root=source_hint if source_hint and source_hint.exists() else output_file.parent,
            output_file=output_file,
        )

        logger.info(
            "开始整理重封装 MKV: "
            f"output={output_file}, downloader={self._history_value(download_history, 'downloader')}, "
            f"hash={download_hash}, "
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

    def _delete_source_disc_only(self, source_root: Path) -> bool:
        """只删除源文件原盘（ISO/IMG/BDMV/CERTIFICATE），保留同目录已生成的 MKV。"""
        if not source_root:
            return False
        deleted = False
        try:
            if self._is_disc_image_file(source_root):
                self._delete_local_path_safely(source_root)
                deleted = True
                # 同目录残留 CERTIFICATE/BDMV 一并清理，但不动 *.mkv
                parent = source_root.parent
                for name in ("BDMV", "CERTIFICATE"):
                    candidate = parent / name
                    if candidate.exists():
                        self._delete_local_path_safely(candidate)
                        deleted = True
                return deleted

            # BDMV 影片目录
            if source_root.is_dir():
                bdmv = source_root / "BDMV"
                cert = source_root / "CERTIFICATE"
                if self._is_valid_bdmv_dir(bdmv):
                    self._delete_local_path_safely(bdmv)
                    deleted = True
                if cert.exists():
                    self._delete_local_path_safely(cert)
                    deleted = True
                for image in list(source_root.glob("*.iso")) + list(source_root.glob("*.img")):
                    if self._is_disc_image_file(image):
                        self._delete_local_path_safely(image)
                        deleted = True
                return deleted
        except Exception as err:
            logger.warning(f"删除源文件原盘失败: source={source_root}, error={err}")
            raise
        return deleted

    def _cleanup_source_disc_after_success(self, source_root: Path, source_disc_action: str, download_history=None) -> str:
        """MKV 成功入库后：源目录只留 MKV；删除 qB 任务但不删剩余源文件。

        注意：绝不能 remove_torrents(delete_file=True)，否则会把刚生成的 MKV 一起删掉。
        """
        if source_disc_action != "delete":
            logger.info(f"配置为保留源文件原盘: source={source_root}")
            return "keep"

        disc_still_there = self._is_valid_disc_source(source_root)
        disc_deleted = False
        if disc_still_there:
            disc_deleted = self._delete_source_disc_only(source_root)
            logger.info(f"已删除源文件原盘并保留 MKV: source={source_root}, deleted={disc_deleted}")
        else:
            logger.info(f"源文件原盘已不存在，仅尝试删除下载器任务: source={source_root}")

        download_hash = self._history_value(download_history, "download_hash") if download_history else None
        downloader = self._history_value(download_history, "downloader") if download_history else None
        torrent_deleted = False
        if download_hash:
            try:
                result = self.chain.remove_torrents(
                    hashs=[download_hash],
                    delete_file=False,
                    downloader=downloader,
                )
                torrent_deleted = bool(result) if result is not None else True
                logger.info(
                    "已删除下载器原任务并保留源目录 MKV: "
                    f"downloader={downloader}, hash={download_hash}, result={result}"
                )
            except Exception as err:
                logger.warning(
                    f"删除下载器原任务失败: downloader={downloader}, hash={download_hash}, error={err}"
                )

        if disc_deleted and torrent_deleted:
            return "delete_disc_and_torrent_keep_mkv"
        if disc_deleted:
            return "delete_disc_keep_mkv"
        if torrent_deleted:
            return "delete_torrent_only"
        if not disc_still_there:
            return "source_missing"
        return "cleanup_noop"

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

    @classmethod
    def _is_disc_transfer_history(cls, history) -> bool:
        """判断整理记录是否指向 ISO/IMG/BDMV 原盘，而非 MKV。"""
        if not history:
            return False
        src = (getattr(history, "src", None) or "").lower()
        dest = (getattr(history, "dest", None) or "").lower()
        markers = (".iso", ".img", "/bdmv", "bdmv/", "\bdmv", "certificate/")
        if any(marker in src or marker in dest for marker in markers):
            return True
        return cls._is_bdmv_history(history)

    def _clear_stale_disc_transfer_histories(
            self,
            download_hash: Optional[str] = None,
            source_root: Optional[Path] = None,
            output_file: Optional[Path] = None,
    ) -> int:
        """整理 MKV 前清理原盘相关旧转移记录，避免“已整理过”阻断或复用原盘记录。"""
        oper = TransferHistoryOper()
        candidates = []
        if download_hash:
            try:
                candidates.extend(oper.list_by_hash(download_hash) or [])
            except Exception as err:
                logger.warning(f"按 hash 查询转移记录失败: hash={download_hash}, error={err}")

        path_candidates: List[str] = []
        if source_root is not None:
            path_candidates.extend(self._candidate_download_lookup_paths(source_root))
            if source_root.is_file():
                path_candidates.append(source_root.as_posix())
            else:
                path_candidates.append((source_root / "BDMV").as_posix())
        if output_file is not None:
            # 仅清理失败的 MKV 记录；成功 MKV 记录留给 force 覆盖逻辑
            try:
                mkv_history = oper.get_by_src(output_file.as_posix(), storage="local")
                if mkv_history and not bool(mkv_history.status):
                    candidates.append(mkv_history)
            except Exception:
                pass

        for path_text in path_candidates:
            try:
                history = oper.get_by_src(path_text, storage="local")
                if history:
                    candidates.append(history)
            except Exception:
                continue
            try:
                history = oper.get_by_dest(path_text)
                if history:
                    candidates.append(history)
            except Exception:
                continue

        deleted = 0
        seen = set()
        for history in candidates:
            if not history or getattr(history, "id", None) in seen:
                continue
            seen.add(history.id)
            if not self._is_disc_transfer_history(history):
                continue
            try:
                oper.delete(history.id)
                deleted += 1
                logger.info(
                    "已删除原盘旧转移记录: "
                    f"id={history.id}, src={getattr(history, 'src', None)}, dest={getattr(history, 'dest', None)}"
                )
            except Exception as err:
                logger.warning(f"删除原盘旧转移记录失败: id={getattr(history, 'id', None)}, error={err}")
        if deleted:
            logger.info(f"整理前共清理 {deleted} 条原盘转移记录")
        return deleted

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
            force=True,
        )
