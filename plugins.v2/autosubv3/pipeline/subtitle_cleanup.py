import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Sequence, Tuple


@dataclass
class SubtitleCleanupStats:
    """字幕清理统计结果。"""

    total_blocks: int = 0
    changed_blocks: int = 0
    removed_blocks: int = 0
    removed_brackets: int = 0
    removed_speaker_labels: int = 0
    removed_sdh_lines: int = 0
    samples: List[Dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        """转换为可序列化字典。"""
        return {
            "total_blocks": self.total_blocks,
            "changed_blocks": self.changed_blocks,
            "removed_blocks": self.removed_blocks,
            "removed_brackets": self.removed_brackets,
            "removed_speaker_labels": self.removed_speaker_labels,
            "removed_sdh_lines": self.removed_sdh_lines,
            "samples": self.samples[:20],
        }


class SubtitleCleanupService:
    """清理成品字幕中的 AI/CC 味舞台说明。"""

    _ITALIC_TAG_RE = re.compile(r"</?i>", re.I)
    _HTML_TAG_RE = re.compile(r"</?(?:i|b|u|font|c|ruby|rt|rp)[^>]*>", re.I)
    _MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
    _EMPTY_WRAPPER_RE = re.compile(r"^\s*(?:[-—–]+\s*)?(?:[♪♫♬\s,，、：:;；·…\-—–]+)?\s*$")

    _CC_KEYWORDS = (
        "声", "声音", "音效", "音乐", "配乐", "掌声", "笑声", "哭声", "喊声", "叫声", "欢呼",
        "欢呼声", "尖叫", "尖叫声", "脚步", "脚步声", "敲门", "开门", "关门", "电话", "铃声",
        "咳嗽", "喘息", "喘气", "叹气", "倒吸", "轻笑", "苦笑", "哭泣", "抽泣", "啜泣",
        "风声", "雨声", "雷声", "爆炸", "枪声", "耳语", "低语", "旁白", "画外音", "众人",
        "观众", "人群", "孩子们", "喊叫", "呼喊", "鼓掌", "拍手", "口哨", "含混", "听不清", "不可辨",
        "歌曲结束", "响起", "播放", "继续", "渐弱", "渐强", "停止", "结束", "哼唱", "哼声",
        "笑", "哭", "喘", "呻吟", "吸气", "沉默", "静默", "字幕", "解说",
    )
    _EN_CC_KEYWORDS = (
        "music", "song", "playing", "applause", "cheer", "cheering", "laugh", "laughs", "laughter",
        "door", "knock", "footstep", "sigh", "sighs", "cough", "coughs", "cry", "cries", "crying",
        "scream", "screaming", "crowd", "audience", "chant", "chanting", "inaudible", "indistinct",
        "wind", "rain", "thunder", "phone", "ringing", "whistle", "whooping", "chatter", "chattering",
        "gasps", "gasp", "narrator", "voiceover", "continues", "fades", "stops", "ends", "claps",
    )
    _SAFE_DIALOGUE_HINTS = re.compile(r"[我你他她它们的是了不在有和就都而及与把被让给吗呢吧啊呀哦嗯]|[A-Za-z]{3,}")
    _LYRIC_MARK_RE = re.compile(r"[♪♫♬]")

    _BRACKET_RE = re.compile(r"[（(【\[]([^（）()【】\[\]\n\r]{1,60})[）)】\]]")
    _NON_SPEAKER_PREFIX_RE = re.compile(
        r"^(?:片名|字幕|翻译|校对|时间轴|压制|制作|出品|导演|编剧|主演|第?[一二三四五六七八九十0-9]+条?|亲爱的[^：:]{0,12})[：:]"
    )
    _SPEAKER_PREFIX_RE = re.compile(
        r"(^|[\n\r]|(?:^|[\n\r])\s*[-—–]\s*)"
        r"(?:[《\"“][^》\"”]{2,24}[》\"”]|[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9· .．'’\-]{1,23}|[A-Z][A-Z .'’\-]{1,23})"
        r"(?:（[^）]{1,16}）|\([^)]{1,16}\))?\s*[：:]\s*"
    )
    _SAYS_PREFIX_RE = re.compile(
        r"(^|[\n\r]|(?:^|[\n\r])\s*[-—–]\s*)"
        r"(?:[\u4e00-\u9fa5A-Za-z· .]{1,16}|他|她|他们|她们|有人|男人|女人|男孩|女孩)"
        r"\s*(?:说|说道|喊道|问道|低声说|轻声说|大喊)\s*[：:]\s*"
    )

    def __init__(self, enabled: Any = True):
        """初始化字幕清理器。"""
        self._enabled = enabled

    def enabled(self) -> bool:
        """返回当前清理开关状态。"""
        if callable(self._enabled):
            try:
                return bool(self._enabled())
            except Exception:
                return True
        return bool(self._enabled)

    def clean_srt_file(self, path: str) -> SubtitleCleanupStats:
        """清理 SRT 文件并在有变化时覆盖写回。"""
        stats = SubtitleCleanupStats()
        if not self.enabled() or not path:
            return stats
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            original = fh.read()
        cleaned, stats = self.clean_srt_text(original)
        if cleaned != original:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(cleaned)
        return stats

    _CUE_HEADER_RE = re.compile(
        r"(?m)^(?P<index>\d+)\s*\n"
        r"(?P<time>\d{2}:\d{2}:\d{2}[,\.]\d{1,3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{1,3})\s*\n"
    )

    def clean_srt_text(self, text: str) -> Tuple[str, SubtitleCleanupStats]:
        """清理 SRT 文本并返回新文本与统计。"""
        stats = SubtitleCleanupStats()
        if not self.enabled() or not text:
            return text, stats
        newline = "\n"
        cues = self._split_cues(text)
        output_blocks: List[str] = []
        new_index = 1
        for _old_index, time_line, body_lines in cues:
            stats.total_blocks += 1
            old_body = "\n".join(body_lines).strip()
            new_body_lines, changed, block_removed, block_stats = self._clean_body_lines(body_lines)
            stats.removed_brackets += block_stats.get("removed_brackets", 0)
            stats.removed_speaker_labels += block_stats.get("removed_speaker_labels", 0)
            stats.removed_sdh_lines += block_stats.get("removed_sdh_lines", 0)
            if block_removed or not any(line.strip() for line in new_body_lines):
                stats.removed_blocks += 1
                stats.changed_blocks += 1
                self._add_sample(stats, old_body, "")
                continue
            new_body = "\n".join(new_body_lines).strip()
            if changed or new_body != old_body:
                stats.changed_blocks += 1
                self._add_sample(stats, old_body, new_body)
            # 标准 SRT 要求 cue 之间必须有空行分隔。
            # 之前用单换行拼接会把合法 SRT 压成一整块，播放器无法解析。
            output_blocks.append(f"{new_index}\n{time_line}\n{new_body}")
            new_index += 1
        result = (newline + newline).join(output_blocks)
        if output_blocks:
            result += newline
        return result, stats

    def _split_cues(self, text: str) -> List[Tuple[str, str, List[str]]]:
        """拆分 SRT cue。

        兼容两种输入：
        1. 标准 SRT（cue 之间有空行）
        2. 被错误清理器压扁后的 SRT（cue 之间没有空行）
        """
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        if not normalized.strip():
            return []
        matches = list(self._CUE_HEADER_RE.finditer(normalized))
        if matches:
            cues: List[Tuple[str, str, List[str]]] = []
            for idx, match in enumerate(matches):
                body_start = match.end()
                body_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(normalized)
                body = normalized[body_start:body_end].strip("\n")
                body_lines = [line.rstrip() for line in body.split("\n")] if body else []
                while body_lines and not body_lines[-1].strip():
                    body_lines.pop()
                cues.append((match.group("index"), match.group("time").strip(), body_lines))
            return cues

        # 兜底：仍按空行拆，兼容极少数非标准时间轴格式。
        blocks = re.split(r"\n\s*\n", normalized.strip())
        cues = []
        for raw_block in blocks:
            parsed = self._parse_block(raw_block)
            if parsed:
                cues.append(parsed)
        return cues

    @staticmethod
    def _parse_block(block: str) -> Tuple[str, str, List[str]]:
        """解析单个 SRT 块。"""
        lines = [line.rstrip() for line in block.split("\n")]
        if len(lines) < 3 or "-->" not in lines[1]:
            return None
        return lines[0].strip(), lines[1].strip(), lines[2:]

    def _clean_body_lines(self, lines: Sequence[str]) -> Tuple[List[str], bool, bool, Dict[str, int]]:
        """清理字幕正文行。"""
        changed = False
        removed_line = False
        stats = {"removed_brackets": 0, "removed_speaker_labels": 0, "removed_sdh_lines": 0}
        result: List[str] = []
        for line in lines:
            original = line
            cleaned = self._clean_line(line, stats)
            if cleaned is None:
                changed = True
                removed_line = True
                stats["removed_sdh_lines"] += 1
                continue
            if cleaned != original:
                changed = True
            if cleaned.strip():
                result.append(cleaned)
        if not result and removed_line:
            return [], changed, True, stats
        return result, changed, False, stats

    def _clean_line(self, line: str, stats: Dict[str, int]) -> str:
        """清理单行字幕。"""
        text = line.strip()
        if not text:
            return ""
        before = text
        text = self._remove_sdh_brackets(text, stats)
        text = self._remove_speaker_prefixes(text, stats)
        text = self._strip_empty_markup(text)
        if self._is_pure_sdh_line(text):
            return None
        if text != before:
            text = self._normalize_line_spacing(text)
        return text.strip()

    def _remove_sdh_brackets(self, text: str, stats: Dict[str, int]) -> str:
        """移除环境声和动作说明括注。"""
        def repl(match: re.Match) -> str:
            inner = match.group(1).strip()
            if self._is_sdh_bracket(inner):
                stats["removed_brackets"] += 1
                return ""
            # 对说话人括注如 观众（齐声）：保守保留，交由前缀清理处理。
            if self._is_speaker_hint(inner) and self._line_looks_like_speaker_prefix(text, match.end()):
                stats["removed_brackets"] += 1
                return ""
            return match.group(0)

        last = None
        current = text
        for _ in range(4):
            if current == last:
                break
            last = current
            current = self._BRACKET_RE.sub(repl, current)
        return current

    def _remove_speaker_prefixes(self, text: str, stats: Dict[str, int]) -> str:
        """移除说话人标签和“某某说”前缀。"""
        if self._NON_SPEAKER_PREFIX_RE.search(self._strip_markup(text).strip()):
            return text
        before = text
        text = self._SAYS_PREFIX_RE.sub(lambda m: m.group(1) or "", text)
        text = self._SPEAKER_PREFIX_RE.sub(lambda m: m.group(1) or "", text)
        if text != before:
            stats["removed_speaker_labels"] += 1
        # 清理行内第二说话人：- 男人：你好 -> - 你好
        before_inline = text
        text = re.sub(r"([\n\r]|^|\s[-—–]\s*)[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9· .．'’\-]{0,20}\s*[：:]\s*", lambda m: m.group(1), text)
        if text != before_inline:
            stats["removed_speaker_labels"] += 1
        return text

    def _is_pure_sdh_line(self, text: str) -> bool:
        """判断整行是否仅为 CC/SDH 辅助说明。"""
        plain = self._strip_markup(text).strip()
        if not plain:
            return True
        no_dash = re.sub(r"^[-—–\s]+", "", plain).strip()
        if not no_dash:
            return False
        # 纯括注说明。
        if self._is_wrapped(no_dash):
            inner = no_dash[1:-1].strip()
            return self._is_sdh_bracket(inner)
        # 多个纯括注/音乐符号组合。
        tmp = self._BRACKET_RE.sub(lambda m: "" if self._is_sdh_bracket(m.group(1).strip()) else m.group(0), no_dash)
        tmp = self._strip_markup(tmp)
        if self._EMPTY_WRAPPER_RE.match(tmp):
            return True
        return False

    def _is_sdh_bracket(self, inner: str) -> bool:
        """判断括号内容是否属于舞台说明。"""
        text = self._strip_markup(inner).strip().lower()
        if not text:
            return True
        compact = re.sub(r"[\s　]+", "", text)
        if len(compact) <= 1:
            return False
        if any(keyword.lower() in text for keyword in self._EN_CC_KEYWORDS):
            return True
        if any(keyword in compact for keyword in self._CC_KEYWORDS):
            return True
        # 纯拟声词或语气词括注。
        if re.fullmatch(r"[啊呀哈呵嘿哼嗯呃呜噢哦唉嘘嘻嘿\-—…\.\s]{1,12}", compact):
            return True
        return False

    @staticmethod
    def _is_speaker_hint(inner: str) -> bool:
        """判断括注是否是说话方式提示。"""
        return bool(re.search(r"齐声|低声|轻声|大喊|喊叫|耳语|旁白|画外音|合唱|独白|继续|渐弱", inner or ""))

    @staticmethod
    def _line_looks_like_speaker_prefix(text: str, end_pos: int) -> bool:
        """判断括注后是否紧跟说话人冒号。"""
        tail = text[end_pos:end_pos + 8]
        return "：" in tail or ":" in tail

    @staticmethod
    def _is_wrapped(text: str) -> bool:
        """判断文本是否由括号包裹。"""
        pairs = {"（": "）", "(": ")", "[": "]", "【": "】"}
        return len(text) >= 2 and text[0] in pairs and text[-1] == pairs[text[0]]

    def _strip_empty_markup(self, text: str) -> str:
        """清理空标签和多余连接符。"""
        text = re.sub(r"<i>\s*</i>", "", text, flags=re.I)
        text = re.sub(r"<i>\s*[-—–]?\s*</i>", "", text, flags=re.I)
        text = re.sub(r"</i>\s*<i>", " ", text, flags=re.I)
        if self._EMPTY_WRAPPER_RE.match(self._strip_markup(text)):
            text = self._strip_markup(text)
        elif "</i>" in text and "<i>" not in text:
            text = self._strip_markup(text)
        text = re.sub(r"^\s*[-—–]\s*$", "", text)
        text = re.sub(r"^\s*[-—–]\s*(?=[。！？!?,，、；;：:]|$)", "", text)
        text = re.sub(r"(^|\s)[-—–]\s*$", r"\1", text)
        return text

    def _normalize_line_spacing(self, text: str) -> str:
        """规范清理后的空格和标点。"""
        text = self._MULTI_SPACE_RE.sub(" ", text)
        text = re.sub(r"\s+([，。！？、；：])", r"\1", text)
        text = re.sub(r"([（(【\[])[\s　]+", r"\1", text)
        text = re.sub(r"[\s　]+([）)】\]])", r"\1", text)
        text = re.sub(r"^\s*[-—–]\s*", "", text)
        text = re.sub(r"\s*[-—–]\s*$", "", text)
        text = text.replace("<i></i>", "")
        return text.strip()

    def _strip_markup(self, text: str) -> str:
        """去除字幕样式标签。"""
        return self._HTML_TAG_RE.sub("", text or "")

    @staticmethod
    def _add_sample(stats: SubtitleCleanupStats, before: str, after: str) -> None:
        """记录少量清理样本。"""
        if len(stats.samples) >= 20:
            return
        stats.samples.append({"before": before[:180], "after": after[:180]})
