"""MKV 轨道规范化工具。

本模块只修改 Matroska 轨道头部元数据，不重新压制音视频。
目标是让 Emby、Jellyfin、Plex 以及常见播放器的音轨/字幕轨列表更易读。
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.log import logger


@dataclass
class TrackEdit:
    """单条轨道元数据修改计划。"""

    selector: str
    track_type: str
    track_id: int
    number: int
    language: str
    name: str
    default_track: Optional[bool] = None
    forced_track: Optional[bool] = None


class TrackNormalizer:
    """基于 mkvtoolnix 的 MKV 音轨/字幕轨规范化器。"""

    LANGUAGE_CODES: Dict[str, str] = {
        "und": "und",
        "heb": "heb",
        "he": "heb",
        "eng": "eng",
        "en": "eng",
        "chi": "chi",
        "zho": "chi",
        "zh": "chi",
        "cmn": "chi",
        "yue": "chi",
        "fre": "fra",
        "fra": "fra",
        "fr": "fra",
        "jpn": "jpn",
        "ja": "jpn",
        "kor": "kor",
        "ko": "kor",
        "spa": "spa",
        "es": "spa",
        "ger": "deu",
        "deu": "deu",
        "de": "deu",
        "ita": "ita",
        "it": "ita",
        "rus": "rus",
        "ru": "rus",
        "por": "por",
        "pt": "por",
        "ara": "ara",
        "cat": "cat",
        "cze": "ces",
        "ces": "ces",
        "dan": "dan",
        "dut": "nld",
        "nld": "nld",
        "fin": "fin",
        "gre": "ell",
        "ell": "ell",
        "hin": "hin",
        "hun": "hun",
        "ind": "ind",
        "nor": "nor",
        "pol": "pol",
        "swe": "swe",
        "tha": "tha",
        "tur": "tur",
        "vie": "vie",
        "fil": "fil",
        "kan": "kan",
        "mal": "mal",
        "may": "msa",
        "msa": "msa",
        "tam": "tam",
        "tel": "tel",
    }

    AUDIO_CODEC_NAMES: Dict[str, str] = {
        "DTS-HD Master Audio": "DTS-HD MA",
        "DTS-HD High Resolution Audio": "DTS-HD HRA",
        "DTS": "DTS",
        "AC-3": "Dolby Digital",
        "E-AC-3": "Dolby Digital Plus",
        "TrueHD": "TrueHD",
        "AAC": "AAC",
        "FLAC": "FLAC",
        "PCM": "PCM",
        "Opus": "Opus",
    }

    SUBTITLE_CODEC_NAMES: Dict[str, str] = {
        "HDMV PGS": "PGS",
        "SubRip/SRT": "SRT",
        "SubStationAlpha": "ASS",
        "SubStation Alpha": "ASS",
        "WebVTT": "WebVTT",
        "VobSub": "VobSub",
    }

    COMMENTARY_HINTS = (
        "commentary",
        "comment",
        "director",
        "导演",
        "评论",
        "解说",
    )

    FORCED_HINTS = (
        "forced",
        "force",
        "强制",
        "仅外语",
    )

    def __init__(self, reset_video_language: bool = True) -> None:
        """初始化轨道规范化器。"""
        self._reset_video_language = reset_video_language

    @staticmethod
    def available() -> bool:
        """判断 mkvtoolnix 命令是否可用。"""
        return bool(shutil.which("mkvmerge") and shutil.which("mkvpropedit"))

    def normalize(self, mkv_file: str | Path, dry_run: bool = False) -> List[TrackEdit]:
        """规范化指定 MKV 文件的轨道标题。"""
        path = Path(mkv_file)
        if not path.exists() or not path.is_file():
            raise RuntimeError(f"MKV 文件不存在: {path}")
        if not self.available():
            raise RuntimeError("未检测到 mkvmerge/mkvpropedit，请先安装 mkvtoolnix。")

        tracks = self._load_tracks(path)
        edits = self._build_edits(tracks)
        if not edits:
            logger.info(f"未生成轨道规范化修改: {path}")
            return []

        logger.info(
            "准备规范化 MKV 轨道: "
            f"file={path}, edits={[edit.__dict__ for edit in edits]}"
        )
        if dry_run:
            return edits

        cmd = ["mkvpropedit", path.as_posix()]
        for edit in edits:
            cmd.extend(["--edit", edit.selector])
            cmd.extend(["--set", f"name={edit.name}"])
            if edit.default_track is not None:
                cmd.extend(["--set", f"flag-default={'1' if edit.default_track else '0'}"])
            if edit.forced_track is not None:
                cmd.extend(["--set", f"flag-forced={'1' if edit.forced_track else '0'}"])
            if edit.track_type == "video" and self._reset_video_language:
                cmd.extend(["--set", "language=und"])
        self._run(cmd)
        logger.info(f"MKV 轨道规范化完成: {path}")
        return edits

    def _load_tracks(self, path: Path) -> List[dict]:
        """读取 mkvmerge JSON 轨道信息。"""
        output = self._run(["mkvmerge", "-J", path.as_posix()])
        data = json.loads(output or "{}")
        return data.get("tracks") or []

    @staticmethod
    def _run(cmd: List[str]) -> str:
        """执行命令并返回标准输出。"""
        process = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if process.returncode != 0:
            stderr = process.stderr or process.stdout or ""
            raise RuntimeError(f"命令执行失败: {' '.join(cmd)}\n{stderr[-4000:]}")
        return process.stdout or ""

    def _build_edits(self, tracks: List[dict]) -> List[TrackEdit]:
        """根据轨道信息生成修改计划。"""
        edits: List[TrackEdit] = []
        audio_seen: Dict[str, int] = {}
        subtitle_seen: Dict[str, int] = {}
        audio_index = 0
        subtitle_index = 0
        video_index = 0

        for track in tracks:
            track_type = track.get("type")
            props = track.get("properties") or {}
            track_id = int(track.get("id"))
            number = int(props.get("number") or (track_id + 1))
            selector = f"track:@{number}"

            if track_type == "video":
                video_index += 1
                if self._reset_video_language:
                    edits.append(
                        TrackEdit(
                            selector=selector,
                            track_type="video",
                            track_id=track_id,
                            number=number,
                            language="und",
                            name="",
                            default_track=bool(props.get("default_track")) or None,
                            forced_track=bool(props.get("forced_track")),
                        )
                    )
                continue

            if track_type == "audio":
                audio_index += 1
                name = self._audio_name(track, props)
                duplicate_count = audio_seen.get(name, 0) + 1
                audio_seen[name] = duplicate_count
                if duplicate_count > 1:
                    name = f"{name} #{duplicate_count}"
                edits.append(
                    TrackEdit(
                        selector=selector,
                        track_type="audio",
                        track_id=track_id,
                        number=number,
                        language=str(props.get("language") or "und"),
                        name=name,
                        default_track=None,
                        forced_track=None,
                    )
                )
                continue

            if track_type == "subtitles":
                subtitle_index += 1
                name = self._subtitle_name(track, props)
                duplicate_count = subtitle_seen.get(name, 0) + 1
                subtitle_seen[name] = duplicate_count
                if duplicate_count > 1:
                    name = f"{name} #{duplicate_count}"
                edits.append(
                    TrackEdit(
                        selector=selector,
                        track_type="subtitles",
                        track_id=track_id,
                        number=number,
                        language=str(props.get("language") or "und"),
                        name=name,
                        default_track=None,
                        forced_track=True if (bool(props.get("forced_track")) or self._is_forced(props)) else None,
                    )
                )
        return edits

    def _audio_name(self, track: dict, props: Dict[str, Any]) -> str:
        """生成音轨标题。"""
        original_title = str(props.get("track_name") or "").strip()
        language = self._audio_language_label(str(props.get("language") or "und"), original_title)
        raw_codec = str(track.get("codec") or props.get("codec_id") or original_title or "Audio")
        codec = self._audio_codec_name(raw_codec)
        channels = self._format_channels(props.get("audio_channels"))
        parts = [language]
        audio_feature = self._audio_feature_label(original_title, raw_codec)
        if audio_feature:
            parts.append(audio_feature)
        format_bits = [codec]
        if channels:
            format_bits.append(channels)
        parts.append(" ".join(format_bits).strip())
        return "-".join(part for part in parts if part).strip("-") or "Audio"

    def _subtitle_name(self, track: dict, props: Dict[str, Any]) -> str:
        """生成字幕轨标题。"""
        original_title = str(props.get("track_name") or "").strip()
        language = self._subtitle_language_label(str(props.get("language") or "und"), original_title)
        codec = self._subtitle_codec_name(str(track.get("codec") or props.get("codec_id") or "Subtitle"))
        parts = [language]
        subtitle_feature = self._subtitle_feature_label(original_title, props)
        if subtitle_feature:
            parts.append(subtitle_feature)
        parts.append(codec)
        return "-".join(part for part in parts if part).strip("-") or "Subtitle"

    def _audio_language_label(self, language: str, original_title: str = "") -> str:
        """生成音轨语言代码，优先保留国语/粤语等标签对应的语言代码。"""
        title = (original_title or "").lower()
        raw_title = original_title or ""
        if "粤" in raw_title or "cantonese" in title:
            return "chi"
        if "国语" in raw_title or "mandarin" in title or "taiwanese mandarin" in title:
            return "chi"
        return self._language_code(language)

    def _subtitle_language_label(self, language: str, original_title: str = "") -> str:
        """生成字幕语言代码，保留简体/繁体/双语的特征信息由特征段承载。"""
        return self._language_code(language)

    @staticmethod
    def _clean_qualifier_text(text: str) -> str:
        """清理轨道标题中可保留的补充说明。"""
        return " ".join((text or "").replace("_", " ").replace("-", " ").split())

    def _audio_feature_label(self, original_title: str, raw_codec: str = "") -> str:
        """仅从原始音轨标题和工具读到的编码描述提取明确短特征。"""
        title = original_title or ""
        lower = title.lower()
        codec_lower = (raw_codec or "").lower()
        features = []
        if "atmos" in lower or "atmos" in codec_lower:
            features.append("Atmos")
        if self._is_commentary({"track_name": title}):
            features.append("Commentary")
        if "compatibility" in lower or "core" in lower:
            features.append("Compatibility")
        if "directors" in lower or "director" in lower or "导评" in title:
            features.append("Director")
        if "dub" in lower or "国配" in title or "配音" in title:
            features.append("Dub")
        if "国语" in title or "mandarin" in lower:
            features.append("Mandarin")
        if "粤" in title or "cantonese" in lower:
            features.append("Cantonese")
        return "+".join(self._dedupe(features))

    def _subtitle_feature_label(self, original_title: str, props: Dict[str, Any]) -> str:
        """仅按原始字幕标题和轨道标记提取明确存在的短特征。"""
        title = original_title or ""
        lower = title.lower()
        tokens = []

        if self._is_forced(props) or "forced" in lower or "强制" in title:
            tokens.append("Forced")
        if "sdh" in lower:
            tokens.append("SDH")
        if lower.strip() == "cc" or "closed caption" in lower:
            tokens.append("CC")

        simplified = any(x in lower for x in ("chs", "simplified")) or any(x in title for x in ("简体", "简中", "简"))
        traditional = any(x in lower for x in ("cht", "traditional")) or any(x in title for x in ("繁体", "繁中", "繁"))
        english = any(x in lower for x in ("eng", "english")) or any(x in title for x in ("英",))
        bilingual = any(x in lower for x in ("chs/eng", "chs&eng", "chs-eng", "cht/eng", "cht&eng", "cht-eng", "zh&en", "zh-en", "bilingual")) or any(x in title for x in ("简英", "繁英", "中英", "双语"))
        if simplified and (bilingual or english):
            tokens.append("S&E")
        elif traditional and (bilingual or english):
            tokens.append("T&E")
        elif bilingual:
            tokens.append("Bilingual")
        elif simplified:
            tokens.append("S")
        elif traditional:
            tokens.append("T")

        if any(x in lower for x in ("tx", "styled")) or any(x in title for x in ("特效", "特效字幕")):
            tokens.append("Styled")
        if "粤" in title or "cantonese" in lower:
            tokens.append("Cantonese")
        if "国配" in title or "国语" in title or "mandarin" in lower:
            tokens.append("Mandarin")
        if "canadian" in lower or "canada" in lower:
            tokens.append("CA")
        if "latin" in lower or "brazilian" in lower:
            tokens.append("LATAM")
        if "european" in lower:
            tokens.append("EU")

        return "+".join(self._dedupe(tokens))

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        """按出现顺序去重并移除空特征。"""
        result: List[str] = []
        for item in items:
            if item and item not in result:
                result.append(item)
        return result

    @classmethod
    def _language_code(cls, language: str) -> str:
        """将语言代码归一化为简洁的三字母代码。"""
        normalized = (language or "und").lower()
        return cls.LANGUAGE_CODES.get(normalized, normalized)

    @classmethod
    def _audio_codec_name(cls, codec: str) -> str:
        """将音频编码名转换为短标题。"""
        codec_text = codec or ""
        upper = codec_text.upper()
        lower = codec_text.lower()
        if "TRUEHD" in upper and "ATMOS" in upper:
            return "TrueHD"
        if ("E-AC-3" in upper or "EAC3" in upper) and "ATMOS" in upper:
            return "DDP"
        if "TRUEHD" in upper:
            return "TrueHD"
        if "DTS-HD MASTER" in upper:
            return "DTS-HD MA"
        if "DTS-HD HIGH" in upper:
            return "DTS-HD HRA"
        if "DTS" in upper:
            return "DTS"
        if "E-AC-3" in upper or "EAC3" in upper:
            return "DDP"
        if "AC-3" in upper or "AC3" in upper:
            return "DD"
        if "AAC" in upper:
            return "AAC"
        if "FLAC" in upper:
            return "FLAC"
        if "PCM" in upper:
            return "PCM"
        return codec_text.replace("/", " ").strip() or "Audio"

    @classmethod
    def _subtitle_codec_name(cls, codec: str) -> str:
        """将字幕编码名转换为短标题。"""
        for key, value in cls.SUBTITLE_CODEC_NAMES.items():
            if key.lower() in codec.lower():
                return value
        if "PGS" in codec.upper():
            return "PGS"
        if "SRT" in codec.upper():
            return "SRT"
        if "ASS" in codec.upper():
            return "ASS"
        if "VTT" in codec.upper():
            return "VTT"
        return codec.replace("/", " ").strip() or "Subtitle"

    @staticmethod
    def _format_channels(channels: Any) -> str:
        """格式化声道数量。"""
        try:
            count = int(channels)
        except (TypeError, ValueError):
            return ""
        return {
            1: "1.0",
            2: "2.0",
            3: "2.1",
            4: "4.0",
            5: "5.0",
            6: "5.1",
            7: "6.1",
            8: "7.1",
        }.get(count, f"{count}ch")

    @classmethod
    def _is_commentary(cls, props: Dict[str, Any]) -> bool:
        """判断轨道标题是否明显表示评论音轨。"""
        title = str(props.get("track_name") or "").lower()
        return any(hint in title for hint in cls.COMMENTARY_HINTS)

    @classmethod
    def _is_forced(cls, props: Dict[str, Any]) -> bool:
        """判断字幕是否明显为强制字幕。"""
        if bool(props.get("forced_track")):
            return True
        title = str(props.get("track_name") or "").lower()
        return any(hint in title for hint in cls.FORCED_HINTS)
