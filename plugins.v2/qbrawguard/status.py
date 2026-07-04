"""
QBRawGuard 运行状态检查模块。

职责：
1. 构建插件首页/设置页使用的健康检查数据。
2. 只做只读状态探测，不修改配置、不操作下载器任务、不删除文件。
3. 将通知通道、下载器、识别规则、历史拦截等检查从插件入口拆出，方便 AI 定位状态问题。
"""

import time
from typing import Any, Callable, Dict, List

STATUS_TEXT_CLASS = {
    "success": "text-success",
    "warning": "text-warning",
    "error": "text-error",
    "info": "text-info",
    "default": "text-medium-emphasis",
}

STATUS_COLOR_PROP = {
    "success": "success",
    "warning": "warning",
    "error": "error",
    "info": "info",
    "default": "grey",
}


def build_check_status(plugin: Any, services_getter: Callable[[], Dict[str, Any]], notification_type_getter: Callable[[], Any]) -> List[dict]:
    """构建 QBRawGuard 健康检查项，并在插件实例上复用 30 秒缓存。"""
    now = time.time()
    cache = getattr(plugin, "_status_cache", {"ts": 0, "checks": None})
    if cache.get("checks") and (now - cache["ts"]) < 30:
        return cache["checks"]

    checks: List[dict] = []
    on = bool(getattr(plugin, "enabled", False))
    fast = bool(getattr(plugin, "fast_scan_enabled", False))
    full = bool(getattr(plugin, "full_scan_enabled", False))

    def push(icon, label, ok, text_on, text_off="已关闭", warn=None):
        if warn is not None:
            status = "warning"
            text = warn
        elif ok:
            status, text = "success", text_on
        else:
            status, text = "default", text_off
        checks.append({"icon": icon, "label": label, "status": status, "text": text})

    push("mdi-power-plug", "插件状态", on, "已启用", "已停用")
    push("mdi-lightning-bolt", "快速拦截", on and fast, f"每 {getattr(plugin, 'interval', 1)} 分钟")
    full_interval = getattr(plugin, "full_interval", 0)
    full_min = full_interval if full_interval > 0 else getattr(plugin, "interval", 1) * 5
    push("mdi-shield-check", "全量兜底", on and full, f"每 {full_min} 分钟")

    try:
        svcs = services_getter()
        if svcs:
            push("mdi-download", "QB下载器", True, "、".join(svcs.keys()) + " 已连接")
        else:
            push("mdi-download-off", "QB下载器", False, "", "未配置")
            checks[-1]["status"] = "error"
            checks[-1]["text"] = "无可用 Qbittorrent"
    except Exception as err:
        checks.append({"icon": "mdi-download-off", "label": "QB下载器", "status": "error", "text": str(err)})

    try:
        from app.helper.service import ServiceConfigHelper
        switches = ServiceConfigHelper.get_notification_switches() or []
        configs = ServiceConfigHelper.get_notification_configs() or []
        expected_type = notification_type_getter().value
        switch = next((s for s in switches if s.type == expected_type and s.action and s.action != "none"), None)
        enabled_configs = [c for c in configs if c.enabled and expected_type in (c.switchs or [])]
        if switch:
            action_label = {"all": "全部", "user": "仅用户", "admin": "仅管理"}.get(switch.action, switch.action)
            ch_names = "、".join([c.name for c in enabled_configs]) if enabled_configs else "通知渠道"
            push("mdi-bell-ring", "通知通道", True, f"「{expected_type}」→ {action_label}（{ch_names}）")
        elif enabled_configs:
            ch_names = "、".join([c.name for c in enabled_configs])
            push("mdi-bell-ring", "通知通道", True, f"「{expected_type}」→ 已配置（{ch_names}）")
        elif not switches and not configs:
            checks.append({"icon": "mdi-bell-off", "label": "通知通道", "status": "error", "text": "未配置通知场景与通知渠道"})
        else:
            available = [s.type for s in switches if s.action and s.action != "none"]
            if not available:
                available = [c.name for c in configs if c.enabled]
            checks.append({"icon": "mdi-bell-off", "label": "通知通道", "status": "warning", "text": f"「{expected_type}」未开启（可用: {', '.join(available[:5])}）"})
    except Exception as err:
        checks.append({"icon": "mdi-bell-off", "label": "通知通道", "status": "error", "text": str(err)})

    push("mdi-flash", "事件拦截", on, "监听 DownloadAdded", "跟随插件")
    valid = sum(1 for rule in getattr(plugin, "regex", []) if rule)
    if valid > 0:
        push("mdi-regex", "识别规则", True, f"{valid} 条规则就绪")
    else:
        checks.append({"icon": "mdi-regex", "label": "识别规则", "status": "error", "text": "无有效规则"})

    total_hits = sum(1 for v in (getattr(plugin, "processed", {}) or {}).values() if v.get("matched"))
    if total_hits > 0:
        checks.append({"icon": "mdi-alert-octagon", "label": "历史拦截", "status": "info", "text": f"累计 {total_hits} 次命中"})
    else:
        checks.append({"icon": "mdi-alert-octagon", "label": "历史拦截", "status": "default", "text": "暂未命中"})

    plugin._status_cache = {"ts": now, "checks": checks}
    return checks
