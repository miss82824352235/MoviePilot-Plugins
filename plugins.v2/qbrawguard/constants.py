"""
QBRawGuard 常量与默认配置模块。

职责：
1. 集中维护插件默认配置、标题预检提示词、原盘结构匹配规则等常量。
2. 不访问 MoviePilot 运行时对象，不操作下载器，不执行清理逻辑。
3. 为 AI 和人工维护提供稳定的配置入口，避免常量散落在主入口文件中。
"""

from typing import Dict, Tuple


PLUGIN_VERSION = "2.8.1"

TITLE_HINTS: Tuple[str, ...] = (
    "bdmv", "certificate", "video_ts", "audio_ts", "hvdvd_ts",
    ".iso", ".img", ".nrg",
    "complete.bluray", "complete.blu-ray", "complete_uhd",
    "bdiso", "bd25", "bd50",
    "uhd.bluray", "uhd.blu-ray", "uhd bluray", "uhd_bluray",
    "blu-ray", "full.disc",
    "-mteam", "-hds", "-hdsky", "-chdbits", "-52pt", "-pter",
    "thor@hds", "pete@hds", "blu-ray.diy", "bluray.diy",
    "blu-ray.avc", "bluray.avc", "bluray.remux", "blu-ray.remux",
)

DEFAULT_PATTERNS = r"""# Blu-ray / UHD Blu-ray / 3D Blu-ray 原盘
(?i)(^|[/\\])(BDMV|CERTIFICATE|AACS)([/\\]|$)
(?i)(^|[/\\])BDMV[/\\](BACKUP|PLAYLIST|CLIPINF|STREAM|AUXDATA|BDJO|JAR|META)([/\\]|$)
(?i)(^|[/\\])BDMV[/\\](index|MovieObject)\.bdmv$
(?i)\.(bdmv|mpls|clpi)$
# m2ts/ssif 需 BDMV 路径上下文，避免误判 WEB-DL 的 m2ts 流（HBO Max 等流媒体底层用 MPEG-TS/m2ts 封装）
(?i)(^|[/\\])BDMV[/\\].*\.(m2ts|ssif)$
# DVD / HD DVD 原盘
(?i)(^|[/\\])(VIDEO_TS|AUDIO_TS|HVDVD_TS)([/\\]|$)
(?i)(^|[/\\])VIDEO_TS[/\\].*\.(ifo|bup|vob)$
(?i)(^|[/\\])HVDVD_TS[/\\].*\.(evo|ifo|bup|map|xpl)$
# VCD / SVCD 原盘
(?i)(^|[/\\])(VCD|SVCD|MPEGAV|SEGMENT|EXT)([/\\]|$)
(?i)(^|[/\\])(VCD|SVCD|MPEGAV)[/\\].*\.(dat|mpg|mpeg)$
# 光盘镜像、分卷镜像、镜像描述/索引文件
(?i)\.(iso|img|nrg|mdf|mds|ccd|cue|bin|toast|udf|dmg|isz|cdi|b5t|b6t|bwt|sub|dvdmedia)$
(?i)\.i\d{2}$
"""

CONFIG_DEFAULTS: Dict[str, object] = {
    "enabled": False,
    "fast_scan_enabled": True,
    "downloaders": [],
    "interval": 2,
    "action": "stop",
    "tag": "原盘拦截",
    "include_completed": True,
    "retry_failed": True,
    "notify": True,
    "notify_type": "Agent",
    "alert_image": "https://cdn-icons-png.flaticon.com/512/564/564619.png",
    "test_title": "阿凡达：火与烬 (2025)",
    "test_subtitle": "Avatar Fire and Ash 2025 2160p UHD Blu-ray DoVi HDR10 HEVC TrueHD 7.1-Thor@HDSky",
    "test_site": "馒头",
    "test_seeders": "111",
    "test_tags": "中字 4k 中配 hdr10 DoVi",
    "test_format": "光盘镜像文件",
    "test_message": (
        "站点：馒头\n质量：UHD HDR10 DoVi 2160p\n大小：92.61G\n"
        "种子：Avatar Fire and Ash 2025 2160p UHD Blu-ray DoVi HDR10 HEVC TrueHD 7.1-Thor@HDSky\n"
        "发布时间：2026-06-02 06:03:02\n做种数：111\n促销：50%\nHit&Run：否\n"
        "标签：中字 4k 中配 hdr10 DoVi\n"
        "描述：阿凡达：火与烬 / 阿凡达3 / 阿凡达3：带种者 / 阿凡达3：火与灰 / 阿凡达3：火与烬"
        " 【UHD原盘 DIY国语DTS配音 官译简繁粤/双语字幕】"
    ),
    "patterns": "",
}
