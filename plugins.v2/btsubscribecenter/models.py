"""BT订阅中心数据模型与轻量工具。"""

import datetime
import re
from typing import Any, Dict, List, Optional


def now_str() -> str:
    """返回当前时间字符串。"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def to_int(value: Any, default: int) -> int:
    """把配置值安全转换为整数。"""
    try:
        return int(value)
    except Exception:
        return default


def parse_group(title: str) -> str:
    """从标题开头解析发布组。"""
    match = re.match(r"^\s*[\[【]([^\]】]{1,40})[\]】]", title or "")
    if match:
        return match.group(1).strip()
    return ""


def sub_id(tmdbid: Optional[int], mtype: str, season: int, title: str = "") -> str:
    """生成插件私有订阅 ID。"""
    key = tmdbid or re.sub(r"\W+", "", title or "unknown").lower()
    return f"{mtype}:{key}:S{int(season or 1):02d}"


def season_text(season: Any) -> str:
    """格式化季号。"""
    try:
        return f"S{int(season or 1):02d}"
    except Exception:
        return "S01"


def episodes_from_meta(meta: Any) -> List[int]:
    """从 MetaInfo 中提取集数列表。"""
    eps = getattr(meta, "episode_list", None) or []
    result = []
    for ep in eps:
        try:
            result.append(int(ep))
        except Exception:
            continue
    return sorted(set(result))


def new_subscription(
        sub_id_value: str,
        title: str,
        year: str,
        mtype: str,
        tmdbid: Optional[int],
        season: int,
        mode: str,
        group: str = "",
        poster: str = "",
        backdrop: str = "",
        overview: str = "",
        total_episode: int = 0,
) -> Dict[str, Any]:
    """创建插件私有订阅结构。"""
    now = now_str()
    return {
        "id": sub_id_value,
        "title": title,
        "year": year,
        "type": mtype,
        "tmdbid": tmdbid,
        "season": season,
        "mode": mode,
        "state": "active",
        "preferred_group": group or "",
        "allowed_groups": [],
        "poster": poster or "",
        "backdrop": backdrop or "",
        "overview": overview or "",
        "total_episode": total_episode or 0,
        "downloaded": {},
        "pending": {},
        "created_at": now,
        "updated_at": now,
    }



def completed_count(subscription: Dict[str, Any]) -> int:
    """计算私有订阅已完成集数。"""
    downloaded = subscription.get("downloaded") or {}
    if isinstance(downloaded, dict):
        return len(downloaded)
    if isinstance(downloaded, list):
        return len(downloaded)
    return 0


def total_count(subscription: Dict[str, Any]) -> int:
    """计算私有订阅总集数。"""
    try:
        total = int(subscription.get("total_episode") or 0)
    except Exception:
        total = 0
    downloaded = completed_count(subscription)
    pending = len(subscription.get("pending") or {})
    return max(total, downloaded + pending)


def lack_count(subscription: Dict[str, Any]) -> int:
    """计算私有订阅缺集数。"""
    total = total_count(subscription)
    if not total:
        return 0
    return max(total - completed_count(subscription), 0)


def progress_percent(subscription: Dict[str, Any]) -> int:
    """计算私有订阅完成百分比。"""
    total = total_count(subscription)
    if not total:
        return 0
    return min(100, int(completed_count(subscription) * 100 / total))
