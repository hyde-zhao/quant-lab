#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/sync_data_lake_to_nas.sh [push|pull] [lake|research|all] [--execute] [--delete] [--env-file PATH]

Default behavior is a dry-run push of all configured data roots to NAS.

Required environment:
  MARKET_DATA_LAKE_ROOT
  QUANT_LAB_RESEARCH_ROOT
  MARKET_DATA_NAS_IP
  MARKET_DATA_NAS_RSYNC_MODE=daemon
  MARKET_DATA_NAS_RSYNC_MODULE
  MARKET_DATA_NAS_PASSWORD

NAS target environment:
  MARKET_DATA_NAS_RSYNC_LAKE_TARGET
  MARKET_DATA_NAS_RSYNC_RESEARCH_TARGET
  QUANT_LAB_RESEARCH_EXTRA_SOURCES
USAGE
}

direction="push"
scope="all"
execute="false"
delete_flag=""
env_file=".env"

while [ "$#" -gt 0 ]; do
  case "$1" in
    push|pull)
      direction="$1"
      ;;
    lake|research|all)
      scope="$1"
      ;;
    --execute)
      execute="true"
      ;;
    --delete)
      delete_flag="true"
      ;;
    --env-file)
      shift
      env_file="${1:-}"
      if [ -z "$env_file" ]; then
        echo "missing value for --env-file" >&2
        exit 2
      fi
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [ -f "$env_file" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  set +a
fi

if [ -z "$delete_flag" ]; then
  delete_flag="${MARKET_DATA_NAS_RSYNC_DELETE:-false}"
fi

local_root="${MARKET_DATA_LAKE_ROOT:-/home/hyde/data/quant-lab/lake}"
research_root="${QUANT_LAB_RESEARCH_ROOT:-/home/hyde/data/quant-lab/research}"
research_extra_sources="${QUANT_LAB_RESEARCH_EXTRA_SOURCES:-reports runs notebooks/outputs}"
nas_ip="${MARKET_DATA_NAS_IP:-}"
nas_user="${MARKET_DATA_NAS_USERNAME:-}"
rsync_mode="${MARKET_DATA_NAS_RSYNC_MODE:-daemon}"
rsync_port="${MARKET_DATA_NAS_RSYNC_PORT:-873}"
lake_target="${MARKET_DATA_NAS_RSYNC_LAKE_TARGET:-${MARKET_DATA_NAS_RSYNC_TARGET:-/lake}}"
research_target="${MARKET_DATA_NAS_RSYNC_RESEARCH_TARGET:-/research}"
rsync_module="${MARKET_DATA_NAS_RSYNC_MODULE:-}"

if [ -z "$nas_ip" ]; then
  echo "MARKET_DATA_NAS_IP is required" >&2
  exit 2
fi
rsync_args=(-aH --human-readable --info=stats2,progress2 --exclude "*.tmp" --exclude ".quant-lab-write-test-*")
if [ "$execute" != "true" ]; then
  rsync_args+=(--dry-run)
fi
if [ "$delete_flag" = "true" ]; then
  rsync_args+=(--delete)
fi

if [ "$rsync_mode" != "daemon" ]; then
  echo "unsupported MARKET_DATA_NAS_RSYNC_MODE: $rsync_mode; this script is configured for daemon mode" >&2
  exit 2
fi
if [ -z "$rsync_module" ]; then
  echo "MARKET_DATA_NAS_RSYNC_MODULE is required when MARKET_DATA_NAS_RSYNC_MODE=daemon" >&2
  exit 2
fi

export RSYNC_PASSWORD="${MARKET_DATA_NAS_PASSWORD:-}"
if [ -n "$rsync_port" ]; then
  rsync_args+=(--port "$rsync_port")
fi

echo "direction=$direction"
echo "scope=$scope"
echo "execute=$execute"
echo "delete=$delete_flag"
echo "rsync_mode=$rsync_mode"

remote_base="${nas_ip}::${rsync_module}"
if [ -n "$nas_user" ]; then
  remote_base="${nas_user}@${remote_base}"
fi

sync_one() {
  local label="$1"
  local local_dir="$2"
  local remote_dir="$3"
  local source_path
  local target_path

  if [ "$direction" = "push" ]; then
    if [ ! -d "$local_dir" ]; then
      echo "local $label root does not exist: $local_dir" >&2
      echo "create it first, for example: mkdir -p '$local_dir'" >&2
      exit 2
    fi
    source_path="${local_dir%/}/"
    target_path="${remote_base}${remote_dir%/}/"
  else
    source_path="${remote_base}${remote_dir%/}/"
    target_path="${local_dir%/}/"
    mkdir -p "$local_dir"
  fi

  echo "sync_target=$label"
  echo "local_root=$local_dir"
  rsync "${rsync_args[@]}" "$source_path" "$target_path"
}

sync_research() {
  sync_one "research" "$research_root" "$research_target"

  if [ "$direction" != "push" ]; then
    return
  fi

  for extra_source in $research_extra_sources; do
    if [ -d "$extra_source" ]; then
      case "$extra_source" in
        reports)
          sync_one "research-reports" "$extra_source" "${research_target%/}/reports"
          ;;
        runs)
          sync_one "research-runs" "$extra_source" "${research_target%/}/runs"
          ;;
        notebooks/outputs)
          sync_one "research-notebooks" "$extra_source" "${research_target%/}/notebooks/outputs"
          ;;
        *)
          safe_name=$(printf "%s" "$extra_source" | tr "/" "_")
          sync_one "research-extra-${safe_name}" "$extra_source" "${research_target%/}/extra/${safe_name}"
          ;;
      esac
    fi
  done
}

case "$scope" in
  lake)
    sync_one "lake" "$local_root" "$lake_target"
    ;;
  research)
    sync_research
    ;;
  all)
    sync_one "lake" "$local_root" "$lake_target"
    sync_research
    ;;
esac
