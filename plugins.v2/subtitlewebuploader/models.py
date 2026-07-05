"""字幕网页上传器的数据模型与响应工具。"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SubtitleWebSession:
    """字幕网页操作台用户会话。"""

    user_id: str
    selected_target_ids: List[str] = field(default_factory=list)
    selected_media: Dict[str, Any] = field(default_factory=dict)
    last_active: float = field(default_factory=time.time)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]], user_id: str) -> "SubtitleWebSession":
        """从字典恢复网页操作台会话。"""
        payload = data or {}
        target_ids = payload.get("selected_target_ids") or payload.get("target_ids") or []
        if not isinstance(target_ids, list):
            target_ids = []
        media = payload.get("selected_media") or {}
        if not isinstance(media, dict):
            media = {}
        return cls(
            user_id=str(payload.get("user_id") or user_id or "default"),
            selected_target_ids=[str(item) for item in target_ids if str(item or "").strip()],
            selected_media=media,
            last_active=float(payload.get("last_active") or time.time()),
        )

    def to_dict(self) -> Dict[str, Any]:
        """将会话转换为可持久化字典。"""
        return {
            "user_id": self.user_id,
            "selected_target_ids": list(self.selected_target_ids),
            "selected_media": dict(self.selected_media),
            "last_active": self.last_active,
        }


def ok(data: Any = None, msg: str = "success") -> Dict[str, Any]:
    """构造兼容前端的成功响应。"""
    return {"code": 0, "msg": msg, "data": data if data is not None else {}}


def fail(msg: str, code: int = 1, data: Any = None) -> Dict[str, Any]:
    """构造兼容前端的失败响应。"""
    return {"code": code, "msg": msg, "data": data if data is not None else {}}
