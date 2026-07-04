"""
QBRawGuard 通知构造模块。

职责：
1. 维护通知类型映射、原盘格式归纳、脱敏命中依据和下载通知样式正文构造。
2. 不发送通知，不读取下载器，不删除文件；发送动作仍由插件入口调用 post_message 完成。
3. 通知正文只展示格式依据，不暴露 hash 和真实绝对路径。
"""

from typing import Any, Dict, List

from app.schemas.types import NotificationType


def notification_type(value: Any) -> NotificationType:
    """将配置中的通知场景名称映射为 MoviePilot NotificationType。"""
    mapping = {
        "Download": NotificationType.Download, "资源下载": NotificationType.Download,
        "Organize": NotificationType.Organize, "整理入库": NotificationType.Organize,
        "Plugin": NotificationType.Plugin, "插件": NotificationType.Plugin,
        "Agent": NotificationType.Agent, "智能体": NotificationType.Agent,
        "Other": NotificationType.Other, "其它": NotificationType.Other,
    }
    return mapping.get(value, NotificationType.Agent)


def detect_format(matched: List[str]) -> str:
    """根据真实命中文件路径归纳 Emby 不友好的原盘格式。"""
    text = " ".join(matched or []).lower()
    if "bdmv" in text or "certificate" in text:
        return "Blu-ray/UHD Blu-ray 原盘结构（BDMV/CERTIFICATE）"
    if "video_ts" in text or ".ifo" in text or ".vob" in text:
        return "DVD 原盘结构（VIDEO_TS）"
    if any(x in text for x in (".iso", ".img", ".nrg", ".mdf", ".mds", ".cue", ".bin")):
        return "光盘镜像文件"
    return "Emby 可能无法直接识别的原盘结构"


def safe_format_hint(path: str) -> str:
    """只返回格式层面的脱敏命中依据，不暴露真实路径。"""
    lower = str(path).lower()
    for key, label in (
        ("bdmv", "BDMV 蓝光目录"), ("certificate", "CERTIFICATE 蓝光证书目录"),
        ("video_ts", "VIDEO_TS DVD目录"), ("hvdvd_ts", "HVDVD_TS HD-DVD目录"),
        (".iso", "ISO 光盘镜像"), (".img", "IMG 光盘镜像"), (".nrg", "NRG 光盘镜像"),
        (".mdf", "MDF/MDS 光盘镜像"), (".cue", "CUE/BIN 镜像索引"), (".m2ts", "M2TS 原盘流文件"),
    ):
        if key in lower:
            return label
    return "原盘结构特征"


def build_download_style_notice(
    name: str,
    matched: List[str],
    action: str,
    torrent_info: Dict[str, str],
    extra: str = "",
    fmt: str = "",
    fallback_tag: str = "",
) -> str:
    """构建接近 MoviePilot 下载通知的原盘拦截通知正文。"""
    format_hint = fmt or detect_format(matched)
    action_label = "删除" if action == "delete" else "停止下载"
    lines: List[str] = []
    if extra:
        for line in str(extra).splitlines():
            line = line.strip()
            if line:
                lines.append(line)

    def add(label: str, value: Any) -> None:
        value = str(value or "").strip()
        if value and not any(x.startswith(f"{label}：") for x in lines):
            lines.append(f"{label}：{value}")

    add("站点", torrent_info.get("site"))
    add("质量", torrent_info.get("quality"))
    add("大小", torrent_info.get("size"))
    add("种子", torrent_info.get("torrent_title") or name)
    add("发布时间", torrent_info.get("pubdate"))
    add("做种数", torrent_info.get("seeders"))
    add("促销", torrent_info.get("promotion"))
    add("Hit&Run", torrent_info.get("hit_and_run"))
    add("标签", torrent_info.get("tags") or fallback_tag)
    add("描述", torrent_info.get("description"))
    lines.append(f"判定格式：{format_hint}")
    if matched:
        lines.append("判定依据：" + "、".join(safe_format_hint(x) for x in matched[:3]))
    lines.append(f"处理动作：{action_label}")
    return "\n".join(lines)
