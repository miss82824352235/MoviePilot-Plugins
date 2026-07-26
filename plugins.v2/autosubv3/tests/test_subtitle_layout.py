import unittest
from datetime import timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import srt

_MODULE_PATH = Path(__file__).resolve().parents[1] / "pipeline" / "subtitle_layout.py"
_SPEC = spec_from_file_location("autosubv3_subtitle_layout", _MODULE_PATH)
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
SubtitleLayoutService = _MODULE.SubtitleLayoutService


class SubtitleLayoutServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = SubtitleLayoutService({
            "subtitle_max_chars_per_line": 16,
            "subtitle_min_duration": 0.9,
            "subtitle_max_duration": 5.5,
            "subtitle_max_reading_speed": 14,
        })

    def test_wraps_chinese_only_to_two_lines(self):
        subtitle = srt.Subtitle(1, timedelta(seconds=0), timedelta(seconds=3), "这是一个足够长的中文字幕测试用于验证自动换行是否符合播放规范")
        report = self.service.process_subtitles([subtitle])
        self.assertEqual(2, len(subtitle.content.split("\n")))
        self.assertGreaterEqual(report["auto_fixed"], 1)

    def test_bilingual_does_not_add_a_third_line(self):
        subtitle = srt.Subtitle(1, timedelta(seconds=0), timedelta(seconds=3), "这是一个足够长的中文字幕测试用于验证自动换行是否符合播放规范\nThis is source")
        self.service.process_subtitles([subtitle], bilingual=True)
        self.assertEqual(2, len(subtitle.content.split("\n")))

    def test_extends_when_safe_for_reading_speed(self):
        subtitle = srt.Subtitle(1, timedelta(seconds=0), timedelta(milliseconds=300), "这是一段需要更多阅读时间的中文字幕")
        self.service.process_subtitles([subtitle])
        self.assertGreaterEqual((subtitle.end - subtitle.start).total_seconds(), 0.9)


if __name__ == "__main__":
    unittest.main()
