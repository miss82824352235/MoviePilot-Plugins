import json
import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request

from ..core.models import OverwritePolicy, SourcePolicy, TaskSource, TriggerType
from ..translate.openai_translate import OpenAi

try:
    from app.core.config import settings
except Exception:
    settings = None

try:
    from app.agent.llm import LLMHelper, LLMProviderManager, LLMTestTimeout
except Exception:
    LLMHelper = None
    LLMProviderManager = None
    LLMTestTimeout = TimeoutError


class AutoSubTaskApi:
    def __init__(self, plugin: Any):
        self._plugin = plugin

    def routes(self) -> List[Dict[str, Any]]:
        routes = [
            {
                "path": "/status",
                "endpoint": self.api_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取 AI 字幕生成联动状态",
            },
            {
                "path": "/submit",
                "endpoint": self.api_submit,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "提交 AI 字幕生成任务",
            },
            {
                "path": "/tasks",
                "endpoint": self.api_tasks,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取 AI 字幕生成任务状态",
            },
            {
                "path": "/cancel",
                "endpoint": self.api_cancel,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "取消 AI 字幕生成任务",
            },
            {
                "path": "/delete",
                "endpoint": self.api_delete,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "删除 AI 字幕任务记录",
            },
            {
                "path": "/restart",
                "endpoint": self.api_restart,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "重新生成 AI 字幕任务",
            },
            {
                "path": "/runtime_update/status",
                "endpoint": self.api_runtime_update_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取 Whisper 运行库更新器状态",
            },
            {
                "path": "/runtime_update/check",
                "endpoint": self.api_runtime_update_check,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "请求宿主机检查 Whisper 运行库更新",
            },
            {
                "path": "/llm_providers",
                "endpoint": self.api_llm_providers,
                "methods": ["GET", "POST"],
                "auth": "bear",
                "summary": "获取 LLM Provider 目录",
            },
            {
                "path": "/llm_models",
                "endpoint": self.api_llm_models,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "使用插件独立 LLM 配置获取模型列表",
            },
            {
                "path": "/llm_model_metadata",
                "endpoint": self.api_llm_model_metadata,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "获取 LLM 模型元数据",
            },
            {
                "path": "/llm_test",
                "endpoint": self.api_llm_test,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "测试插件独立 LLM 配置",
            },
            {
                "path": "/models",
                "endpoint": self.api_llm_models,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "兼容旧前端：使用插件独立 LLM 配置获取模型列表",
            },
            {
                "path": "/test_model",
                "endpoint": self.api_llm_test,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "兼容旧前端：测试插件独立 LLM 配置",
            },
        ]
        if os.environ.get("AUTOSUBV3_TEST_ROUTES") == "1":
            routes.append({
                "path": "/_debug_llm_runtime",
                "endpoint": self.api_debug_llm_runtime,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "调试：解析插件独立 LLM 运行参数",
            })
        return routes

    def api_status(self) -> Dict[str, Any]:
        return self._plugin._ok(self._plugin._status_payload())

    def api_runtime_update_status(self) -> Dict[str, Any]:
        """返回宿主机运行库更新器状态。"""
        return self._plugin._ok(self._plugin._get_runtime_updater().get_status())

    async def api_runtime_update_check(self, request: Request) -> Dict[str, Any]:
        """请求宿主机更新器检查更新，不在插件进程中运行系统命令。"""
        return self._plugin._ok(self._plugin._get_runtime_updater().request_check())

    async def api_debug_llm_runtime(self, request: Request) -> Dict[str, Any]:
        """调试解析后的 LLM 运行参数，默认不注册。"""
        body = await request.json()
        runtime = self._resolve_llm_runtime(body)
        if runtime.get("api_key"):
            runtime["api_key"] = "***"
        return self._plugin._ok(runtime, message="已解析 LLM 运行参数")

    async def api_submit(self, request: Request) -> Dict[str, Any]:
        if not self._plugin._running or not self._plugin._task_queue:
            raise HTTPException(status_code=409, detail=self._plugin._status_payload()["message"])
        body = await request.json()
        paths = body.get("paths") or []
        if isinstance(paths, str):
            paths = [paths]
        if not isinstance(paths, list):
            paths = []
        subtitle_overrides = body.get("subtitle_overrides") if isinstance(body.get("subtitle_overrides"), dict) else None
        result = self._plugin.submit_tasks(
            paths,
            source=self._plugin._normalize_text(body.get("source")) or TaskSource.MANUAL.value,
            subtitle_overrides=subtitle_overrides,
            trigger=self._plugin._normalize_text(body.get("trigger")) or TriggerType.MANUAL.value,
            source_policy=self._plugin._normalize_text(body.get("source_policy")) or SourcePolicy.AUTO.value,
            overwrite_policy=self._plugin._normalize_text(body.get("overwrite_policy")) or OverwritePolicy.SKIP.value,
        )
        return self._plugin._ok(
            result,
            message=f"已提交 {len(result['added'])} 个 AI 字幕生成任务，跳过 {len(result['skipped'])} 个，失败 {len(result['failed'])} 个",
        )

    async def api_cancel(self, request: Request) -> Dict[str, Any]:
        body = await request.json()
        paths = body.get("paths") or []
        task_ids = body.get("task_ids") or []
        if isinstance(paths, str):
            paths = [paths]
        if isinstance(task_ids, str):
            task_ids = [task_ids]
        result = self._plugin.cancel_tasks(task_ids=task_ids if isinstance(task_ids, list) else [], paths=paths if isinstance(paths, list) else [])
        return self._plugin._ok(
            result,
            message=f"已取消 {len(result.get('cancelled') or [])} 个 AI 字幕任务，跳过 {len(result.get('skipped') or [])} 个",
        )

    async def api_delete(self, request: Request) -> Dict[str, Any]:
        body = await request.json()
        paths = body.get("paths") or []
        task_ids = body.get("task_ids") or []
        if isinstance(paths, str):
            paths = [paths]
        if isinstance(task_ids, str):
            task_ids = [task_ids]
        result = self._plugin.delete_tasks(task_ids=task_ids if isinstance(task_ids, list) else [], paths=paths if isinstance(paths, list) else [])
        return self._plugin._ok(
            result,
            message=f"已删除 {len(result.get('deleted') or [])} 个 AI 字幕任务，跳过 {len(result.get('skipped') or [])} 个",
        )

    async def api_restart(self, request: Request) -> Dict[str, Any]:
        if not self._plugin._running or not self._plugin._task_queue:
            raise HTTPException(status_code=409, detail=self._plugin._status_payload()["message"])
        body = await request.json()
        task_ids = body.get("task_ids") or []
        if isinstance(task_ids, str):
            task_ids = [task_ids]
        result = self._plugin.restart_tasks(
            task_ids=task_ids if isinstance(task_ids, list) else [],
            source_policy=self._plugin._normalize_text(body.get("source_policy")) or SourcePolicy.REUSE.value,
            overwrite_policy=self._plugin._normalize_text(body.get("overwrite_policy")) or OverwritePolicy.BACKUP_REPLACE.value,
        )
        return self._plugin._ok(
            result,
            message=f"已重新提交 {len(result.get('added') or [])} 个 AI 字幕任务，跳过 {len(result.get('skipped') or [])} 个，失败 {len(result.get('failed') or [])} 个",
        )

    async def api_llm_providers(self, request: Request = None) -> Dict[str, Any]:
        """返回 MoviePilot Provider 目录，但不读取 MP 当前 LLM 配置值。"""
        if LLMProviderManager is None:
            raise HTTPException(status_code=500, detail="当前 MoviePilot 版本未提供 LLMProviderManager")
        try:
            providers = await LLMProviderManager().list_providers_async()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"获取 Provider 目录失败：{exc}")
        return self._plugin._ok({"providers": providers, "items": providers}, message=f"已获取 {len(providers or [])} 个 Provider")

    async def api_llm_models(self, request: Request) -> Dict[str, Any]:
        """使用 AutoSubv3 独立字段获取模型列表，禁止从 settings.LLM_* 补值。"""
        body = await request.json()
        try:
            model_items = await self._list_models_with_plugin_config(body)
        except HTTPException:
            raise
        except Exception as exc:
            api_key = self._normalize_api_key(body)
            raise HTTPException(status_code=502, detail=f"获取模型列表失败：{self._sanitize_llm_error(str(exc), api_key)}")
        return self._plugin._ok(
            {
                "models": model_items,
                "items": model_items,
                "count": len(model_items),
                "source": "plugin_independent_llm_helper",
            },
            message=f"已获取 {len(model_items)} 个模型",
        )

    async def api_llm_model_metadata(self, request: Request) -> Dict[str, Any]:
        """解析模型 metadata 和上下文能力，仅使用插件传入字段。"""
        if LLMProviderManager is None:
            raise HTTPException(status_code=500, detail="当前 MoviePilot 版本未提供 LLMProviderManager")
        body = await request.json()
        provider = self._normalize_provider(body)
        model = self._normalize_model(body)
        if not model:
            raise HTTPException(status_code=400, detail="请先填写或选择模型")
        base_url = self._normalize_base_url(body)
        base_url_preset = self._normalize_base_url_preset(body)
        use_proxy = self._parse_bool(body.get("llm_use_proxy", body.get("use_proxy", body.get("openai_proxy", False))))
        try:
            metadata = await LLMProviderManager().resolve_model_metadata(
                provider_id=provider,
                model_id=model,
                base_url=base_url,
                base_url_preset_id=base_url_preset,
                use_proxy=use_proxy,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"获取模型 metadata 失败：{exc}")
        normalized = self._normalize_metadata(model, metadata)
        return self._plugin._ok(normalized, message="已获取模型 metadata")

    async def api_llm_test(self, request: Request) -> Dict[str, Any]:
        """测试 AutoSubv3 独立 LLM 配置，禁止读取 MP 当前 LLM 配置。"""
        if LLMHelper is None:
            raise HTTPException(status_code=500, detail="当前 MoviePilot 版本未提供 LLMHelper")
        body = await request.json()
        runtime = self._resolve_llm_runtime(body)
        provider = runtime["provider"]
        model = runtime["model"]
        api_key = runtime["api_key"]
        if not model:
            raise HTTPException(status_code=400, detail="请先填写或选择模型")
        if provider not in {"chatgpt", "github-copilot"} and not api_key:
            raise HTTPException(status_code=400, detail="请先填写插件独立 LLM API Key")
        try:
            result = await LLMHelper.test_current_settings(
                provider=provider,
                model=model,
                api_key=api_key,
                base_url=runtime["base_url"],
                base_url_preset=runtime["base_url_preset"],
                user_agent=runtime["user_agent"],
                use_proxy=runtime["use_proxy"],
                temperature=0,
            )
            return self._plugin._ok(result, message=f"模型 {model} 可用")
        except (LLMTestTimeout, TimeoutError):
            raise HTTPException(status_code=504, detail="LLM 调用超时")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"模型测试失败：{self._sanitize_llm_error(str(exc), api_key)}")

    async def _list_models_with_plugin_config(self, body: Dict[str, Any]) -> List[Dict[str, str]]:
        """使用 MoviePilot LLMHelper 技术机制，但参数只来自插件独立配置。"""
        if LLMHelper is None:
            raise RuntimeError("当前 MoviePilot 版本未提供 LLMHelper")
        runtime = self._resolve_llm_runtime(body)
        provider = runtime["provider"]
        api_key = runtime["api_key"]
        if provider not in {"chatgpt", "github-copilot"} and not api_key:
            raise HTTPException(status_code=400, detail="请先填写插件独立 LLM API Key")
        records = await LLMHelper().get_models(
            provider=provider,
            api_key=api_key,
            base_url=runtime["base_url"],
            base_url_preset=runtime["base_url_preset"],
            user_agent=runtime["user_agent"],
            use_proxy=runtime["use_proxy"],
            force_refresh=bool(body.get("force_refresh", False)),
        )
        items: List[Dict[str, str]] = []
        seen = set()
        for record in records or []:
            if not isinstance(record, dict):
                continue
            value = str(record.get("id") or record.get("value") or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            title = str(record.get("name") or record.get("title") or value).strip()
            items.append({"title": title, "value": value, "id": value, "name": title})
        return items

    def _normalize_provider(self, body: Dict[str, Any]) -> str:
        """解析插件独立 provider 字段。"""
        return self._plugin._normalize_text(body.get("llm_provider") or body.get("provider") or "openai")

    def _normalize_api_key(self, body: Dict[str, Any]) -> str:
        """解析插件独立 API Key 字段。"""
        return self._plugin._normalize_text(body.get("llm_api_key") or body.get("api_key") or body.get("openai_key"))

    def _normalize_model(self, body: Dict[str, Any]) -> str:
        """解析插件独立模型字段，兼容前端 Combobox 回传对象。"""
        raw = body.get("llm_model") or body.get("model") or body.get("openai_model")
        if isinstance(raw, dict):
            raw = raw.get("value") or raw.get("id") or raw.get("model") or raw.get("title") or raw.get("name")
        return self._plugin._normalize_text(raw)

    def _normalize_base_url(self, body: Dict[str, Any]) -> str:
        """解析插件独立 Base URL 字段。"""
        return self._resolve_llm_runtime(body).get("base_url") or ""

    def _normalize_base_url_preset(self, body: Dict[str, Any]) -> str:
        """解析插件独立 Base URL 预设字段。"""
        return self._plugin._normalize_text(body.get("llm_base_url_preset") or body.get("base_url_preset"))

    def _normalize_user_agent(self, body: Dict[str, Any]) -> str:
        """解析插件独立 User-Agent 字段。"""
        return self._plugin._normalize_text(body.get("llm_user_agent") or body.get("user_agent"))

    @staticmethod
    def _parse_bool(value: Any) -> bool:
        """更严格地解析布尔值，避免字符串 false 被当成真值。"""
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off", ""}:
            return False
        return bool(value)

    def _resolve_llm_runtime(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """统一解析 AutoSubv3 独立 LLM 运行参数，供测试、拉模型、metadata 和翻译共用。"""
        base_url = self._plugin._normalize_text(body.get("llm_base_url") or body.get("base_url") or body.get("openai_url"))
        if base_url and not body.get("llm_base_url") and not body.get("base_url") and not body.get("compatible", True):
            base_url = base_url.rstrip("/") + "/v1"
        helper_base_url = base_url.rstrip("/") if base_url else ""
        translator_api_url = helper_base_url
        translator_compatible = True
        if translator_api_url.endswith("/v1"):
            translator_api_url = translator_api_url[:-3].rstrip("/")
            translator_compatible = False
        return {
            "provider": self._normalize_provider(body),
            "model": self._normalize_model(body),
            "api_key": self._normalize_api_key(body),
            "base_url": helper_base_url,
            "helper_base_url": helper_base_url,
            "translator_api_url": translator_api_url,
            "translator_compatible": translator_compatible,
            "base_url_preset": self._normalize_base_url_preset(body),
            "user_agent": self._normalize_user_agent(body),
            "use_proxy": self._parse_bool(body.get("llm_use_proxy", body.get("use_proxy", body.get("openai_proxy", False)))),
        }

    @staticmethod
    def _sanitize_llm_error(message: str, api_key: Optional[str] = None) -> str:
        """清理 LLM 错误中的敏感信息，并把常见 HTTP 跳转错误转换为可读提示。"""
        text = str(message or "")
        if api_key:
            text = text.replace(api_key, "***")
        text = text.replace("Authorization", "认证信息")
        lowered = text.lower()
        if "302" in text or "found" in lowered:
            return "服务端返回 302 跳转，请检查 AutoSubv3 独立 Base URL 是否填写为 API 入口而不是网页入口，必要时改用带 /v1 的 OpenAI 兼容地址。"
        if "<!doctype html" in lowered or "<html" in lowered:
            return "服务端返回了网页 HTML，而不是模型 API JSON 响应；请检查 AutoSubv3 独立 Base URL 是否为正确的 OpenAI 兼容 API 地址，通常应以 /v1 结尾。"
        return text

    @staticmethod
    def _metadata_get(metadata: Any, *names: str) -> Any:
        """兼容对象和字典读取 metadata 字段。"""
        for name in names:
            if isinstance(metadata, dict) and metadata.get(name) is not None:
                return metadata.get(name)
            value = getattr(metadata, name, None)
            if value is not None:
                return value
        return None

    def _normalize_metadata(self, model_id: str, metadata: Any) -> Dict[str, Any]:
        """把 MP metadata 转换为前端易用结构，同时保留 raw。"""
        context_length = self._metadata_get(metadata, "context_length", "context", "max_input_tokens", "input_tokens")
        output_tokens = self._metadata_get(metadata, "max_output_tokens", "output_tokens", "max_tokens")
        name = self._metadata_get(metadata, "name", "title", "display_name") or model_id
        raw = metadata
        if hasattr(metadata, "model_dump"):
            try:
                raw = metadata.model_dump()
            except Exception:
                raw = str(metadata)
        elif not isinstance(metadata, (dict, list, str, int, float, bool, type(None))):
            raw = getattr(metadata, "__dict__", str(metadata))
        return {
            "model_id": model_id,
            "id": model_id,
            "name": name,
            "context_length": context_length,
            "input_token_limit": context_length,
            "max_output_tokens": output_tokens,
            "output_token_limit": output_tokens,
            "raw": raw,
        }

    def api_tasks(self, request: Request) -> Dict[str, Any]:
        raw_paths = request.query_params.get("paths") or ""
        filter_paths = set()
        if raw_paths:
            try:
                parsed = json.loads(raw_paths)
                if isinstance(parsed, list):
                    filter_paths = {self._plugin._normalize_text(item) for item in parsed if self._plugin._normalize_text(item)}
            except Exception:
                filter_paths = {self._plugin._normalize_text(item) for item in raw_paths.split(",") if self._plugin._normalize_text(item)}
        try:
            limit = int(request.query_params.get("limit") or 300)
        except Exception:
            limit = 300
        limit = min(max(limit, 1), 1000)
        return self._plugin._ok(self._plugin.tasks_payload(paths=list(filter_paths), limit=limit))
