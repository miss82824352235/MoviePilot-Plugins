"""字幕网页上传器。"""
from __future__ import annotations

import base64
import os
import shutil
import time
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.event import eventmanager
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType
from app.schemas.types import EventType

from .console import render_console
from .models import SubtitleWebSession
from .ui import build_form, build_page
from .web_api import SubtitleWebApi


class SubtitleWebUploader(_PluginBase):
    """字幕网页上传器插件。"""

    plugin_name = "字幕网页上传器"
    plugin_desc = "TG 网页入口 + Web 操作台，桥接字幕匹配魔改版：上传/在线/外挂管理/AI 源策略/重做/在线→AI/备份恢复与任务进度。"
    plugin_icon = "https://raw.githubusercontent.com/jxxghp/MoviePilot-Plugins/main/icons/subtitle.png"
    plugin_version = "v0.6.0"
    plugin_author = "MoviePilot Agent"
    author_url = "https://github.com/jxxghp/MoviePilot"
    plugin_config_prefix = "subtitleweb_"
    plugin_order = 99
    auth_level = 1

    _enabled: bool = False
    _root_path: str = ""
    _allowed_users: List[str] = []
    _session_timeout: int = 3600
    _console_title: str = "字幕操作台"
    _tg_entry_enabled: bool = True
    _legacy_api_enabled: bool = False
    _console_base_url: str = ""
    _supported_video_exts = {".mkv", ".mp4", ".ts", ".avi", ".mov", ".m2ts"}

    def init_plugin(self, config: dict = None) -> None:
        """根据插件配置初始化运行状态。"""
        config = config or {}
        self._enabled = bool(config.get("enabled", False))
        self._root_path = str(config.get("root_path") or "").strip()
        self._allowed_users = [u.strip() for u in str(config.get("allowed_users") or "").split(",") if u.strip()]
        self._session_timeout = int(config.get("session_timeout") or 3600)
        self._console_title = str(config.get("console_title") or "字幕操作台").strip() or "字幕操作台"
        self._tg_entry_enabled = bool(config.get("tg_entry_enabled", True))
        self._legacy_api_enabled = bool(config.get("legacy_api_enabled", False))
        self._console_base_url = str(config.get("console_base_url") or "").strip().rstrip("/")
        if self._enabled:
            os.makedirs(self._get_data_path(), exist_ok=True)
        logger.info(
            "SubtitleWebUploader v%s 初始化完成，启用=%s，TG入口=%s，旧API=%s",
            self.plugin_version,
            self._enabled,
            self._tg_entry_enabled,
            self._legacy_api_enabled,
        )

    def get_state(self) -> bool:
        """获取插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """注册 TG/远程命令入口。"""
        return [
            {
                "cmd": "/subweb",
                "event": EventType.PluginAction,
                "desc": "打开字幕操作台",
                "category": "字幕",
                "data": {"action": "subtitleweb_open"},
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        """注册插件 API。"""
        api = SubtitleWebApi(self)
        routes: List[Dict[str, Any]] = [
            {"path": "/subtitleweb_bridge/status", "endpoint": api.status, "methods": ["GET"], "allow_anonymous": True, "summary": "查询字幕操作台状态"},
            {"path": "/subtitleweb_bridge/console", "endpoint": self.api_console, "methods": ["GET"], "allow_anonymous": True, "summary": "打开字幕网页操作台"},
            {"path": "/subtitleweb_bridge/search", "endpoint": api.search, "methods": ["GET"], "allow_anonymous": True, "summary": "搜索本地媒体候选"},
            {"path": "/subtitleweb_bridge/targets", "endpoint": api.targets, "methods": ["GET"], "allow_anonymous": True, "summary": "读取媒体目标文件"},
            {"path": "/subtitleweb_bridge/history", "endpoint": api.history, "methods": ["GET"], "allow_anonymous": True, "summary": "读取字幕匹配历史"},
            {"path": "/subtitleweb_bridge/selection", "endpoint": api.get_selection, "methods": ["GET"], "allow_anonymous": True, "summary": "读取选择会话"},
            {"path": "/subtitleweb_bridge/selection/save", "endpoint": api.save_selection, "methods": ["POST"], "allow_anonymous": True, "summary": "保存选择会话"},
            {"path": "/subtitleweb_bridge/upload/prepare", "endpoint": api.upload_prepare, "methods": ["POST"], "allow_anonymous": True, "summary": "上传字幕并生成预览"},
            {"path": "/subtitleweb_bridge/upload/apply", "endpoint": api.upload_apply, "methods": ["POST"], "allow_anonymous": True, "summary": "确认写入字幕"},
            {"path": "/subtitleweb_bridge/delete/preview", "endpoint": api.delete_preview, "methods": ["POST"], "allow_anonymous": True, "summary": "删除字幕预检"},
            {"path": "/subtitleweb_bridge/delete/apply", "endpoint": api.delete_apply, "methods": ["POST"], "allow_anonymous": True, "summary": "确认删除字幕"},
            {"path": "/subtitleweb_bridge/clear/preview", "endpoint": api.clear_preview, "methods": ["POST"], "allow_anonymous": True, "summary": "清空外挂字幕预检"},
            {"path": "/subtitleweb_bridge/clear/apply", "endpoint": api.clear_apply, "methods": ["POST"], "allow_anonymous": True, "summary": "确认清空外挂字幕"},
            {"path": "/subtitleweb_bridge/ai/preview", "endpoint": api.ai_preview, "methods": ["POST"], "allow_anonymous": True, "summary": "AI 字幕任务预检"},
            {"path": "/subtitleweb_bridge/ai/submit", "endpoint": api.ai_submit, "methods": ["POST"], "allow_anonymous": True, "summary": "确认提交 AI 字幕任务"},
            {"path": "/subtitleweb_bridge/ai/cancel", "endpoint": api.ai_cancel, "methods": ["POST"], "allow_anonymous": True, "summary": "取消 AI 字幕任务"},
            {"path": "/subtitleweb_bridge/ai/restart", "endpoint": api.ai_restart, "methods": ["POST"], "allow_anonymous": True, "summary": "重新生成 AI 字幕任务"},
            {"path": "/subtitleweb_bridge/online_ai/submit", "endpoint": api.online_ai_submit, "methods": ["POST"], "allow_anonymous": True, "summary": "在线字幕转 AI 翻译"},
            {"path": "/subtitleweb_bridge/restore", "endpoint": api.restore, "methods": ["POST"], "allow_anonymous": True, "summary": "恢复字幕备份"},
            {"path": "/subtitleweb_bridge/timeline/fix", "endpoint": api.timeline_fix, "methods": ["POST"], "allow_anonymous": True, "summary": "历史外挂字幕调轴"},
            {"path": "/subtitleweb_bridge/tasks", "endpoint": api.tasks, "methods": ["POST"], "allow_anonymous": True, "summary": "查询字幕任务状态（含进度）"},
            {"path": "/subtitleweb_bridge/online/search", "endpoint": api.online_search, "methods": ["POST"], "allow_anonymous": True, "summary": "搜索在线字幕"},
            {"path": "/subtitleweb_bridge/online/download_preview", "endpoint": api.online_download_preview, "methods": ["POST"], "allow_anonymous": True, "summary": "在线字幕下载预览"},
        ]
        if self._legacy_api_enabled:
            routes.extend(self._legacy_routes())
        return routes

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """声明插件使用 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """返回 Vue 配置组件的默认配置。"""
        return [], self._current_config()

    def get_page(self) -> List[dict]:
        """Vue 模式下详情页由远程 Page 组件渲染。"""
        return []

    def _current_config(self) -> Dict[str, Any]:
        """返回当前配置快照。"""
        return {
            "enabled": bool(self._enabled),
            "console_title": self._console_title,
            "session_timeout": int(self._session_timeout),
            "tg_entry_enabled": bool(self._tg_entry_enabled),
            "legacy_api_enabled": bool(self._legacy_api_enabled),
            "console_base_url": self._console_base_url or "",
            "root_path": self._root_path or "",
        }

    def get_service(self) -> List[Dict[str, Any]]:
        """返回插件定时服务。"""
        return []

    def stop_service(self) -> None:
        """停止插件后台服务。"""
        logger.info("SubtitleWebUploader 停止服务")

    def api_console(self):
        """返回移动端网页操作台兼容入口。"""
        return render_console(self)

    @eventmanager.register(EventType.PluginAction)
    def open_console_action(self, event: Any = None) -> None:
        """响应 /subweb 命令并发送网页入口。"""
        if not event:
            return
        event_data = event.event_data or {}
        if event_data.get("action") != "subtitleweb_open":
            return
        if not self._enabled or not self._tg_entry_enabled:
            self.post_message(
                channel=event_data.get("channel"),
                title="字幕操作台未启用",
                text="请先在插件配置中启用「字幕网页上传器」和 TG 入口。",
                userid=event_data.get("user"),
            )
            return
        url = self._console_url()
        if not url:
            self.post_message(
                channel=event_data.get("channel"),
                title="字幕操作台地址未配置",
                text="当前 MoviePilot APP_DOMAIN 为空，不能给 Telegram 发送 127.0.0.1 这类仅本机可访问的地址。请在插件配置里填写『操作台外部访问地址』，例如 http://你的NAS-IP:3001 或 https://你的域名。\n\n配置后再发送 /subweb 即可打开操作台。",
                userid=event_data.get("user"),
                mtype=NotificationType.Plugin,
            )
            return
        buttons = [[{"text": "打开字幕操作台", "url": url}]]
        self.post_message(
            channel=event_data.get("channel"),
            title="字幕操作台",
            text=f"点击下方按钮打开移动端字幕操作台。\n\n访问地址：{url}\n\n写入、删除、清空和 AI 提交都会先预检/确认。",
            userid=event_data.get("user"),
            mtype=NotificationType.Plugin,
            buttons=buttons,
        )

    def _console_url(self) -> str:
        """生成网页操作台访问地址。"""
        base = self._console_base_url or str(getattr(settings, "APP_DOMAIN", "") or "").rstrip("/")
        if not base or "127.0.0.1" in base or "localhost" in base.lower():
            return ""
        return f"{base}/api/v1/plugin/SubtitleWebUploader/subtitleweb_bridge/console"

    def _web_session_key(self, user_id: str) -> str:
        """生成网页会话键。"""
        return f"subtitleweb.bridge.session.{user_id or 'web'}"

    def _load_web_session(self, user_id: str = "web") -> SubtitleWebSession:
        """加载网页操作台会话。"""
        key = self._web_session_key(user_id)
        session = SubtitleWebSession.from_dict(self.get_data(key), user_id)
        if time.time() - session.last_active > self._session_timeout:
            self.del_data(key)
            return SubtitleWebSession(user_id=user_id)
        return session

    def _save_web_session(self, session: SubtitleWebSession) -> None:
        """保存网页操作台会话。"""
        session.last_active = time.time()
        self.save_data(self._web_session_key(session.user_id), session.to_dict())

    def _legacy_routes(self) -> List[Dict[str, Any]]:
        """返回旧版硬链接目录 API。"""
        return [
            {"path": "/subtitleweb/browse", "endpoint": self.api_browse, "methods": ["GET", "POST"], "auth": "bear", "summary": "浏览目录"},
            {"path": "/subtitleweb/search", "endpoint": self.api_search, "methods": ["GET", "POST"], "auth": "bear", "summary": "搜索目录"},
            {"path": "/subtitleweb/recommend_name", "endpoint": self.api_recommend_name, "methods": ["GET", "POST"], "auth": "bear", "summary": "推荐字幕命名"},
            {"path": "/subtitleweb/upload", "endpoint": self.api_upload, "methods": ["POST"], "auth": "bear", "summary": "旧版上传字幕"},
            {"path": "/subtitleweb/delete", "endpoint": self.api_delete, "methods": ["POST"], "auth": "bear", "summary": "旧版删除字幕"},
            {"path": "/subtitleweb/session", "endpoint": self.api_session, "methods": ["GET", "POST"], "auth": "bear", "summary": "旧版会话管理"},
        ]

    def _get_data_path(self) -> str:
        """返回旧版会话目录。"""
        return os.path.join(self.get_data_path(), "sessions")

    def _get_session_key(self, user_id: str) -> str:
        """生成旧版会话键。"""
        return f"subtitleweb.session.{user_id}"

    def _load_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """加载旧版目录浏览会话。"""
        key = self._get_session_key(user_id)
        data = self.get_data(key)
        if not data:
            return None
        if time.time() - data.get("last_active", 0) > self._session_timeout:
            self.del_data(key)
            return None
        return data

    def _save_session(self, user_id: str, current_path: str) -> None:
        """保存旧版目录浏览会话。"""
        self.save_data(self._get_session_key(user_id), {"current_path": current_path, "last_active": time.time(), "user_id": user_id})

    def _check_permission(self, user_id: str) -> bool:
        """检查旧版 API 用户权限。"""
        if not self._allowed_users:
            return True
        return str(user_id) in self._allowed_users

    def _is_safe_path(self, target: str) -> bool:
        """检查目标路径是否在旧版根目录内。"""
        if not self._root_path:
            return False
        root = os.path.abspath(self._root_path)
        target_abs = os.path.abspath(target)
        return target_abs.startswith(root)

    def _list_directory(self, path: str) -> List[Dict[str, Any]]:
        """列出旧版目录内容。"""
        try:
            entries = []
            for entry in sorted(os.listdir(path)):
                full = os.path.join(path, entry)
                is_dir = os.path.isdir(full)
                entries.append({"name": entry, "is_dir": is_dir, "size": os.path.getsize(full) if not is_dir else 0, "mtime": os.path.getmtime(full)})
            return entries
        except Exception as exc:
            logger.error("列目录失败: %s - %s", path, exc)
            return []

    def _extract_subtitle(self, archive_path: str, extract_dir: str) -> Optional[str]:
        """从 zip 中提取第一个字幕文件。"""
        try:
            if archive_path.lower().endswith(".zip"):
                with zipfile.ZipFile(archive_path) as zf:
                    for name in zf.namelist():
                        if name.lower().endswith((".ass", ".srt", ".ssa", ".vtt")):
                            zf.extract(name, extract_dir)
                            return os.path.join(extract_dir, name)
        except Exception as exc:
            logger.error("解压失败: %s - %s", archive_path, exc)
        return None

    def api_browse(self, body: dict = None) -> Dict[str, Any]:
        """旧版目录浏览。"""
        body = body or {}
        user_id = str(body.get("user_id", ""))
        if not self._check_permission(user_id):
            return {"code": 403, "msg": "无权限"}
        base = self._root_path
        if not base or not os.path.isdir(base):
            return {"code": 500, "msg": "根目录未配置或不存在"}
        session = self._load_session(user_id)
        current = session["current_path"] if session else base
        action = body.get("action", "enter")
        target = body.get("path", "")
        if action == "up":
            parent = os.path.dirname(current)
            current = parent if self._is_safe_path(parent) and parent != base else base
        elif action == "enter" and target:
            new_path = os.path.join(current, target) if not os.path.isabs(target) else target
            if self._is_safe_path(new_path) and os.path.isdir(new_path):
                current = new_path
        self._save_session(user_id, current)
        return {"code": 0, "msg": "success", "data": {"current_path": os.path.relpath(current, base), "absolute_path": current, "entries": self._list_directory(current), "can_go_up": current != base}}

    def api_search(self, body: dict = None) -> Dict[str, Any]:
        """旧版目录搜索。"""
        body = body or {}
        user_id = str(body.get("user_id", ""))
        if not self._check_permission(user_id):
            return {"code": 403, "msg": "无权限"}
        session = self._load_session(user_id)
        if not session:
            return {"code": 400, "msg": "会话不存在"}
        keyword = str(body.get("keyword", "")).lower()
        results = []
        for root, _, files in os.walk(session["current_path"]):
            for filename in files:
                if keyword in filename.lower() and filename.lower().endswith((".ass", ".srt", ".ssa", ".vtt", ".mkv", ".mp4")):
                    results.append({"name": filename, "path": os.path.relpath(os.path.join(root, filename), session["current_path"])})
        return {"code": 0, "msg": "success", "data": {"results": results[:50]}}

    def api_recommend_name(self, body: dict = None) -> Dict[str, Any]:
        """旧版推荐字幕命名。"""
        body = body or {}
        user_id = str(body.get("user_id", ""))
        if not self._check_permission(user_id):
            return {"code": 403, "msg": "无权限"}
        session = self._load_session(user_id)
        if not session:
            return {"code": 400, "msg": "会话不存在"}
        video_names = [os.path.splitext(f)[0] for f in os.listdir(session["current_path"]) if os.path.splitext(f)[1].lower() in self._supported_video_exts]
        if not video_names:
            return {"code": 404, "msg": "当前目录未找到视频文件"}
        all_recommends = {name: [f"{name}.chs.ass", f"{name}.cht.ass", f"{name}.chs.srt", f"{name}.cht.srt"] for name in video_names}
        return {"code": 0, "msg": "success", "data": {"recommends": all_recommends[video_names[0]], "all_recommends": all_recommends, "video_files": video_names, "base_name": video_names[0]}}

    def api_upload(self, body: dict = None) -> Dict[str, Any]:
        """旧版字幕上传。"""
        body = body or {}
        user_id = str(body.get("user_id", ""))
        if not self._check_permission(user_id):
            return {"code": 403, "msg": "无权限"}
        session = self._load_session(user_id)
        if not session:
            return {"code": 400, "msg": "会话不存在"}
        filename = str(body.get("filename", ""))
        content_b64 = str(body.get("content", ""))
        target_name = str(body.get("target_name") or filename)
        overwrite = bool(body.get("overwrite", False))
        if not filename.lower().endswith((".ass", ".srt", ".ssa", ".vtt", ".zip")):
            return {"code": 400, "msg": "仅支持字幕或 zip 格式"}
        target_path = os.path.join(session["current_path"], target_name)
        if not self._is_safe_path(target_path):
            return {"code": 403, "msg": "路径越权"}
        if os.path.exists(target_path) and not overwrite:
            return {"code": 409, "msg": "文件已存在", "data": {"exists": True}}
        try:
            tmp_dir = os.path.join(self.get_data_path(), "tmp")
            os.makedirs(tmp_dir, exist_ok=True)
            tmp_file = os.path.join(tmp_dir, f"{int(time.time())}_{filename}")
            with open(tmp_file, "wb") as file_obj:
                file_obj.write(base64.b64decode(content_b64))
            final_file = self._extract_subtitle(tmp_file, tmp_dir) if filename.lower().endswith(".zip") else tmp_file
            if not final_file:
                return {"code": 400, "msg": "压缩包内未找到字幕文件"}
            shutil.move(final_file, target_path)
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            self._log_operation(user_id, "upload", target_path)
            return {"code": 0, "msg": "上传成功", "data": {"path": target_path}}
        except Exception as exc:
            logger.error("上传失败: %s", exc)
            return {"code": 500, "msg": f"上传失败: {exc}"}

    def api_delete(self, body: dict = None) -> Dict[str, Any]:
        """旧版删除字幕。"""
        body = body or {}
        user_id = str(body.get("user_id", ""))
        if not self._check_permission(user_id):
            return {"code": 403, "msg": "无权限"}
        session = self._load_session(user_id)
        if not session:
            return {"code": 400, "msg": "会话不存在"}
        target = str(body.get("path", ""))
        full_path = os.path.join(session["current_path"], target) if not os.path.isabs(target) else target
        if not self._is_safe_path(full_path):
            return {"code": 403, "msg": "路径越权"}
        if not os.path.isfile(full_path):
            return {"code": 404, "msg": "文件不存在"}
        try:
            os.remove(full_path)
            self._log_operation(user_id, "delete", full_path)
            return {"code": 0, "msg": "删除成功"}
        except Exception as exc:
            return {"code": 500, "msg": f"删除失败: {exc}"}

    def api_session(self, body: dict = None) -> Dict[str, Any]:
        """旧版会话管理。"""
        body = body or {}
        user_id = str(body.get("user_id", ""))
        if not self._check_permission(user_id):
            return {"code": 403, "msg": "无权限"}
        if body.get("action", "status") == "extend":
            session = self._load_session(user_id)
            if session:
                self._save_session(user_id, session["current_path"])
                return {"code": 0, "msg": "会话已延长"}
            return {"code": 404, "msg": "会话不存在"}
        session = self._load_session(user_id)
        return {"code": 0, "msg": "success", "data": session} if session else {"code": 404, "msg": "会话不存在"}

    def _log_operation(self, user_id: str, action: str, path: str) -> None:
        """记录旧版操作日志。"""
        log_key = f"subtitleweb.log.{user_id}"
        logs = self.get_data(log_key) or []
        logs.append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "action": action, "path": os.path.relpath(path, self._root_path) if self._root_path else path})
        self.save_data(log_key, logs[-50:])
