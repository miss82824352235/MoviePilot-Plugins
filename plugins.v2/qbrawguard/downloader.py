"""
QBRawGuard 下载器文件列表模块。

职责：
1. 只负责从下载器任务读取真实文件列表，并做必要的字段兼容和短轮询等待。
2. 原盘/Emby 不友好格式判定必须交给 matcher.py，不能在这里根据种子名做简单命中。
3. 当刚添加种子或磁力时文件列表可能尚未就绪，本模块提供重试能力，避免把空列表误判为安全任务。
"""

import time
from typing import Any, List


def _value_of(obj: Any, *keys: str) -> Any:
    """从 dict、对象属性或 get 方法中读取字段。"""
    for key in keys:
        if isinstance(obj, dict) and key in obj:
            return obj[key]
        if hasattr(obj, key):
            return getattr(obj, key)
        try:
            value = obj.get(key)
            if value is not None:
                return value
        except Exception:
            pass
    return None


def normalize_file_name(file_item: Any) -> str:
    """将下载器返回的文件项规范化为相对路径字符串。"""
    if isinstance(file_item, str):
        text = file_item
    else:
        text = _value_of(file_item, "name", "path", "filepath", "file_path") or ""
    return str(text or "").replace("\\", "/").strip()


def get_file_names(service: Any, torrent_hash: str) -> List[str]:
    """读取下载器真实文件列表，返回规范化后的文件路径列表。"""
    files = service.instance.get_files(torrent_hash) or []
    return [name for name in (normalize_file_name(item) for item in files) if name]


def get_file_names_with_retry(service: Any, torrent_hash: str, attempts: int = 5, delay: float = 1.5) -> List[str]:
    """短轮询等待下载器文件列表就绪，适合 DownloadAdded 事件刚触发的场景。"""
    last: List[str] = []
    for index in range(max(int(attempts), 1)):
        last = get_file_names(service, torrent_hash)
        if last:
            return last
        if index < attempts - 1 and delay > 0:
            time.sleep(delay)
    return last
