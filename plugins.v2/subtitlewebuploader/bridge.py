"""SubtitleManualUpload 桥接层。"""
from __future__ import annotations

import inspect
import json
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlencode

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import FormData, QueryParams, UploadFile

from app.core.plugin import PluginManager
from app.log import logger

from .models import fail, ok


class _JsonRequest:
    """用于调用字幕匹配内部 API 的 JSON Request 适配器。"""

    def __init__(self, body: Dict[str, Any]):
        """初始化 JSON 请求适配器。"""
        self._body = body or {}
        self.query_params = QueryParams("")

    async def json(self) -> Dict[str, Any]:
        """返回请求 JSON 内容。"""
        return self._body


class _QueryRequest:
    """用于调用字幕匹配内部 API 的查询 Request 适配器。"""

    def __init__(self, params: Dict[str, Any]):
        """初始化查询请求适配器。"""
        cleaned = {str(k): "" if v is None else str(v) for k, v in (params or {}).items() if v is not None}
        self.query_params = QueryParams(urlencode(cleaned))

    async def json(self) -> Dict[str, Any]:
        """返回空 JSON 内容。"""
        return {}


class _FormRequest:
    """用于调用字幕匹配上传 API 的表单 Request 适配器。"""

    def __init__(self, target_ids: Iterable[str], files: List[UploadFile]):
        """初始化 multipart 表单请求适配器。"""
        self._target_ids = [str(item) for item in target_ids if str(item or "").strip()]
        self._files = files or []
        self.query_params = QueryParams("")

    async def form(self) -> FormData:
        """返回包含 target_ids 和 files 的表单数据。"""
        items = [("target_ids", json.dumps(self._target_ids, ensure_ascii=False))]
        items.extend(("files", item) for item in self._files)
        return FormData(items)


class SubtitleManualBridge:
    """字幕匹配插件桥接器。"""

    plugin_id = "SubtitleManualUpload"
    plugin_candidates = ("SubtitleManualUploadMobile", "SubtitleManualUpload")

    def __init__(self, owner: Any):
        """初始化桥接器。"""
        self.owner = owner
        self.active_plugin_id = "SubtitleManualUploadMobile"
        self.active_module_base = "app.plugins.subtitlemanualuploadmobile"

    def plugin(self) -> Optional[Any]:
        """获取运行中的字幕匹配插件实例，优先原版，自动回退移动版。"""
        try:
            running = PluginManager().running_plugins or {}
            for plugin_id in self.plugin_candidates:
                plugin = running.get(plugin_id)
                if not plugin:
                    continue
                if hasattr(plugin, "get_state") and not bool(plugin.get_state()):
                    continue
                self.active_plugin_id = plugin_id
                module_name = str(getattr(plugin.__class__, "__module__", ""))
                if module_name.endswith(".__init__"):
                    module_name = module_name.rsplit(".", 1)[0]
                self.active_module_base = module_name or (
                    "app.plugins.subtitlemanualuploadmobile" if plugin_id == "SubtitleManualUploadMobile" else "app.plugins.subtitlemanualupload"
                )
                return plugin
        except Exception as exc:
            logger.warning("[SubtitleWebUploader] 获取字幕匹配插件失败：%s", exc)
        return None

    def _import_api_class(self, module_name: str, class_name: str) -> Any:
        """按当前桥接到的字幕插件动态导入 API 类。"""
        import importlib

        module = importlib.import_module(f"{self.active_module_base}.api.{module_name}")
        return getattr(module, class_name)

    def status(self) -> Dict[str, Any]:
        """查询桥接状态。"""
        plugin = self.plugin()
        if not plugin:
            return fail("字幕匹配插件未运行，请先启用 SubtitleManualUpload 或 SubtitleManualUploadMobile", 503, {"bridge": False, "plugin_candidates": list(self.plugin_candidates)})
        bridge_mode = "移动版" if self.active_plugin_id == "SubtitleManualUploadMobile" else "原版"
        return ok(
            {
                "bridge": True,
                "plugin_id": self.active_plugin_id,
                "plugin_name": getattr(plugin, "plugin_name", "字幕匹配"),
                "plugin_version": getattr(plugin, "plugin_version", ""),
                "plugin_state": bool(plugin.get_state()) if hasattr(plugin, "get_state") else True,
                "bridge_mode": bridge_mode,
                "bridge_target": f"{getattr(plugin, 'plugin_name', '字幕匹配')} {getattr(plugin, 'plugin_version', '')}".strip(),
                "web_plugin_version": getattr(self.owner, "plugin_version", ""),
            }
        )

    def _ensure_plugin(self) -> Any:
        """确保字幕匹配插件可用。"""
        plugin = self.plugin()
        if not plugin:
            raise HTTPException(status_code=503, detail="字幕匹配插件未运行，请先启用 SubtitleManualUpload 或 SubtitleManualUploadMobile")
        return plugin

    async def _call(self, func: Any, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """兼容同步/异步调用字幕匹配内部方法。"""
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return await run_in_threadpool(func, *args, **kwargs)

    async def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """搜索字幕匹配本地媒体候选。"""
        plugin = self._ensure_plugin()
        CatalogApi = self._import_api_class("catalog_api", "CatalogApi")
        return await self._call(CatalogApi(plugin).search, _QueryRequest(params))

    async def targets(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """读取字幕匹配本地目标文件。"""
        plugin = self._ensure_plugin()
        CatalogApi = self._import_api_class("catalog_api", "CatalogApi")
        return await self._call(CatalogApi(plugin).targets, _QueryRequest(params))

    async def history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """读取字幕匹配历史。"""
        plugin = self._ensure_plugin()
        CatalogApi = self._import_api_class("catalog_api", "CatalogApi")
        return await self._call(CatalogApi(plugin).match_history, _QueryRequest(params))

    async def prepare_upload(self, target_ids: List[str], files: List[UploadFile]) -> Dict[str, Any]:
        """调用字幕匹配上传预览。"""
        plugin = self._ensure_plugin()
        UploadApi = self._import_api_class("upload_api", "UploadApi")
        return await self._call(UploadApi(plugin).prepare_upload, _FormRequest(target_ids, files))

    async def apply_upload(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用字幕匹配确认写入。"""
        plugin = self._ensure_plugin()
        UploadApi = self._import_api_class("upload_api", "UploadApi")
        return await self._call(UploadApi(plugin).apply_upload, _JsonRequest(body))

    async def clear_subtitles(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用字幕匹配清空外挂字幕。"""
        plugin = self._ensure_plugin()
        UploadApi = self._import_api_class("upload_api", "UploadApi")
        return await self._call(UploadApi(plugin).clear_subtitles, _JsonRequest(body))

    async def delete_subtitle(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用字幕匹配删除单个外挂字幕。"""
        plugin = self._ensure_plugin()
        UploadApi = self._import_api_class("upload_api", "UploadApi")
        return await self._call(UploadApi(plugin).delete_subtitle, _JsonRequest(body))

    async def ai_submit(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用字幕匹配提交 AI 字幕任务。"""
        plugin = self._ensure_plugin()
        AiApi = self._import_api_class("ai_api", "AiApi")
        return await self._call(AiApi(plugin).ai_submit, _JsonRequest(body))

    async def ai_tasks(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用字幕匹配查询 AI 字幕任务。"""
        plugin = self._ensure_plugin()
        AiApi = self._import_api_class("ai_api", "AiApi")
        return await self._call(AiApi(plugin).ai_tasks, _JsonRequest(body))

    async def ai_cancel(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用字幕匹配取消 AI 字幕任务。"""
        plugin = self._ensure_plugin()
        AiApi = self._import_api_class("ai_api", "AiApi")
        return await self._call(AiApi(plugin).ai_cancel, _JsonRequest(body))

    async def task_status(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """汇总 AI、调轴和自动入库队列任务状态。"""
        plugin = self._ensure_plugin()
        facade = getattr(plugin, "automation", None)
        if facade and hasattr(facade, "task_status"):
            return ok(await run_in_threadpool(facade.task_status, target_ids=body.get("target_ids"), limit=int(body.get("limit") or 100)))
        return await self.ai_tasks(body)

    async def timeline_fix(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用字幕匹配历史外挂字幕调轴。"""
        plugin = self._ensure_plugin()
        TimelineApi = self._import_api_class("timeline_api", "TimelineApi")
        return await self._call(TimelineApi(plugin).timeline_fix_existing, _JsonRequest(body))

    async def online_search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用字幕匹配在线字幕搜索。"""
        plugin = self._ensure_plugin()
        OnlineApi = self._import_api_class("online_api", "OnlineApi")
        return await self._call(OnlineApi(plugin).online_search, _JsonRequest(body))

    async def online_download_preview(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """调用字幕匹配在线字幕下载预览。"""
        plugin = self._ensure_plugin()
        OnlineApi = self._import_api_class("online_api", "OnlineApi")
        return await self._call(OnlineApi(plugin).online_download_preview, _JsonRequest(body))
