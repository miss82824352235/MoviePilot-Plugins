#!/usr/bin/env bash
set -Eeuo pipefail
usage() { echo 'Usage: sudo bash install.sh --container moviepilot-v2 --data-dir /host/config/plugins/AutoSubv3'; }
container=""
plugin_data_dir=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --container) container="$2"; shift 2 ;;
    --data-dir) plugin_data_dir="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
[ "$(id -u)" -eq 0 ] || { echo 'Please run as root with sudo.' >&2; exit 1; }
[ -n "${container}" ] && [ -n "${plugin_data_dir}" ] || { usage >&2; exit 2; }
docker inspect "${container}" >/dev/null 2>&1 || { echo "MoviePilot container not found: ${container}" >&2; exit 1; }
source_dir="$(cd "$(dirname "$0")" && pwd)"
install_dir="/usr/local/lib/autosubv3-runtime-updater"
mkdir -p "${install_dir}" "${plugin_data_dir}/runtime-updater" /var/lib/autosubv3-runtime-updater /var/log/autosubv3-runtime-updater
install -m 0755 "${source_dir}/update.sh" "${install_dir}/update.sh"
printf 'CONTAINER=%s\nPLUGIN_DATA_DIR=%s\n' "${container}" "${plugin_data_dir}" > /etc/default/autosubv3-runtime-updater
install -m 0644 "${source_dir}/autosubv3-runtime-update.service" /etc/systemd/system/autosubv3-runtime-update.service
install -m 0644 "${source_dir}/autosubv3-runtime-update.timer" /etc/systemd/system/autosubv3-runtime-update.timer
cat > /etc/systemd/system/autosubv3-runtime-update-request.path <<EOF
[Unit]
Description=Watch for AutoSubv3 manual runtime update requests
[Path]
PathChanged=${plugin_data_dir}/runtime-updater/request.json
Unit=autosubv3-runtime-update.service
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now autosubv3-runtime-update.timer autosubv3-runtime-update-request.path
systemctl start autosubv3-runtime-update.service
echo 'AutoSubv3 runtime updater installed.'

