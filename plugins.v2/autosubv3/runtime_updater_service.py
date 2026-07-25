"""AutoSubv3 运行库更新器的受限文件协议。"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict


class RuntimeUpdaterService:
    """向宿主机更新器提供状态读取和手动检查请求。"""

    def __init__(self, get_data_path: Callable[[], Path]):
        self._get_data_path = get_data_path

    def get_status(self) -> Dict[str, Any]:
        """读取宿主机更新器写入的公开状态，不执行任何系统命令。"""
        runtime_dir = self._runtime_dir()
        state = self._read_json(runtime_dir / "state.json")
        installed = bool(state.get("installed"))
        return {
            "installed": installed,
            "state": state.get("state") or ("unknown" if installed else "not_installed"),
            "message": state.get("message") or (
                "尚未安装宿主机运行库更新器" if not installed else "等待宿主机更新器写入状态"
            ),
            "checked_at": state.get("checked_at") or "",
            "updated_at": state.get("updated_at") or "",
            "next_run_at": state.get("next_run_at") or "",
            "faster_whisper_version": state.get("faster_whisper_version") or "",
            "ctranslate2_version": state.get("ctranslate2_version") or "",
            "request_pending": (runtime_dir / "request.json").exists(),
            "install_hint": "管理员请按插件 README 的“运行库自动更新”章节，在 MoviePilot 宿主机执行一次安装脚本。",
        }

    def request_check(self) -> Dict[str, Any]:
        """写入固定检查请求，由宿主机更新器自行决定是否执行升级。"""
        runtime_dir = self._runtime_dir()
        runtime_dir.mkdir(parents=True, exist_ok=True)
        request_path = runtime_dir / "request.json"
        payload = {
            "action": "check",
            "requested_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "source": "plugin_ui",
        }
        temporary_path = request_path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temporary_path.replace(request_path)
        return {
            "accepted": True,
            "message": "已请求宿主机检查运行库更新；有字幕任务时会自动延后，不会中断任务。",
        }

    def _runtime_dir(self) -> Path:
        return Path(self._get_data_path()) / "runtime-updater"

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}
        return value if isinstance(value, dict) else {}
