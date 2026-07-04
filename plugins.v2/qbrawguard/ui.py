"""
QBRawGuard MoviePilot 原生风格 UI 模块。

职责：
1. 构建插件详情页和配置表单，优先使用 MoviePilot 常见 Vuetify 组件风格。
2. 配置页内提供运行状态、健康检查和调试动作，减少设置页/仪表盘割裂。
3. 只读取插件实例状态，不执行判定、下载器操作或清理动作；按钮通过插件 API 触发。
"""

from typing import Any, Dict, List, Tuple


def build_page(plugin: Any) -> List[dict]:
    """构建插件详情首页。"""
    checks = plugin._check_status()
    return [
        header_card(plugin),
        stats_row(plugin),
        section_title("系统健康检查", "mdi-heart-pulse"),
        health_row(plugin, checks),
        section_title("调试动作", "mdi-tools"),
        action_row(plugin),
        {"component": "VAlert", "props": {
            "type": "info", "variant": "tonal", "density": "comfortable", "class": "mt-3",
            "text": "原盘判定基于下载器返回的真实文件列表/目录结构；普通 Web/HDTV 单文件 .ts、扁平 .m2ts 不会作为原盘拦截。清理按钮仅处理已拦截删除任务的 hash 关联残留。",
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
    defaults = dict(plugin.CONFIG_DEFAULTS)
    return form, defaults


def form_tabs(plugin: Any, downloader_opts: list) -> List[dict]:
    """构建配置页 Tab 容器。"""
    titles = ["运行状态", "基本设置", "通知与测试", "高级规则"]
    icons = ["mdi-view-dashboard", "mdi-tune", "mdi-bell-ring", "mdi-regex"]
    windows = [tab_status(plugin), tab_basic(downloader_opts), tab_notify(), tab_advanced()]
    return [
        {"component": "VTabs", "props": {"model": "_tab", "grow": True, "density": "comfortable"},
         "content": [{"component": "VTab", "props": {"value": i, "prepend-icon": icons[i]}, "text": t}
                     for i, t in enumerate(titles)]},
        {"component": "VWindow", "props": {"model": "_tab", "class": "mt-4"},
         "content": [{"component": "VWindowItem", "props": {"value": i}, "content": w}
                     for i, w in enumerate(windows)]},
    ]


def tab_status(plugin: Any) -> list:
    """构建配置页运行状态 Tab。"""
    return [
        {"component": "VAlert", "props": {
            "type": "info", "variant": "tonal", "density": "comfortable", "class": "mb-4",
            "text": "这里显示当前运行状态和调试动作；真正拦截依据为下载器真实文件列表，不靠种子名简单判断。红色清理按钮会按 hash 清理已拦截删除任务的 MP 关联残留，请谨慎点击。",
        }},
        stats_row(plugin),
        section_title("系统健康检查", "mdi-heart-pulse"),
        health_row(plugin, plugin._check_status()),
        section_title("调试动作", "mdi-tools"),
        action_row(plugin),
    ]


def tab_basic(downloader_opts: list) -> list:
    """构建基本设置 Tab。"""
    return [
        card("运行开关", [
            field_row(
                switch("enabled", "启用插件"),
                switch("fast_scan_enabled", "快速拦截", "标题预检仅用于降噪，最终仍检查真实文件列表"),
                switch("full_scan_enabled", "全量兜底", "低频扫描所有任务真实文件列表"),
            ),
            field_row(
                number("interval", "快速间隔（分钟）", min_val=1),
                number("full_interval", "全量间隔（分钟）", min_val=5, hint="留空=快速间隔×5"),
                switch("include_completed", "检查已完成", "避免间隔期内任务漏检"),
            ),
        ]),
        card("处理策略", [
            field_row(
                select("action", "命中动作", [
                    {"title": "停止下载", "value": "stop"},
                    {"title": "删除并联动清理", "value": "delete"},
                ], hint="删除会复用 MP Chain 和整理记录清理语义"),
                text("tag", "命中标签"),
                switch("retry_failed", "失败重试"),
            ),
            field_row({"component": "VCol", "props": {"cols": 12}, "content": [
                {"component": "VSelect", "props": {
                    "multiple": True, "chips": True, "model": "downloaders",
                    "label": "QB 下载器", "items": downloader_opts,
                    "hint": "留空 = 全部 QB 下载器", "persistent-hint": True,
                }}
            ]}),
        ]),
    ]


def tab_notify() -> list:
    """构建通知与测试 Tab。"""
    return [
        card("通知配置", [
            field_row(
                switch("notify", "发送通知"),
                select("notify_type", "通知场景", [
                    {"title": "智能体", "value": "Agent"},
                    {"title": "插件", "value": "Plugin"},
                    {"title": "资源下载", "value": "Download"},
                    {"title": "整理入库", "value": "Organize"},
                    {"title": "其它", "value": "Other"},
                ], hint="发送动作复用 MP 原生通知通道"),
                text("alert_image", "报警图地址", hint="留空自动恢复默认图标"),
            ),
        ]),
        card("模拟通知测试", [
            field_row(text("test_title", "测试标题", md=6), text("test_subtitle", "测试种子名/副标题", md=6)),
            field_row(text("test_site", "测试站点"), text("test_seeders", "测试做种数"), text("test_tags", "测试标签")),
            field_row({"component": "VCol", "props": {"cols": 12}, "content": [
                {"component": "VTextField", "props": {"model": "test_format", "label": "判定格式", "hint": "只写格式依据，不暴露路径/hash", "persistent-hint": True}}
            ]}),
            field_row({"component": "VCol", "props": {"cols": 12}, "content": [
                {"component": "VTextarea", "props": {"model": "test_message", "label": "下载通知字段（多行）", "rows": 4, "hint": "按 MP 下载通知格式逐行填写", "persistent-hint": True}}
            ]}),
            field_row(action_button("发送模拟拦截测试通知", "mdi-send", "warning", "test_notify", md=12)),
        ]),
    ]


def tab_advanced() -> list:
    """构建高级规则 Tab。"""
    return [
        {"component": "VAlert", "props": {"type": "warning", "variant": "tonal", "density": "comfortable", "class": "mb-4", "text": "一般不需修改。规则过宽可能误杀正常任务，建议先用默认规则在小范围验证后再调整。普通 Web/HDTV 单文件 .ts、扁平 .m2ts 默认放行。"}},
        card("原盘识别规则", [
            {"component": "VRow", "content": [{"component": "VCol", "props": {"cols": 12}, "content": [
                {"component": "VTextarea", "props": {"model": "patterns", "label": "原盘识别正则（每行一条）", "rows": 10, "hint": "以 # 开头的行为注释；留空自动恢复内置默认规则", "persistent-hint": True}}
            ]}]},
        ]),
    ]


def header_card(plugin: Any) -> dict:
    """构建 MP 原生风格标题卡片。"""
    return {"component": "VCard", "props": {"variant": "tonal", "rounded": "lg", "class": "mb-4"}, "content": [
        {"component": "VCardText", "props": {"class": "d-flex align-center"}, "content": [
            {"component": "VAvatar", "props": {"color": "primary", "variant": "tonal", "rounded": "lg", "size": 48, "class": "me-3"}, "content": [
                {"component": "VImg", "props": {"src": plugin.plugin_icon or "", "width": 30, "height": 30}}
            ]},
            {"component": "div", "content": [
                {"component": "div", "props": {"class": "text-h6 font-weight-bold"}, "text": f"原盘通知 v{plugin.plugin_version}"},
                {"component": "div", "props": {"class": "text-body-2 text-medium-emphasis"}, "text": "基于下载器真实文件列表识别 Emby 不友好的原盘结构"},
            ]},
            {"component": "VSpacer"},
            {"component": "VChip", "props": {"color": "success" if plugin.enabled else "grey", "variant": "flat", "size": "small", "text": "运行中" if plugin.enabled else "已停用"}},
        ]}
    ]}


def section_title(title: str, icon: str) -> dict:
    """构建分区标题。"""
    return {"component": "div", "props": {"class": "d-flex align-center text-subtitle-2 font-weight-medium mb-2 mt-4"}, "content": [
        {"component": "VIcon", "props": {"size": 18, "class": "me-1"}, "content": icon},
        {"component": "span", "text": title},
    ]}


def card(title: str, content: List[dict]) -> dict:
    """构建 MP 原生 tonal 卡片。"""
    return {"component": "VCard", "props": {"variant": "tonal", "rounded": "lg", "class": "mb-4"}, "content": [
        {"component": "VCardTitle", "props": {"class": "text-subtitle-1 font-weight-medium pb-0"}, "text": title},
        {"component": "VCardText", "content": content},
    ]}


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


def action_row(plugin: Any) -> dict:
    """构建调试动作按钮行。"""
    return {"component": "VRow", "content": [
        action_button("发送模拟拦截测试通知", "mdi-send", "warning", "test_notify"),
        action_button(f"清理已拦截删除任务残留（队列 {len(plugin._rescan_queue)}）", "mdi-broom", "error", "manual_rescan"),
    ]}


def action_button(button_text: str, icon: str, color: str, endpoint: str, method: str = "post", md: int = 6) -> dict:
    """构建操作按钮。"""
    return {"component": "VCol", "props": {"cols": 12, "md": md}, "content": [
        {"component": "VBtn", "props": {"color": color, "variant": "tonal", "rounded": "lg", "block": True, "prepend-icon": icon, "class": "text-none"},
         "text": button_text, "events": {"click": {"api": f"plugin/QBRawGuard/{endpoint}", "method": method}}}
    ]}


def metric_card(icon: str, label: str, value: str, color: str = "primary") -> dict:
    """构建统计指标卡片。"""
    return {"component": "VCard", "props": {"variant": "tonal", "rounded": "lg"}, "content": [
        {"component": "VCardText", "props": {"class": "d-flex align-center pa-3"}, "content": [
            {"component": "VAvatar", "props": {"color": color, "variant": "tonal", "rounded": "lg", "size": 42, "class": "me-3"}, "content": [
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
    return {"component": "VCard", "props": {"variant": "tonal", "rounded": "lg"}, "content": [
        {"component": "VCardText", "props": {"class": "pa-3"}, "content": [
            {"component": "div", "props": {"class": "d-flex align-center mb-1"}, "content": [
                {"component": "VIcon", "props": {"size": 18, "class": "me-1", "color": color_prop}, "content": item.get("icon") or "mdi-information"},
                {"component": "span", "props": {"class": "text-caption text-medium-emphasis"}, "text": item.get("label", "状态")},
            ]},
            {"component": "div", "props": {"class": f"text-body-2 font-weight-medium {text_class}"}, "text": item.get("text", "")},
        ]}
    ]}
