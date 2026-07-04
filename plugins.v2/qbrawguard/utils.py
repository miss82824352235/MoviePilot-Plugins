"""
QBRawGuard 通用工具模块。

职责：
1. 提供字段读取、文本清洗、大小/时间格式化、标题预检、通知图片兜底等纯工具函数。
2. 标题预检只允许用于快速扫描降噪，不能作为原盘命中的最终依据。
3. 不访问下载器，不删除文件，不发送通知，便于 AI 安全复用。
"""

import re
from datetime import datetime
from typing import Any, Iterable


def value_of(obj: Any, *keys: str) -> Any:
    """从 dict、对象属性或 get 方法中按顺序读取第一个非空字段。"""
    for key in keys:
        if isinstance(obj, dict) and key in obj:
            return obj[key]
        if hasattr(obj, key):
            return getattr(obj, key)
        try:
            val = obj.get(key)
            if val is not None:
                return val
        except Exception:
            pass
    return None


def clean_line(value: Any, limit: int = 240) -> str:
    """清理单行文本，避免通知和日志中出现换行污染。"""
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)[:limit]


def format_size(value: Any) -> str:
    """将字节大小格式化为 MoviePilot 通知可读的短文本。"""
    try:
        size = float(value or 0)
        if size <= 0:
            return ""
        for unit in ("B", "K", "M", "G", "T"):
            if size < 1024 or unit == "T":
                return f"{size:.2f}{unit}" if unit != "B" else f"{int(size)}B"
            size /= 1024
    except Exception:
        return str(value or "")
    return ""


def format_time(value: Any) -> str:
    """将时间戳格式化为通知展示时间。"""
    try:
        if value in (None, ""):
            return ""
        value = float(value)
        if value > 0:
            return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value or "")[:19]
    return ""


def site_name(value: Any) -> str:
    """从站点名或 tracker URL 中提取安全展示名。"""
    text = str(value or "").strip()
    if not text:
        return ""
    if "://" in text:
        text = text.split("://", 1)[-1].split("/", 1)[0]
    return text[:80]


def display_title(name: str) -> str:
    """将种子名压缩为适合通知标题展示的名称。"""
    text = str(name or "").strip()
    text = re.sub(r"[._]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text[:80] or "下载任务"


def suspect_name(name: str, hints: Iterable[str]) -> bool:
    """标题预检：只用于快速拦截降噪，最终命中必须来自真实文件列表。"""
    text = str(name or "").lower()
    if not text:
        return False
    return any(str(hint).lower() in text for hint in hints or [])


def notice_image(image: Any) -> str:
    """通知图片兜底，过滤 MoviePilot 当前通知链路不可靠的本地 file 路径。"""
    text = str(image or "").strip()
    if text.startswith("file://") or text.startswith("/"):
        return ""
    return text


def short_name(name: str, limit: int = 60) -> str:
    """返回适合日志展示的短种子名。"""
    return (name[:limit] + "…") if len(name) > limit else name
