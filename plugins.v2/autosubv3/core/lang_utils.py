"""语言码安全规范化工具。

统一处理 und/空值/转换失败，避免 iso639.to_iso639_1 返回空串污染路径与偏好匹配。
"""

from __future__ import annotations

from typing import Any

import iso639

_EMPTY_LANGS = {"und", "unknown", "none", "null"}


def normalize_iso_lang(lang: Any, default: str = "en") -> str:
    """将语言代码规范为 ISO-639-1；und/空值/失败时回落 default。"""
    text = str(lang or "").strip()
    if not text or text.lower() in _EMPTY_LANGS:
        return default
    try:
        code = iso639.to_iso639_1(text)
    except Exception:
        code = ""
    code = str(code or "").strip()
    return code or default
