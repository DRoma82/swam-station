#!/usr/bin/env bash
set -euo pipefail

# Manual one-copy backup for Docker app state.
# Mirrors ./apps/ to /mnt/seagate/homelab/apps/ and overwrites the prior copy.

COMPOSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${COMPOSE_DIR}/apps/"
DEST_ROOT="/mnt/seagate/homelab"
DEST="${DEST_ROOT}/apps/"
LOCK="/run/backup-apps-to-seagate.lock"
STOP_SERVICES=1
DRY_RUN=0

if [[ "${EUID}" -ne 0 ]]; then
  exec sudo -- "$0" "$@"
fi

usage() {
  cat <<'USAGE'
Usage: ./backup-apps-to-seagate.sh [--live] [--dry-run]

Mirrors /home/danny/docker/apps/ to /mnt/seagate/homelab/apps/.
The destination is overwritten to match the source, including deletions.

Options:
  --live     Do not stop Docker Compose services before copying.
             Faster/no downtime, but less consistent for database files.
  --dry-run  Show what rsync would do without changing the destination.
  -h, --help Show this help.
USAGE
}

while (($#)); do
  case "$1" in
    --live)
      STOP_SERVICES=0
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

for cmd in docker findmnt flock rsync; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $cmd" >&2
    exit 1
  fi
done

if [[ ! -f "${COMPOSE_DIR}/docker-compose.yaml" ]]; then
  echo "ERROR: docker-compose.yaml not found in ${COMPOSE_DIR}" >&2
  exit 1
fi

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: source directory does not exist: $SRC" >&2
  exit 1
fi

if [[ ! -d "$DEST_ROOT" ]] || ! findmnt -T "$DEST_ROOT" >/dev/null 2>&1; then
  echo "ERROR: ${DEST_ROOT} is not mounted; refusing to write backup" >&2
  exit 1
fi

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "ERROR: another backup is already running" >&2
  exit 1
fi

mkdir -p "$DEST"
cd "$COMPOSE_DIR"

mapfile -t running_services < <(docker compose ps --services --filter status=running)
services_stopped=0

cleanup() {
  local status=$?
  if [[ "$services_stopped" -eq 1 && "${#running_services[@]}" -gt 0 ]]; then
    echo "Restarting previously running Docker Compose services..."
    docker compose start "${running_services[@]}" || true
  fi
  exit "$status"
}
trap cleanup EXIT

if [[ "$STOP_SERVICES" -eq 1 && "${#running_services[@]}" -gt 0 ]]; then
  echo "Stopping currently running Docker Compose services for a consistent copy..."
  docker compose stop "${running_services[@]}"
  services_stopped=1
elif [[ "$STOP_SERVICES" -eq 0 ]]; then
  echo "Running live backup without stopping services. Database files may be inconsistent."
fi

rsync_args=(
  -aH
  --numeric-ids
  --delete
  --info=progress2,stats2
)

if [[ "$DRY_RUN" -eq 1 ]]; then
  rsync_args+=(--dry-run)
fi

echo "Mirroring ${SRC} -> ${DEST}"
rsync "${rsync_args[@]}" "$SRC" "$DEST"

if [[ "$services_stopped" -eq 1 && "${#running_services[@]}" -gt 0 ]]; then
  echo "Restarting previously running Docker Compose services..."
  docker compose start "${running_services[@]}"
  services_stopped=0
fi

trap - EXIT

echo "Backup complete: ${DEST}"
