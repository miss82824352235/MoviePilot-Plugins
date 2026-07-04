"""
QBRawGuard Vuetify JSON UI 模块。

职责：
1. 构建插件详情页和配置表单，减少入口文件中的大段 Vuetify JSON。
2. 只读取插件实例的状态和配置，不执行原盘判定、下载器操作或清理动作。
3. 操作按钮仍调用插件 API，后续如 MoviePilot 提供更原生的插件前端 API 注入能力，可在本模块集中替换。
"""

from typing import Any, Dict, List, Tuple


def build_page(plugin: Any) -> List[dict]:
    """构建插件详情首页。"""
    checks = plugin._check_status()
    icon = plugin.plugin_icon or ""
    return [
        {"component": "VCard", "props": {
            "variant": "flat", "elevation": "0", "rounded": "xl", "class": "mb-4 pa-4",
            "style": glass_card_style(blur=18, opacity=0.5),
        }, "content": [
            {"component": "VRow", "props": {"align": "center", "no-gutters": True}, "content": [
                {"component": "VAvatar", "props": {"color": "primary", "variant": "tonal", "rounded": "lg", "size": 44},
                 "content": [
                    {"component": "VImg", "props": {"src": icon, "width": 28, "height": 28}}
                ]},
                {"component": "VCol", "props": {"class": "ml-3"}, "content": [
                    {"component": "div", "props": {"class": "text-h6 font-weight-bold"},
                     "text": f"原盘通知 v{plugin.plugin_version}"},
                    {"component": "div", "props": {"class": "text-body-2 text-medium-emphasis"},
                     "text": "BDMV / ISO / DVD 原盘拦截 · 事件驱动 + 定时扫描 + 延迟回扫"},
                ]},
                {"component": "VSpacer"},
                {"component": "VChip", "props": {
                    "color": "success" if plugin.enabled else "grey", "variant": "flat", "size": "small",
                    "prepend-icon": "mdi-play-circle" if plugin.enabled else "mdi-pause-circle",
                    "text": "运行中" if plugin.enabled else "已停用"
                }},
            ]},
        ]},
        stats_row(plugin),
        {"component": "div", "props": {"class": "text-subtitle-2 font-weight-medium mb-2 mt-4"},
         "text": "系统健康检查"},
        health_row(plugin, checks),
        {"component": "VRow", "props": {"class": "mt-3"}, "content": [
            {"component": "VCol", "props": {"cols": 12, "md": 6}, "content": [
                action_button("发送模拟拦截测试通知", "mdi-send", "warning", "test_notify")
            ]},
            {"component": "VCol", "props": {"cols": 12, "md": 6}, "content": [
                action_button(f"手动回扫孤儿入库（队列 {len(plugin._rescan_queue)}）",
                              "mdi-broom", "error", "manual_rescan")
            ]},
        ]},
        {"component": "VAlert", "props": {
            "type": "info", "variant": "tonal", "density": "compact", "class": "mt-3",
            "text": "点击右上角「设置」进入完整配置：拦截参数、通知通道、测试字段、识别规则。",
        }},
    ]


def build_form(plugin: Any) -> Tuple[List[dict], Dict[str, Any]]:
    """构建插件配置表单和默认配置。"""
    try:
        opts = [{"title": c.name, "value": c.name} for c in plugin.downloader_helper.get_configs().values()
                if "qb" in f"{getattr(c, 'type', '')}{c.name}".lower()]
    except Exception:
        opts = []
    form = [{"component": "VForm", "content": [*form_tabs(plugin, opts)]}]
    defaults = {
        "enabled": False, "fast_scan_enabled": True, "full_scan_enabled": False,
        "downloaders": [], "interval": 2, "full_interval": 0,
        "action": "stop", "notify": True, "notify_type": "Agent", "tag": "原盘拦截",
        "include_completed": True, "retry_failed": True,
        "alert_image": "https://cdn-icons-png.flaticon.com/512/564/564619.png",
        "test_message": "站点：馒头\n质量：UHD HDR10 DoVi 2160p\n大小：92.61G\n种子：Avatar Fire and Ash 2025 2160p UHD Blu-ray DoVi HDR10 HEVC TrueHD 7.1-Thor@HDSky\n发布时间：2026-06-02 06:03:02\n做种数：111\n促销：50%\nHit&Run：否\n标签：中字 4k 中配 hdr10 DoVi\n描述：阿凡达：火与烬 / 阿凡达3 / 阿凡达3：带种者 / 阿凡达3：火与灰 / 阿凡达3：火与烬 【UHD原盘 DIY国语DTS配音 官译简繁粤/双语字幕】",
        "test_title": "阿凡达：火与烬 (2025)",
        "test_subtitle": "Avatar Fire and Ash 2025 2160p UHD Blu-ray DoVi HDR10 HEVC TrueHD 7.1-Thor@HDSky",
        "test_site": "馒头", "test_seeders": "111",
        "test_tags": "中字 4k 中配 hdr10 DoVi",
        "test_format": "光盘镜像文件",
        "patterns": plugin.DEFAULT_PATTERNS,
    }
    return form, defaults


def form_tabs(plugin: Any, downloader_opts: list) -> List[dict]:
    """构建配置页 Tab 容器。"""
    titles = ["基本设置", "通知与测试", "高级规则"]
    icons = ["mdi-tune", "mdi-bell-ring", "mdi-regex"]
    windows = [tab_basic(downloader_opts), tab_notify(), tab_advanced()]
    tab_items = [{"component": "VTab", "props": {"value": i, "prepend-icon": icons[i]}, "text": t}
                 for i, t in enumerate(titles)]
    win_items = [{"component": "VWindowItem", "props": {"value": i}, "content": w}
                 for i, w in enumerate(windows)]
    return [
        {"component": "VTabs", "props": {"model": "_tab", "grow": True}, "content": tab_items},
        {"component": "VWindow", "props": {"model": "_tab", "style": "padding-top: 16px"}, "content": win_items},
    ]


def tab_basic(downloader_opts: list) -> list:
    """构建基本设置 Tab。"""
    return [
        field_row(
            switch("enabled", "启用插件"),
            switch("fast_scan_enabled", "快速拦截", "标题预检→文件匹配，低开销优先命中"),
            switch("full_scan_enabled", "全量兜底", "低频补漏，事件驱动已覆盖所有新任务"),
        ),
        field_row(
            number("interval", "快速间隔（分钟）", min_val=1),
            number("full_interval", "全量间隔（分钟）", min_val=5, hint="留空=自动（快速×5）"),
            select("action", "命中动作", [
                {"title": "停止下载", "value": "stop"},
                {"title": "删除并联动清理", "value": "delete"},
            ], hint="删除会联动清理文件/入库/记录"),
            switch("include_completed", "检查已完成", "避免间隔期内任务漏检"),
        ),
        field_row(
            {"component": "VCol", "props": {"cols": 12, "md": 6}, "content": [
                {"component": "VSelect", "props": {
                    "multiple": True, "chips": True, "model": "downloaders",
                    "label": "QB 下载器", "items": downloader_opts,
                    "hint": "留空 = 全部 QB 下载器", "persistent-hint": True,
                }}
            ]},
            text("tag", "命中标签"),
            switch("retry_failed", "失败重试"),
        ),
    ]


def tab_notify() -> list:
    """构建通知与测试 Tab。"""
    return [
        {"component": "VCard", "props": {"variant": "tonal", "elevation": "0", "rounded": "lg", "class": "mb-4 pa-4"}, "content": [
            {"component": "div", "props": {"class": "text-subtitle-2 font-weight-medium mb-3"}, "text": "通知配置"},
            field_row(
                switch("notify", "发送通知"),
                select("notify_type", "通知场景", [
                    {"title": "智能体", "value": "Agent"},
                    {"title": "插件", "value": "Plugin"},
                    {"title": "资源下载", "value": "Download"},
                    {"title": "整理入库", "value": "Organize"},
                    {"title": "其它", "value": "Other"},
                ], hint="复用 MP 通知通道发送"),
                text("alert_image", "报警图地址", hint="留空自动恢复默认图标"),
            ),
        ]},
        {"component": "VCard", "props": {"variant": "tonal", "elevation": "0", "rounded": "lg", "class": "mb-4 pa-4"}, "content": [
            {"component": "div", "props": {"class": "text-subtitle-2 font-weight-medium mb-3"}, "text": "模拟通知字段"},
            field_row(text("test_title", "测试标题", md=6), text("test_subtitle", "测试种子名/副标题", md=6)),
            field_row(text("test_site", "测试站点"), text("test_seeders", "测试做种数"), text("test_tags", "测试标签")),
            field_row({"component": "VCol", "props": {"cols": 12}, "content": [
                {"component": "VTextField", "props": {"model": "test_format", "label": "判定格式", "hint": "只写格式依据，不暴露路径/hash", "persistent-hint": True}}
            ]}),
            field_row({"component": "VCol", "props": {"cols": 12}, "content": [
                {"component": "VTextarea", "props": {"model": "test_message", "label": "下载通知字段（多行）", "rows": 4, "hint": "按 MP 下载通知格式逐行填写", "persistent-hint": True}}
            ]}),
        ]},
    ]


def tab_advanced() -> list:
    """构建高级规则 Tab。"""
    return [
        {"component": "VAlert", "props": {"type": "warning", "variant": "tonal", "density": "compact", "class": "mb-3", "text": "一般不需修改。规则过宽可能误杀正常任务，建议先用默认规则在小范围验证后再调整。"}},
        {"component": "VRow", "content": [{"component": "VCol", "props": {"cols": 12}, "content": [
            {"component": "VTextarea", "props": {"model": "patterns", "label": "原盘识别正则（每行一条）", "rows": 8, "hint": "以 # 开头的行为注释；留空自动恢复内置默认规则", "persistent-hint": True}}
        ]}]},
    ]


def field_row(*cols: dict) -> dict:
    """多个 VCol 包入一个 VRow。"""
    return {"component": "VRow", "content": list(cols)}


def switch(key: str, label: str, hint: str = "") -> dict:
    """构建开关字段。"""
    return col(4, "VSwitch", {"model": key, "label": label, "hint": hint, "persistent-hint": bool(hint)})


def text(key: str, label: str, hint: str = "", md: int = 4) -> dict:
    """构建文本字段。"""
    return col(md, "VTextField", {"model": key, "label": label, "hint": hint, "persistent-hint": bool(hint)})


def number(key: str, label: str, min_val: int = 1, hint: str = "", md: int = 4) -> dict:
    """构建数字字段。"""
    return col(md, "VTextField", {"model": key, "label": label, "type": "number", "min": min_val, "hint": hint, "persistent-hint": bool(hint)})


def select(key: str, label: str, items: list, hint: str = "", md: int = 4) -> dict:
    """构建选择字段。"""
    return col(md, "VSelect", {"model": key, "label": label, "items": items, "hint": hint, "persistent-hint": bool(hint)})


def col(cols: int, component: str, props: dict) -> dict:
    """构建栅格列。"""
    return {"component": "VCol", "props": {"cols": 12, "md": cols}, "content": [{"component": component, "props": props}]}


def stats_row(plugin: Any) -> dict:
    """构建顶部统计卡片行。"""
    hits = sum(1 for v in (plugin.processed or {}).values() if v.get("matched"))
    stats = [
        ("mdi-alert-octagon", "累计拦截", f"{hits} 次", "error"),
        ("mdi-shield-search", "幸存缓存", f"{len(plugin._survivors)} 个", "info"),
        ("mdi-timer-sand", "回扫队列", f"{len(plugin._rescan_queue)} 个", "warning" if plugin._rescan_queue else "success"),
        ("mdi-database-check", "处理记录", f"{len(plugin.processed or {})} 条", "primary"),
    ]
    return {"component": "VRow", "content": [
        {"component": "VCol", "props": {"cols": 6, "md": 3}, "content": [metric_card(icon, label, value, color)]}
        for icon, label, value, color in stats
    ]}


def health_row(plugin: Any, checks: List[dict]) -> dict:
    """构建健康检查卡片行。"""
    return {"component": "VRow", "content": [
        {"component": "VCol", "props": {"cols": 6, "md": 3}, "content": [status_card(plugin, item)]}
        for item in checks
    ]}


def action_button(button_text: str, icon: str, color: str, endpoint: str, method: str = "post") -> dict:
    """构建操作按钮。"""
    return {"component": "VBtn", "props": {
        "color": color, "variant": "tonal", "rounded": "lg", "block": True,
        "prepend-icon": icon, "class": "text-none",
    }, "text": button_text, "events": {
        "click": {"api": f"plugin/QBRawGuard/{endpoint}", "method": method}
    }}


def metric_card(icon: str, label: str, value: str, color: str = "primary") -> dict:
    """构建统计指标卡片。"""
    return {"component": "VCard", "props": {"variant": "tonal", "elevation": "0", "rounded": "lg", "style": "backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);"}, "content": [
        {"component": "VCardText", "props": {"class": "d-flex align-center pa-3"}, "content": [
            {"component": "VAvatar", "props": {"color": color, "variant": "tonal", "rounded": "lg", "size": 44, "class": "me-3"}, "content": [
                {"component": "VIcon", "props": {"size": 22}, "content": icon}
            ]},
            {"component": "div", "content": [
                {"component": "div", "props": {"class": "text-caption text-medium-emphasis"}, "text": label},
                {"component": "div", "props": {"class": "text-h6 font-weight-bold"}, "text": value},
            ]}
        ]}
    ]}


def status_card(plugin: Any, item: dict) -> dict:
    """构建健康检查卡片。"""
    status = item.get("status", "default")
    color_prop = plugin._STATUS_COLOR_PROP.get(status, "grey")
    text_class = plugin._STATUS_TEXT_CLASS.get(status, "text-medium-emphasis")
    return {"component": "VCard", "props": {"variant": "tonal", "elevation": "0", "rounded": "lg", "style": "backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);"}, "content": [
        {"component": "VCardText", "props": {"class": "pa-3"}, "content": [
            {"component": "div", "props": {"class": "d-flex align-center mb-1"}, "content": [
                {"component": "VIcon", "props": {"size": 18, "class": "me-1", "color": color_prop}, "content": item.get("icon") or "mdi-information"},
                {"component": "span", "props": {"class": "text-caption text-medium-emphasis"}, "text": item.get("label", "状态")},
            ]},
            {"component": "div", "props": {"class": f"text-body-2 font-weight-medium {text_class}"}, "text": item.get("text", "")},
        ]}
    ]}


def glass_card_style(blur: int = 14, opacity: float = 0.55) -> str:
    """液态玻璃卡片 CSS。"""
    return (
        f"background: rgba(var(--v-theme-surface), {opacity}); "
        f"backdrop-filter: blur({blur}px); "
        f"-webkit-backdrop-filter: blur({blur}px); "
        f"border: 1px solid rgba(var(--v-theme-on-surface), 0.06);"
    )
