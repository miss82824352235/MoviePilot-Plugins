"""BT订阅中心 Vuetify JSON 页面。"""

from typing import Any, Dict, List

from .models import season_text


def col(component: dict, md: int = 6) -> dict:
    """构造表单列。"""
    return {"component": "VCol", "props": {"cols": 12, "md": md}, "content": [component]}


def metric_card(title: str, value: Any, color: str) -> dict:
    """构造统计卡片。"""
    return {
        "component": "VCol",
        "props": {"cols": 6, "md": 3},
        "content": [{
            "component": "VCard",
            "props": {"variant": "tonal", "color": color, "rounded": "lg", "class": "h-100"},
            "content": [
                {"component": "VCardText", "props": {"class": "text-caption pb-1"}, "text": title},
                {"component": "VCardTitle", "props": {"class": "text-h5 pt-0"}, "text": str(value)},
            ],
        }],
    }


def form_schema(defaults: Dict[str, Any]) -> List[dict]:
    """返回配置表单 JSON。"""
    return [{"component": "VForm", "content": [
        {"component": "VAlert", "props": {"type": "info", "variant": "tonal", "text": "BT订阅中心只从配置的 RSS/BT 源消费资源，不写入 MP 原生订阅。自动下载默认关闭，先看候选效果。"}},
        {"component": "VRow", "content": [
            col({"component": "VSwitch", "props": {"model": "enabled", "label": "启用插件"}}, 4),
            col({"component": "VSwitch", "props": {"model": "onlyonce", "label": "立即刷新一次"}}, 4),
            col({"component": "VSwitch", "props": {"model": "auto_download", "label": "自动下载候选（谨慎）"}}, 4),
        ]},
        {"component": "VRow", "content": [
            col({"component": "VCronField", "props": {"model": "cron", "label": "刷新周期", "placeholder": "*/30 * * * *"}}, 6),
            col({"component": "VTextField", "props": {"model": "save_path", "label": "保存目录", "placeholder": "留空使用 MP 默认下载目录"}}, 6),
        ]},
        {"component": "VTextarea", "props": {"model": "rss_urls", "label": "RSS 地址", "rows": 4, "placeholder": "每行一个 RSS 地址"}},
        {"component": "VRow", "content": [
            col({"component": "VTextField", "props": {"model": "include", "label": "包含规则", "placeholder": "正则，可留空"}}, 6),
            col({"component": "VTextField", "props": {"model": "exclude", "label": "排除规则", "placeholder": "正则，可留空"}}, 6),
        ]},
        {"component": "VRow", "content": [
            col({"component": "VTextField", "props": {"model": "size_range", "label": "种子大小(GB)", "placeholder": "如 0.2-10"}}, 4),
            col({"component": "VTextField", "props": {"model": "airing_window_days", "label": "新番窗口天数"}}, 4),
            col({"component": "VTextField", "props": {"model": "early_episode_max", "label": "新番早期集上限"}}, 4),
        ]},
        {"component": "VRow", "content": [
            col({"component": "VSwitch", "props": {"model": "auto_discover_airing", "label": "自动发现新番"}}, 4),
            col({"component": "VSwitch", "props": {"model": "prefer_same_group", "label": "优先同一发布组"}}, 4),
            col({"component": "VSwitch", "props": {"model": "proxy", "label": "RSS 使用代理"}}, 4),
        ]},
        {"component": "VRow", "content": [
            col({"component": "VTextField", "props": {"model": "group_wait_minutes", "label": "偏好组等待分钟"}}, 4),
            col({"component": "VTextField", "props": {"model": "candidate_limit", "label": "候选保留数量"}}, 4),
            col({"component": "VTextField", "props": {"model": "history_limit", "label": "历史保留数量"}}, 4),
        ]},
    ]}]


def page_schema(enabled: bool, auto_download: bool, stats: Dict[str, int], subs: Dict[str, dict], candidates: List[dict]) -> List[dict]:
    """返回详情页 JSON。"""
    return [
        {"component": "VAlert", "props": {"type": "success" if enabled else "warning", "variant": "tonal", "class": "mb-3", "text": f"私有订阅 {stats['subscriptions']} 个，候选 {stats['candidates']} 条，等待 {stats['pending']} 条，已下载 {stats['downloaded']} 集。自动下载：{'开启' if auto_download else '关闭'}。"}},
        {"component": "VRow", "content": [
            metric_card("私有订阅", stats["subscriptions"], "primary"),
            metric_card("候选资源", stats["candidates"], "info"),
            metric_card("等待候选", stats["pending"], "warning"),
            metric_card("已下载", stats["downloaded"], "success"),
        ]},
        {"component": "div", "props": {"class": "text-subtitle-1 font-weight-bold my-3"}, "text": "私有订阅"},
        {"component": "VRow", "content": [_subscription_card(sub) for sub in list(subs.values())[:60]] or [_empty_card("暂无私有订阅。刷新 RSS 后可自动发现新番。")]},
        {"component": "div", "props": {"class": "text-subtitle-1 font-weight-bold my-3"}, "text": "最近候选 / 识别状态"},
        {"component": "VCard", "props": {"variant": "tonal", "rounded": "lg"}, "content": [{"component": "VCardText", "text": _format_candidates(candidates[:40])}]},
    ]


def _empty_card(text: str) -> dict:
    """构造空状态卡片。"""
    return {"component": "VCol", "props": {"cols": 12}, "content": [{"component": "VAlert", "props": {"type": "info", "variant": "tonal", "text": text}}]}


def _subscription_card(sub: Dict[str, Any]) -> dict:
    """构造接近 MP 订阅卡片风格的私有订阅卡。"""
    downloaded = len(sub.get("downloaded") or {})
    pending = len(sub.get("pending") or {})
    total = int(sub.get("total_episode") or 0)
    progress = f"{downloaded} / {total or '?'}"
    percent = 0 if not total else min(100, int(downloaded * 100 / total))
    title = f"{sub.get('title') or '-'} {season_text(sub.get('season'))}"
    # 历史订阅在 v0.1.1 前可能没有图片字段，这里兼容旧数据。
    poster = sub.get("poster") or _tmdb_image(sub.get("tmdbid"), "poster")
    backdrop = sub.get("backdrop") or _tmdb_image(sub.get("tmdbid"), "backdrop") or poster
    state = sub.get("state") or "active"
    group = sub.get("preferred_group") or "BT订阅中心"
    bg_style = "min-height: 150px; overflow: hidden; position: relative;"
    if backdrop:
        bg_style += f" background-image: linear-gradient(90deg, rgba(12,18,30,.92), rgba(12,18,30,.62)), url('{backdrop}'); background-size: cover; background-position: center;"
    return {
        "component": "VCol",
        "props": {"cols": 12, "sm": 6, "md": 4, "lg": 3},
        "content": [{
            "component": "VCard",
            "props": {"rounded": "lg", "elevation": 2, "class": "h-100", "style": bg_style},
            "content": [
                {"component": "VCardText", "props": {"class": "pa-3"}, "content": [
                    {"component": "div", "props": {"class": "d-flex align-start"}, "content": [
                        {"component": "VImg", "props": {"src": poster, "width": 58, "height": 82, "cover": True, "class": "rounded me-3", "style": "background: rgba(255,255,255,.08);"}} if poster else {"component": "div", "props": {"class": "rounded me-3 d-flex align-center justify-center", "style": "width:58px;height:82px;background:rgba(255,255,255,.12);"}, "text": "BT"},
                        {"component": "div", "props": {"class": "flex-grow-1"}, "content": [
                            {"component": "div", "props": {"class": "text-caption text-medium-emphasis"}, "text": str(sub.get("year") or "")},
                            {"component": "div", "props": {"class": "text-subtitle-1 font-weight-bold text-white", "style": "line-height:1.25;min-height:40px;"}, "text": title},
                            {"component": "div", "props": {"class": "text-caption mt-2"}, "text": f"{progress}  ·  {group}"},
                        ]},
                        {"component": "VChip", "props": {"size": "x-small", "color": "success" if state == "active" else "warning", "variant": "tonal"}, "text": "运行" if state == "active" else "暂停"},
                    ]},
                    {"component": "VProgressLinear", "props": {"model-value": percent, "color": "success", "height": 4, "class": "mt-3 rounded"}},
                    {"component": "div", "props": {"class": "d-flex justify-space-between text-caption mt-2 text-medium-emphasis"}, "content": [
                        {"component": "span", "text": f"{sub.get('mode') or 'airing'}"},
                        {"component": "span", "text": f"待定 {pending}"},
                    ]},
                ]}
            ],
        }],
    }


def _format_candidates(candidates: List[dict]) -> str:
    """格式化候选列表。"""
    if not candidates:
        return "暂无候选。"
    lines = []
    for item in candidates:
        ep = ",".join(map(str, item.get("episodes") or [])) or "-"
        lines.append(f"[{item.get('status')}] {item.get('title')}｜组:{item.get('group') or '-'}｜E:{ep}｜{item.get('reason') or ''}")
    return "\n".join(lines)


def _tmdb_image(tmdbid: Any, image_type: str) -> str:
    """根据 TMDB ID 构造兜底图片地址。"""
    if not tmdbid:
        return ""
    if image_type == "poster":
        return f"/api/v1/media/tmdb/image/tv/{tmdbid}/poster"
    return f"/api/v1/media/tmdb/image/tv/{tmdbid}/backdrop"
