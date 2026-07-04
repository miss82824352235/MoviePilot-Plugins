"""
QBRawGuard 数据结构模块。

职责：
1. 集中定义跨模块传递的数据结构，减少隐式 dict 字段和字符串猜测。
2. 不包含 MoviePilot 运行时依赖，便于 AI 快速理解字段含义。
3. 后续拆分下载器、清理、通知时优先复用这里的数据模型。
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TorrentFile:
    """下载器返回的单个种子文件。"""

    path: str
    size: int = 0


@dataclass
class RawDiscMatch:
    """原盘结构判定结果。"""

    matched: bool = False
    format_name: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class CleanupResult:
    """命中原盘后的清理结果摘要。"""

    deleted_items: int = 0
    errors: List[str] = field(default_factory=list)
