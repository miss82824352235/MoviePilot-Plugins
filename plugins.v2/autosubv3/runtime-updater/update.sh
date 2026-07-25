#!/usr/bin/env bash
set -Eeuo pipefail

CONTAINER="${CONTAINER:?missing CONTAINER}"
PLUGIN_DATA_DIR="${PLUGIN_DATA_DIR:?missing PLUGIN_DATA_DIR}"
STATE_DIR="${STATE_DIR:-/var/lib/autosubv3-runtime-updater}"
LOG_FILE="${LOG_FILE:-/var/log/autosubv3-runtime-updater/update.log}"
REQUEST_FILE="${PLUGIN_DATA_DIR}/runtime-updater/request.json"
STATUS_FILE="${PLUGIN_DATA_DIR}/runtime-updater/state.json"
STALE_SECONDS="${STALE_SECONDS:-1800}"
RUNTIME_VENV="${RUNTIME_VENV:-/config/plugins/AutoSubv3/runtime-venv}"
mkdir -p "${STATE_DIR}" "$(dirname "${LOG_FILE}")" "$(dirname "${STATUS_FILE}")"
exec 9>"${STATE_DIR}/update.lock"
flock -n 9 || exit 0
exec >>"${LOG_FILE}" 2>&1

versions() {
  docker exec "${CONTAINER}" "${RUNTIME_VENV}/bin/python" -c 'from importlib.metadata import version; print(version("faster-whisper")); print(version("ctranslate2"))'
}

state() {
  local kind="$1" message="$2" whisper="${3:-}" ctranslate="${4:-}"
  STATUS_FILE="${STATUS_FILE}" KIND="${kind}" MESSAGE="${message}" WHISPER="${whisper}" CTRANSLATE="${ctranslate}" python3 - <<'PY'
import json
import os
import tempfile
from datetime import datetime

payload = {"installed": True, "state": os.environ["KIND"], "message": os.environ["MESSAGE"],
           "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
           "faster_whisper_version": os.environ["WHISPER"], "ctranslate2_version": os.environ["CTRANSLATE"]}
directory = os.path.dirname(os.environ["STATUS_FILE"])
with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=directory) as file:
    json.dump(payload, file, ensure_ascii=False)
    temporary_path = file.name
os.replace(temporary_path, os.environ["STATUS_FILE"])
PY
}

idle() {
  local tasks
  tasks="$(docker exec -i "${CONTAINER}" sh -s <<'INNER'
set -a; . /config/app.env; set +a
curl -fsS -H "X-API-KEY: $API_TOKEN" 'http://127.0.0.1:3001/api/v1/plugin/AutoSubv3/tasks?limit=100'
INNER
)" || return 1
  TASKS="${tasks}" STALE_SECONDS="${STALE_SECONDS}" python3 - <<'PY'
import datetime as dt
import json
import os
import sys

now = dt.datetime.now()
stale_seconds = int(os.environ["STALE_SECONDS"])
for task in json.loads(os.environ["TASKS"]).get("data", {}).get("tasks", []):
    if task.get("status") == "pending":
        sys.exit(1)
    if task.get("status") != "in_progress":
        continue
    value = task.get("progress_updated_at") or task.get("add_time")
    try:
        updated = dt.datetime.fromisoformat(value) if value else None
    except ValueError:
        updated = None
    if updated is None or (now - updated).total_seconds() < stale_seconds:
        sys.exit(1)
PY
}

if ! docker inspect "${CONTAINER}" >/dev/null 2>&1; then
  state error "未找到 MoviePilot 容器：${CONTAINER}"
  exit 1
fi
if ! docker exec "${CONTAINER}" /opt/venv/bin/python -m venv "${RUNTIME_VENV}"; then
  state error "无法创建持久化 Whisper 运行库环境"
  exit 1
fi
if ! version_output="$(versions 2>/dev/null)"; then
  version_output=""
fi
if [ -z "${version_output}" ]; then
  before=("" "")
else
  version_output="$(printf '%s' "${version_output}" | tr -d '\r')"
  readarray -t before <<<"${version_output}"
fi
if [ "${#before[@]}" -lt 2 ]; then
  before=("" "")
fi
rm -f "${REQUEST_FILE}"
if ! idle; then
  state deferred "存在排队或运行中的 AI 字幕任务，已延后检查" "${before[0]}" "${before[1]}"
  exit 0
fi
backup="${STATE_DIR}/requirements-$(date +%Y%m%d-%H%M%S).txt"
docker exec "${CONTAINER}" "${RUNTIME_VENV}/bin/pip" freeze > "${backup}"
rollback() {
  docker exec -i "${CONTAINER}" "${RUNTIME_VENV}/bin/pip" install -r - < "${backup}" || true
  state rollback "运行库自检失败，已回滚" "${before[0]}" "${before[1]}"
}
trap rollback ERR
docker exec "${CONTAINER}" "${RUNTIME_VENV}/bin/pip" install --upgrade 'faster-whisper>=1.2.1,<2'
if ! version_output="$(versions)"; then
  state error "更新后无法读取 Whisper 运行库版本" "${before[0]}" "${before[1]}"
  exit 1
fi
version_output="$(printf '%s' "${version_output}" | tr -d '\r')"
readarray -t after <<<"${version_output}"
if [ "${#after[@]}" -lt 2 ]; then
  state error "更新后 Whisper 运行库版本信息不完整" "${before[0]}" "${before[1]}"
  exit 1
fi
if [ "${before[0]}" = "${after[0]}" ] && [ "${before[1]}" = "${after[1]}" ]; then
  trap - ERR
  state up_to_date "运行库已是受支持范围内的最新版本" "${after[0]}" "${after[1]}"
  exit 0
fi
docker exec -i -e RUNTIME_VENV="${RUNTIME_VENV}" "${CONTAINER}" sh -s <<'INNER'
set -e
export HF_HOME=/config/plugins/AutoSubv3/faster-whisper-models/cache
"${RUNTIME_VENV}/bin/python" - <<'PY'
import os
from faster_whisper import WhisperModel
WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=2, num_workers=1, download_root=os.environ["HF_HOME"])
PY
INNER
if ! idle; then
  trap - ERR
  state deferred "检查后出现 AI 字幕任务，已跳过重启" "${after[0]}" "${after[1]}"
  exit 0
fi
trap - ERR
docker restart "${CONTAINER}"
state updated "运行库已更新、自检通过并在空闲时重启 MoviePilot" "${after[0]}" "${after[1]}"
