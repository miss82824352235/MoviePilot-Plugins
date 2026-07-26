import re
from datetime import timedelta
from typing import Dict, List, Tuple

import srt


class SubtitleLayoutService:
    """Apply safe, playback-oriented subtitle layout rules and quality checks."""

    def __init__(self, settings: Dict[str, object]):
        self._settings = settings

    def _number(self, name: str, default, minimum=None):
        try:
            value = type(default)(self._settings.get(name, default))
        except (TypeError, ValueError):
            value = default
        return max(minimum, value) if minimum is not None else value

    @property
    def max_lines(self):
        return self._number("subtitle_max_lines", 2, 1)

    @property
    def max_chars_per_line(self):
        return self._number("subtitle_max_chars_per_line", 14, 8)

    @property
    def min_duration(self):
        return self._number("subtitle_min_duration", 0.9, 0.1)

    @property
    def max_duration(self):
        return self._number("subtitle_max_duration", 5.5, self.min_duration)

    @property
    def max_reading_speed(self):
        return self._number("subtitle_max_reading_speed", 14.0, 1.0)

    @staticmethod
    def _display_length(text: str) -> int:
        return len(re.sub(r"\s+", "", text or ""))

    @staticmethod
    def _duration(item: srt.Subtitle) -> float:
        return max(0.0, (item.end - item.start).total_seconds())

    @staticmethod
    def _normalize_translation(text: str) -> str:
        text = re.sub(r"[ \t]+", "", text or "").strip()
        text = re.sub(r"…{2,}", "…", text)
        return text[:-1].rstrip() if text.endswith("。") else text

    def _wrap_chinese(self, text: str) -> Tuple[str, bool]:
        text = self._normalize_translation(text)
        limit = self.max_chars_per_line
        if self._display_length(text) <= limit:
            return text, False
        if self.max_lines < 2 or self._display_length(text) > limit * self.max_lines:
            return text, False
        target = min(limit, max(1, self._display_length(text) // 2))
        candidates = [match.start() + 1 for match in re.finditer(r"[，、；：？！?!]", text)]
        candidates += [match.start() + 1 for match in re.finditer(r"\s+", text)]
        candidates = [index for index in candidates if 1 <= index < len(text)]
        split_at = min(candidates, key=lambda index: abs(index - target)) if candidates else target
        left, right = text[:split_at].rstrip(), text[split_at:].lstrip()
        if not left or not right or self._display_length(left) > limit or self._display_length(right) > limit:
            return text, False
        return f"{left}\n{right}", True

    def _split_text(self, text: str, limit: int) -> List[str]:
        """Split an overlong translation near punctuation without dropping text."""
        text = self._normalize_translation(text)
        chunks = []
        while self._display_length(text) > limit:
            candidates = [match.start() + 1 for match in re.finditer(r"[，、；：？！?!]", text[:limit + 1])]
            split_at = candidates[-1] if candidates else limit
            chunk = text[:split_at].strip()
            if not chunk:
                return [text]
            chunks.append(chunk)
            text = text[split_at:].strip()
        return chunks + ([text] if text else [])

    def _split_overlong_subtitle(self, item: srt.Subtitle, next_start) -> List[srt.Subtitle]:
        """Safely divide a too-long Chinese cue when its timeline has enough room."""
        text = self._normalize_translation((item.content or "").split("\n")[0])
        capacity = self.max_lines * self.max_chars_per_line
        if self._display_length(text) <= capacity:
            return []
        chunks = self._split_text(text, capacity)
        if len(chunks) < 2:
            return []
        required = max(self.min_duration * len(chunks), self._display_length(text) / self.max_reading_speed)
        available_end = item.start + timedelta(seconds=min(self.max_duration, required))
        if next_start:
            available_end = min(available_end, next_start - timedelta(milliseconds=40))
        if (available_end - item.start).total_seconds() + 1e-6 < required:
            return []
        available_seconds = (available_end - item.start).total_seconds()
        minimum_total = self.min_duration * len(chunks)
        remaining_seconds = max(0.0, available_seconds - minimum_total)
        weights = [self._display_length(chunk) for chunk in chunks]
        total_weight = max(1, sum(weights))
        cursor = item.start
        split_items = []
        for index, (chunk, weight) in enumerate(zip(chunks, weights), 1):
            duration = self.min_duration + remaining_seconds * weight / total_weight
            end = available_end if index == len(chunks) else cursor + timedelta(seconds=duration)
            split_items.append(srt.Subtitle(index=item.index, start=cursor, end=end, content=chunk))
            cursor = end
        return split_items

    def process_file(self, path: str, bilingual: bool = False) -> Dict[str, int]:
        with open(path, "r", encoding="utf-8") as handle:
            subtitles = list(srt.parse(handle.read()))
        report = self.process_subtitles(subtitles, bilingual=bilingual)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(srt.compose(subtitles))
        report["total"] = len(subtitles)
        return report

    def process_subtitles(self, subtitles: List[srt.Subtitle], bilingual: bool = False) -> Dict[str, int]:
        report = {"total": len(subtitles), "overlong": 0, "over_speed": 0, "overlap": 0,
                  "too_short": 0, "line_overflow": 0, "auto_fixed": 0, "remaining": 0}
        gap = timedelta(milliseconds=40)
        prepared = []
        for index, item in enumerate(subtitles):
            lines = (item.content or "").split("\n")
            next_start = subtitles[index + 1].start if index + 1 < len(subtitles) else None
            if not bilingual or len(lines) <= 1:
                split_items = self._split_overlong_subtitle(item, next_start)
                if split_items:
                    report["overlong"] += 1
                    report["auto_fixed"] += 1
                    prepared.extend(split_items)
                    continue
            prepared.append(item)
        subtitles[:] = prepared

        for index, item in enumerate(subtitles):
            lines = (item.content or "").split("\n")
            translated = self._normalize_translation(lines[0]) if lines else ""
            if bilingual and len(lines) > 1:
                item.content = "\n".join([translated] + lines[1:])
            else:
                wrapped, changed = self._wrap_chinese(translated)
                item.content = wrapped
                if changed:
                    report["auto_fixed"] += 1

            visible_lines = item.content.split("\n")
            if len(visible_lines) > self.max_lines or any(self._display_length(line) > self.max_chars_per_line for line in visible_lines):
                report["line_overflow"] += 1
            chars = self._display_length(translated)
            if chars > self.max_chars_per_line * self.max_lines:
                report["overlong"] += 1
            duration = self._duration(item)
            next_start = subtitles[index + 1].start if index + 1 < len(subtitles) else None
            needed = max(self.min_duration, chars / self.max_reading_speed) if chars else self.min_duration
            if duration < self.min_duration:
                report["too_short"] += 1
            if chars and duration > 0 and chars / duration > self.max_reading_speed:
                report["over_speed"] += 1
            if duration < needed:
                desired_end = item.start + timedelta(seconds=min(self.max_duration, needed))
                safe_end = min(desired_end, next_start - gap) if next_start else desired_end
                if safe_end > item.end:
                    item.end = safe_end
                    report["auto_fixed"] += 1
            if next_start and item.end > next_start:
                report["overlap"] += 1
                safe_end = next_start - gap
                if safe_end - item.start >= timedelta(seconds=self.min_duration):
                    item.end = safe_end
                    report["auto_fixed"] += 1

        for index, item in enumerate(subtitles, 1):
            item.index = index
        for item in subtitles:
            duration = self._duration(item)
            text = (item.content or "").split("\n")[0]
            chars = self._display_length(text)
            if (duration < self.min_duration or duration > self.max_duration or
                    (chars and duration and chars / duration > self.max_reading_speed) or
                    any(self._display_length(line) > self.max_chars_per_line for line in item.content.split("\n"))):
                report["remaining"] += 1
        return report
