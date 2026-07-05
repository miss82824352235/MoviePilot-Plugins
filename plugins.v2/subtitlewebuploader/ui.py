"""字幕网页上传器 Vuetify 页面。"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def build_form(owner: Any) -> Tuple[List[dict], Dict[str, Any]]:
    """构建插件配置表单。"""
    return [
        {
            "component": "VForm",
            "content": [
                {
                    "component": "VAlert",
                    "props": {
                        "type": "info",
                        "variant": "tonal",
                        "class": "mb-4",
                        "text": "一期模式：TG /subweb 入口 + Web 操作台 + 桥接字幕匹配本体。暂不做额外用户鉴权，写入/删除/AI 提交仍保留二次确认。",
                    },
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VSwitch", "props": {"model": "enabled", "label": "启用插件"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [
                                {
                                    "component": "VTextField",
                                    "props": {
                                        "model": "console_title",
                                        "label": "操作台标题",
                                        "placeholder": "字幕操作台",
                                    },
                                }
                            ],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [
                                {
                                    "component": "VTextField",
                                    "props": {
                                        "model": "session_timeout",
                                        "label": "会话超时（秒）",
                                        "type": "number",
                                    },
                                }
                            ],
                        },
                    ],
                },
                {
                    "component": "VTextField",
                    "props": {
                        "model": "console_base_url",
                        "label": "操作台外部访问地址",
                        "placeholder": "例如 http://192.168.1.10:3001 或 https://mp.example.com",
                        "hint": "TG 按钮必须使用手机可访问的完整 MoviePilot 地址；留空时优先使用系统 APP_DOMAIN。不要填写 127.0.0.1/localhost。",
                        "persistent-hint": True,
                    },
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [
                                {
                                    "component": "VSwitch",
                                    "props": {
                                        "model": "tg_entry_enabled",
                                        "label": "启用 /subweb Telegram 入口",
                                    },
                                }
                            ],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [
                                {
                                    "component": "VSwitch",
                                    "props": {
                                        "model": "legacy_api_enabled",
                                        "label": "保留旧硬链接目录 API",
                                        "hint": "旧 /subtitleweb/browse/upload/delete 等接口；新桥接 API 不依赖硬链接根目录。",
                                        "persistent-hint": True,
                                    },
                                }
                            ],
                        },
                    ],
                },
                {
                    "component": "VTextField",
                    "props": {
                        "model": "root_path",
                        "label": "旧硬链接根目录（仅旧 API 使用）",
                        "placeholder": "/mnt/link 或 /volume1/media",
                        "hint": "新 Web 操作台优先通过字幕匹配插件目标索引选择资源，此项可留空。",
                        "persistent-hint": True,
                    },
                },
            ],
        }
    ], {
        "enabled": bool(getattr(owner, "_enabled", False)),
        "console_title": getattr(owner, "_console_title", "字幕操作台"),
        "session_timeout": int(getattr(owner, "_session_timeout", 3600)),
        "tg_entry_enabled": bool(getattr(owner, "_tg_entry_enabled", True)),
        "legacy_api_enabled": bool(getattr(owner, "_legacy_api_enabled", False)),
        "console_base_url": getattr(owner, "_console_base_url", "") or "",
        "root_path": getattr(owner, "_root_path", "") or "",
    }


def build_page(owner: Any) -> List[dict]:
    """构建插件详情页。"""
    state_color = "success" if owner.get_state() else "warning"
    state_text = "已启用" if owner.get_state() else "未启用"
    return [
        {
            "component": "VCard",
            "props": {"variant": "tonal", "rounded": "lg", "class": "mb-4"},
            "content": [
                {
                    "component": "VCardText",
                    "content": [
                        {"component": "div", "props": {"class": "text-h6 mb-2"}, "text": getattr(owner, "_console_title", "字幕操作台")},
                        {
                            "component": "VChip",
                            "props": {"color": state_color, "variant": "tonal", "class": "mb-3"},
                            "text": state_text,
                        },
                        {
                            "component": "VAlert",
                            "props": {
                                "type": "info",
                                "variant": "tonal",
                                "text": "从 Telegram 发送 /subweb 可打开移动端字幕操作台；网页端 API 已桥接 SubtitleManualUpload 的搜索、目标、上传预览/写入、删除、AI 与任务状态。",
                            },
                        },
                    ],
                }
            ],
        }
    ]
