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

    def test_defaults_to_fourteen_characters_per_line(self):
        self.assertEqual(14, SubtitleLayoutService({}).max_chars_per_line)

    def test_splits_overlong_cue_when_timeline_allows(self):
        subtitle = srt.Subtitle(1, timedelta(seconds=0), timedelta(seconds=4), "这是一段超过两行显示容量的中文字幕，需要自动拆成两条独立时间轴字幕以便观众阅读")
        subtitles = [subtitle]
        report = self.service.process_subtitles(subtitles)
        self.assertEqual(2, len(subtitles))
        self.assertEqual(1, report["overlong"])
        self.assertGreaterEqual(report["auto_fixed"], 1)
        for item in subtitles:
            self.assertLessEqual(len(item.content.replace("\n", "")), 32)

    def test_uses_following_gap_for_multiple_playable_cues(self):
        subtitle = srt.Subtitle(1, timedelta(seconds=0), timedelta(seconds=3), "这是一段明显超过两行容量的中文字幕，需要拆成多条并在后续足够的时间空档中分别保持合理的阅读速度")
        following = srt.Subtitle(2, timedelta(seconds=12), timedelta(seconds=13), "下一句")
        subtitles = [subtitle, following]
        self.service.process_subtitles(subtitles)
        self.assertGreaterEqual(len(subtitles), 3)
        self.assertLessEqual(subtitles[-2].end, following.start)
        for item in subtitles[:-1]:
            self.assertLessEqual((item.end - item.start).total_seconds(), 5.5)


if __name__ == "__main__":
    unittest.main()
