from typing import Any, Dict, List, Tuple

from .models import GenerationMode, OverwritePolicy, SourcePolicy, TriggerType


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def enum_value(enum_cls: Any, value: Any, default: str) -> str:
    # 兼容直接传入 Enum 成员，避免 str(SourcePolicy.X) 变成 "SourcePolicy.X" 后回落 default
    if isinstance(value, enum_cls):
        return value.value
    text = str(value or "").strip()
    if not text:
        return default
    try:
        return enum_cls(text).value
    except Exception:
        # 兼容大小写不敏感 value，以及 "SourcePolicy.AUTO" 这类 str(Enum)
        lowered = text.lower()
        for member in enum_cls:
            if member.value.lower() == lowered or member.name.lower() == lowered:
                return member.value
            if lowered.endswith("." + member.name.lower()):
                return member.value
        return default


def normalize_generation_mode(value: Any) -> str:
    mode = enum_value(GenerationMode, value, GenerationMode.MONITOR.value)
    return GenerationMode.MONITOR.value if mode == GenerationMode.MIXED.value else mode


def normalize_trigger(value: Any) -> str:
    return enum_value(TriggerType, value, TriggerType.MANUAL.value)


def normalize_source_policy(value: Any, default: str = SourcePolicy.AUTO.value) -> str:
    return enum_value(SourcePolicy, value, default)


def normalize_overwrite_policy(value: Any, default: str = OverwritePolicy.SKIP.value) -> str:
    return enum_value(OverwritePolicy, value, default)


def build_config_form() -> Tuple[List[dict], Dict[str, Any]]:
    """
    拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
    """
    form = [
        {
            "component": "VForm",
            "content": [
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VSwitch", "props": {"model": "enabled", "label": "启用插件", "color": "primary"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VSwitch", "props": {"model": "send_notify", "label": "发送通知"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VSwitch", "props": {"model": "clear_history", "label": "清理历史记录"}}],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12},
                            "content": [
                                {
                                    "component": "VTextarea",
                                    "props": {
                                        "model": "path_whitelist",
                                        "label": "监控路径（每行一个）",
                                        "rows": 3,
                                        "placeholder": "/mnt/media/movies\n/downloads",
                                        "hint": "目录变化时自动触发字幕生成",
                                    },
                                }
                            ],
                        }
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [
                                {
                                    "component": "VSwitch",
                                    "props": {
                                        "model": "generation_mode",
                                        "label": "启用独立入库监控",
                                        "true-value": "monitor",
                                        "false-value": "fallback",
                                        "hint": "关闭后仍可接收字幕匹配联动任务和手动任务",
                                    },
                                }
                            ],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 2},
                            "content": [{"component": "VSwitch", "props": {"model": "process_new_only", "label": "仅处理新增视频", "hint": "关闭则处理路径下所有视频"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 2},
                            "content": [{"component": "VSwitch", "props": {"model": "run_now", "label": "手动执行一次", "color": "secondary"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 2},
                            "content": [{"component": "VSwitch", "props": {"model": "translate_zh", "label": "外语翻译成中文", "hint": "使用 OpenAI 兼容大模型翻译"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 2},
                            "content": [{"component": "VSwitch", "props": {"model": "skip_chinese", "label": "中文视频不翻译", "hint": "Whisper 检测到中文时跳过翻译"}}],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12},
                            "content": [{
                                "component": "VTextarea",
                                "props": {
                                    "model": "default_glossary",
                                    "label": "默认术语表",
                                    "rows": 3,
                                    "placeholder": "每行一个术语，例如：Hamilton = 汉密尔顿",
                                    "hint": "应用到所有新任务；联动提交时提供的本片术语表会优先覆盖。",
                                    "persistent-hint": True,
                                },
                            }],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12},
                            "content": [
                                {
                                    "component": "VTextarea",
                                    "props": {
                                        "model": "path_list",
                                        "label": "媒体路径（手动执行时使用）",
                                        "rows": 3,
                                        "placeholder": "绝对路径，每行一个，支持文件和文件夹",
                                    },
                                }
                            ],
                        }
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [
                                {
                                    "component": "VSelect",
                                    "props": {
                                        "model": "asr_model_strategy",
                                        "label": "Whisper 模型策略",
                                        "hint": "自动策略按选中主音轨元数据决定；不会扫描整片或因少量混杂对白切换模型",
                                        "items": [
                                            {"title": "自动：英语快速、非英语多语（推荐）", "value": "auto_english_fast"},
                                            {"title": "手动指定模型", "value": "manual"},
                                        ],
                                    },
                                }
                            ],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [
                                {
                                    "component": "VSelect",
                                    "props": {
                                        "model": "faster_whisper_model",
                                        "label": "Whisper 模型",
                                        "hint": "模型越大效果越好，耗时越久",
                                        "items": [
                                            {"title": "tiny", "value": "tiny"},
                                            {"title": "base", "value": "base"},
                                            {"title": "small", "value": "small"},
                                            {"title": "medium", "value": "medium"},
                                            {"title": "distil-large-v3", "value": "distil-large-v3"},
                                            {"title": "large-v3", "value": "large-v3"},
                                            {"title": "large-v3-turbo", "value": "deepdml/faster-whisper-large-v3-turbo-ct2"},
                                        ],
                                    },
                                }
                            ],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [
                                {
                                    "component": "VSelect",
                                    "props": {
                                        "model": "subtitle_output_mode",
                                        "label": "字幕输出模式",
                                        "items": [
                                            {"title": "双语字幕（翻译+原文）", "value": "bilingual"},
                                            {"title": "纯中文字幕", "value": "chinese_only"},
                                        ],
                                    },
                                }
                            ],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VTextField", "props": {"model": "max_segment_duration", "label": "每段字幕最大时长（秒）", "placeholder": "8"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VTextField", "props": {"model": "max_segment_chars", "label": "每段字幕最大字符数", "placeholder": "50"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VTextField", "props": {"model": "file_size", "label": "文件最小大小（MB）", "placeholder": "默认10"}}],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [{"component": "VSwitch", "props": {"model": "enable_asr", "label": "允许 ASR 生成字幕"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [{"component": "VSwitch", "props": {"model": "auto_detect_language", "label": "自动检测语言", "hint": "由 Whisper 自动识别，而非视频元数据"}}],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [
                                {
                                    "component": "VSelect",
                                    "props": {
                                        "model": "translate_preference",
                                        "label": "字幕源语言偏好",
                                        "items": [
                                            {"title": "仅英文", "value": "english_only"},
                                            {"title": "英文优先", "value": "english_first"},
                                            {"title": "原音优先", "value": "origin_first"},
                                        ],
                                    },
                                }
                            ],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [{"component": "VSwitch", "props": {"model": "proxy", "label": "使用代理下载模型", "hint": "需配置 MP PROXY 环境变量"}}],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VTextField", "props": {"model": "context_window", "label": "上下文窗口大小", "placeholder": "5"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VTextField", "props": {"model": "max_retries", "label": "LLM 请求重试次数", "placeholder": "3"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VSwitch", "props": {"model": "enable_batch", "label": "启用批量翻译", "hint": "开启后速度更快"}}],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [{"component": "VTextField", "props": {"model": "batch_size", "label": "每批翻译行数", "placeholder": "20 (建议不超过30)"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [{"component": "VTextField", "props": {"model": "parallel_workers", "label": "并发线程数", "placeholder": "5"}}],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [{"component": "VSwitch", "props": {"model": "openai_proxy", "label": "使用代理服务器"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 6},
                            "content": [{"component": "VSwitch", "props": {"model": "compatible", "label": "兼容模式"}}],
                        },
                    ],
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VTextField", "props": {"model": "openai_url", "label": "API URL", "placeholder": "https://api.siliconflow.cn"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VTextField", "props": {"model": "openai_key", "label": "API 密钥", "type": "password", "placeholder": "sk-xxx"}}],
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "md": 4},
                            "content": [{"component": "VTextField", "props": {"model": "openai_model", "label": "自定义模型", "placeholder": "inclusionAI/Ling-mini-2.0"}}],
                        },
                    ],
                },
            ],
        }
    ]
    defaults = {
        "enabled": False,
        "clear_history": False,
        "send_notify": False,
        "listen_transfer_event": True,
        "generation_mode": "monitor",
        "process_new_only": True,
        "path_whitelist": "",
        "run_now": False,
        "path_list": "",
        "file_size": "10",
        "translate_preference": "english_first",
        "translate_zh": True,
        "enable_asr": True,
        "auto_detect_language": False,
        "asr_model_strategy": "auto_english_fast",
        "skip_chinese": False,
        "max_segment_duration": 8.0,
        "max_segment_chars": 50,
        "subtitle_max_lines": 2,
        "subtitle_max_chars_per_line": 14,
        "subtitle_min_duration": 0.9,
        "subtitle_max_duration": 5.5,
        "subtitle_max_reading_speed": 14.0,
        "default_glossary": "",
        "faster_whisper_model": "base",
        "proxy": True,
        "openai_proxy": False,
        "compatible": False,
        "openai_url": "https://api.siliconflow.cn",
        "openai_key": "",
        "openai_model": "inclusionAI/Ling-flash-2.0",
        "llm_provider": "openai",
        "llm_base_url": "https://api.siliconflow.cn/v1",
        "llm_base_url_preset": "",
        "llm_api_key": "",
        "llm_model": "inclusionAI/Ling-flash-2.0",
        "llm_context_tokens": "",
        "llm_use_proxy": False,
        "llm_user_agent": "",
        "context_window": 5,
        "max_retries": 3,
        "enable_merge": False,
        "subtitle_output_mode": "bilingual",
        "enable_batch": True,
        "batch_size": 20,
        "parallel_workers": 10,
        "clean_ai_sdh": True,
    }
    return form, defaults


CONFIG_DEFAULTS = build_config_form()[1]
