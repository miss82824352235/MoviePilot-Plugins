"""字幕网页操作台 API。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException, Request
from starlette.datastructures import UploadFile

from app.log import logger

from .bridge import SubtitleManualBridge
from .models import fail, ok


class SubtitleWebApi:
    """字幕网页操作台 API 处理器。"""

    def __init__(self, owner: Any):
        """初始化 API 处理器。"""
        self.owner = owner
        self.bridge = SubtitleManualBridge(owner)

    async def status(self) -> Dict[str, Any]:
        """查询网页上传器与字幕匹配桥接状态。"""
        data = self.bridge.status()
        if data.get("code") != 0:
            return data
        data["data"].update(
            {
                "enabled": bool(getattr(self.owner, "_enabled", False)),
                "web_console": True,
                "tg_entry": True,
                "extra_auth": False,
            }
        )
        return data

    async def search(self, request: Request) -> Dict[str, Any]:
        """搜索本地媒体资源候选。"""
        params = dict(request.query_params)
        return await self.bridge.search(params)

    async def targets(self, request: Request) -> Dict[str, Any]:
        """读取媒体目标文件。"""
        params = dict(request.query_params)
        return await self.bridge.targets(params)

    async def history(self, request: Request) -> Dict[str, Any]:
        """读取字幕匹配历史。"""
        params = dict(request.query_params)
        return await self.bridge.history(params)

    async def save_selection(self, request: Request) -> Dict[str, Any]:
        """保存网页/TG 多选目标会话。"""
        body = await request.json()
        user_id = str(body.get("user_id") or body.get("userid") or "web")
        target_ids = body.get("target_ids") or []
        if not isinstance(target_ids, list):
            raise HTTPException(status_code=400, detail="target_ids 必须是数组")
        media = body.get("media") or body.get("selected_media") or {}
        session = self.owner._load_web_session(user_id)
        session.selected_target_ids = [str(item) for item in target_ids if str(item or "").strip()]
        session.selected_media = media if isinstance(media, dict) else {}
        self.owner._save_web_session(session)
        return ok(session.to_dict(), "已保存选择")

    async def get_selection(self, request: Request) -> Dict[str, Any]:
        """读取网页/TG 多选目标会话。"""
        user_id = str(request.query_params.get("user_id") or request.query_params.get("userid") or "web")
        session = self.owner._load_web_session(user_id)
        return ok(session.to_dict())

    async def upload_prepare(self, request: Request) -> Dict[str, Any]:
        """接收字幕文件并生成匹配预览。"""
        form = await request.form()
        raw_target_ids = form.get("target_ids") or ""
        if raw_target_ids:
            try:
                target_ids = json.loads(str(raw_target_ids))
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"target_ids 格式错误: {exc}") from exc
        else:
            user_id = str(form.get("user_id") or "web")
            target_ids = self.owner._load_web_session(user_id).selected_target_ids
        if not isinstance(target_ids, list) or not target_ids:
            raise HTTPException(status_code=400, detail="请先选择目标视频")
        files: List[UploadFile] = [item for item in form.getlist("files") if isinstance(item, UploadFile)]
        if not files:
            raise HTTPException(status_code=400, detail="请上传字幕文件、ZIP、RAR 或 7Z")
        return await self.bridge.prepare_upload([str(item) for item in target_ids], files)

    async def upload_apply(self, request: Request) -> Dict[str, Any]:
        """确认写入上传字幕。"""
        body = await request.json()
        if not body.get("confirm"):
            return fail("写入字幕需要 confirm=true", 409, {"need_confirm": True})
        body.setdefault("fix_timeline", True)
        body.setdefault("allow_risky_offset", False)
        return await self.bridge.apply_upload(body)

    async def delete_preview(self, request: Request) -> Dict[str, Any]:
        """删除字幕预检。"""
        body = await request.json()
        items = body.get("items") or []
        if not items and body.get("target_id"):
            items = [{"target_id": body.get("target_id"), "subtitle_path": body.get("subtitle_path"), "subtitle_name": body.get("subtitle_name")}]
        return ok({"items": items, "count": len(items), "need_confirm": True}, f"将删除 {len(items)} 条外挂字幕")

    async def delete_apply(self, request: Request) -> Dict[str, Any]:
        """确认删除单个或批量外挂字幕。"""
        body = await request.json()
        if not body.get("confirm"):
            return fail("删除字幕需要 confirm=true", 409, {"need_confirm": True})
        items = body.get("items") or []
        if not items and body.get("target_id"):
            items = [body]
        if not items:
            raise HTTPException(status_code=400, detail="请指定要删除的字幕")
        results = []
        failed = []
        for item in items:
            try:
                result = await self.bridge.delete_subtitle(item)
                deleted = ((result.get("data") or {}).get("deleted") or {}) if isinstance(result, dict) else {}
                path = deleted.get("path") if isinstance(deleted, dict) else ""
                if path:
                    deleted["exists_after_delete"] = Path(path).exists()
                    deleted["verified_deleted"] = not deleted["exists_after_delete"]
                results.append(result)
            except Exception as exc:
                failed.append({"item": item, "reason": str(exc)})
        return ok({"deleted": results, "failed": failed}, f"删除完成：成功 {len(results)}，失败 {len(failed)}")

    async def clear_preview(self, request: Request) -> Dict[str, Any]:
        """清空目标外挂字幕预检。"""
        body = await request.json()
        target_ids = body.get("target_ids") or []
        if not target_ids:
            raise HTTPException(status_code=400, detail="请先选择目标视频")
        return ok({"target_ids": target_ids, "count": len(target_ids), "need_confirm": True}, f"将清空 {len(target_ids)} 个目标的外挂字幕")

    async def clear_apply(self, request: Request) -> Dict[str, Any]:
        """确认清空目标外挂字幕。"""
        body = await request.json()
        if not body.get("confirm"):
            return fail("清空外挂字幕需要 confirm=true", 409, {"need_confirm": True})
        result = await self.bridge.clear_subtitles(body)
        data = result.get("data") if isinstance(result, dict) else None
        if isinstance(data, dict):
            for item in data.get("deleted") or []:
                path = item.get("path") if isinstance(item, dict) else ""
                if path:
                    item["exists_after_delete"] = Path(path).exists()
                    item["verified_deleted"] = not item["exists_after_delete"]
        return result

    async def ai_preview(self, request: Request) -> Dict[str, Any]:
        """AI 字幕任务提交预检。"""
        body = await request.json()
        target_ids = body.get("target_ids") or []
        if not target_ids:
            raise HTTPException(status_code=400, detail="请先选择目标视频")
        source_policy = str(body.get("source_policy") or "auto").strip() or "auto"
        overwrite_policy = str(body.get("overwrite_policy") or ("skip" if source_policy == "auto" else "new_variant")).strip()
        source_subtitle_path = str(body.get("source_subtitle_path") or body.get("subtitle_path") or "").strip()
        tasks = await self.bridge.task_status({"target_ids": target_ids, "limit": 100})
        return ok(
            {
                "target_ids": target_ids,
                "source_policy": source_policy,
                "overwrite_policy": overwrite_policy,
                "source_subtitle_path": source_subtitle_path,
                "task_status": tasks,
                "need_confirm": True,
            },
            f"将提交 {len(target_ids)} 个目标的 AI 字幕任务（源={source_policy}，覆盖={overwrite_policy}）",
        )

    async def ai_submit(self, request: Request) -> Dict[str, Any]:
        """确认提交 AI 字幕任务，透传 source_policy / overwrite_policy / source_subtitle_path。"""
        body = await request.json()
        if not body.get("confirm"):
            return fail("提交 AI 字幕任务需要 confirm=true", 409, {"need_confirm": True})
        # 默认策略与字幕匹配本体一致
        source_policy = str(body.get("source_policy") or "auto").strip() or "auto"
        if source_policy == "reuse":
            source_policy = "auto"
        body["source_policy"] = source_policy
        if not body.get("overwrite_policy"):
            body["overwrite_policy"] = "new_variant" if source_policy != "auto" else "skip"
        if body.get("subtitle_path") and not body.get("source_subtitle_path"):
            body["source_subtitle_path"] = body.get("subtitle_path")
        return await self.bridge.ai_submit(body)

    async def ai_cancel(self, request: Request) -> Dict[str, Any]:
        """取消 AI 字幕任务。"""
        body = await request.json()
        if not body.get("confirm"):
            return fail("取消 AI 字幕任务需要 confirm=true", 409, {"need_confirm": True})
        return await self.bridge.ai_cancel(body)

    async def ai_restart(self, request: Request) -> Dict[str, Any]:
        """重新生成 AI 字幕任务（需 confirm）。"""
        body = await request.json()
        if not body.get("confirm"):
            return fail("重新生成 AI 字幕任务需要 confirm=true", 409, {"need_confirm": True})
        body.setdefault("source_policy", "reuse")
        body.setdefault("overwrite_policy", "backup_replace")
        if body.get("subtitle_path") and not body.get("source_subtitle_path"):
            body["source_subtitle_path"] = body.get("subtitle_path")
        return await self.bridge.ai_restart(body)

    async def online_ai_submit(self, request: Request) -> Dict[str, Any]:
        """在线字幕 → AI 翻译（需 confirm）。"""
        body = await request.json()
        if not body.get("confirm"):
            return fail("在线字幕 AI 翻译需要 confirm=true", 409, {"need_confirm": True})
        target_ids = body.get("target_ids") or []
        results = body.get("results") or body.get("selected_results") or []
        if not target_ids:
            raise HTTPException(status_code=400, detail="请先选择目标视频")
        if not results:
            raise HTTPException(status_code=400, detail="请至少选择一个在线字幕结果")
        body["results"] = results
        return await self.bridge.online_ai_submit(body)

    async def restore(self, request: Request) -> Dict[str, Any]:
        """恢复字幕备份（需 confirm）。支持单条或 items 批量。"""
        body = await request.json()
        if not body.get("confirm"):
            return fail("恢复字幕备份需要 confirm=true", 409, {"need_confirm": True})
        items = body.get("items") or []
        if not items and body.get("target_id"):
            items = [body]
        if not items:
            raise HTTPException(status_code=400, detail="请指定要恢复的字幕备份")
        results = []
        failed = []
        for item in items:
            try:
                payload = {
                    "target_id": item.get("target_id"),
                    "subtitle_path": item.get("subtitle_path") or item.get("path"),
                    "subtitle_name": item.get("subtitle_name") or item.get("name"),
                    "locked_target_ids": body.get("locked_target_ids") or item.get("locked_target_ids") or [],
                }
                results.append(await self.bridge.restore_subtitle_backup(payload))
            except Exception as exc:
                failed.append({"item": item, "reason": str(exc)})
        return ok(
            {"restored": results, "failed": failed},
            f"恢复完成：成功 {len(results)}，失败 {len(failed)}",
        )

    async def tasks(self, request: Request) -> Dict[str, Any]:
        """查询字幕相关任务状态（含 progress 透传）。"""
        body = await request.json()
        return await self.bridge.task_status(body)

    async def timeline_fix(self, request: Request) -> Dict[str, Any]:
        """提交历史外挂字幕调轴任务。"""
        body = await request.json()
        if not body.get("confirm"):
            return fail("字幕调轴需要 confirm=true", 409, {"need_confirm": True})
        return await self.bridge.timeline_fix(body)

    async def online_search(self, request: Request) -> Dict[str, Any]:
        """搜索在线字幕。"""
        body = await request.json()
        return await self.bridge.online_search(body)

    async def online_download_preview(self, request: Request) -> Dict[str, Any]:
        """下载在线字幕并生成预览。"""
        body = await request.json()
        return await self.bridge.online_download_preview(body)
