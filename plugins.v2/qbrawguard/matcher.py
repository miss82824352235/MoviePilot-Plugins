"""
QBRawGuard 原盘判定模块。

职责：
1. 只根据下载器返回的真实文件列表判定是否为原盘或光盘镜像结构。
2. 不读取插件配置以外的运行时状态，不暂停下载器，不删除文件，不发送通知。
3. 返回命中证据列表，供主流程记录、清理和通知使用。
"""

import re
from typing import Iterable, List, Pattern

from app.log import logger


def compile_patterns(patterns: str) -> List[Pattern[str]]:
    """编译原盘判定正则列表，忽略空行和注释行。"""
    regs: List[Pattern[str]] = []
    for line in (patterns or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            regs.append(re.compile(line))
        except re.error as err:
            logger.warning(f"原盘通知 正则无效：{line}，{err}")
    return regs


def match_raw_disc(file_names: Iterable[str], regex: Iterable[Pattern[str]], limit: int = 3) -> List[str]:
    """基于真实文件路径列表匹配原盘结构，并返回最多 limit 条命中证据。"""
    matched: List[str] = []
    for raw_name in file_names or []:
        name = str(raw_name or "").replace("\\", "/")
        if not name:
            continue
        if any(rule.search(name) for rule in regex):
            matched.append(name)
            if len(matched) >= limit:
                break
    return matched
