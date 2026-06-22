#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ledger_root="${PROCESS_LEDGER_ROOT:-/home/hyde/workspace/meta-flow-artifacts/process/quant-lab}"
entry_path="${project_root}/process"
docs_root="${ledger_root}/docs"

if [[ ! -d "${ledger_root}" ]]; then
  echo "process ledger root not found: ${ledger_root}" >&2
  exit 1
fi

if [[ -e "${entry_path}" && ! -L "${entry_path}" ]]; then
  echo "refusing to replace non-symlink process path: ${entry_path}" >&2
  exit 2
fi

# 使用相对路径，保持 quant-lab 与 sibling artifact 目录整体搬迁时仍可读。
if [[ "${ledger_root}" == "/home/hyde/workspace/meta-flow-artifacts/process/quant-lab" ]]; then
  target="../meta-flow-artifacts/process/quant-lab"
else
  target="${ledger_root}"
fi

link_path() {
  local path="$1"
  local target="$2"

  if [[ -e "${path}" && ! -L "${path}" ]]; then
    echo "refusing to replace non-symlink path: ${path}" >&2
    exit 2
  fi

  ln -sfn "${target}" "${path}"
}

link_path "${entry_path}" "${target}"

if [[ ! -f "${entry_path}/STATE.md" ]]; then
  echo "process symlink created but STATE.md is not readable: ${entry_path}/STATE.md" >&2
  exit 3
fi

if [[ ! -f "${entry_path}/.meta-flow-process.yaml" ]]; then
  echo "process metadata is not readable: ${entry_path}/.meta-flow-process.yaml" >&2
  exit 4
fi

if [[ -d "${docs_root}" ]]; then
  if [[ "${ledger_root}" == "/home/hyde/workspace/meta-flow-artifacts/process/quant-lab" ]]; then
    design_target="../../meta-flow-artifacts/process/quant-lab/docs/design"
    features_target="../../meta-flow-artifacts/process/quant-lab/docs/features"
    quality_target="../../meta-flow-artifacts/process/quant-lab/docs/quality"
    checkpoints_target="../meta-flow-artifacts/process/quant-lab/checkpoints"
    release_prefix="../../../meta-flow-artifacts/process/quant-lab/docs/release"
  else
    design_target="${docs_root}/design"
    features_target="${docs_root}/features"
    quality_target="${docs_root}/quality"
    checkpoints_target="${ledger_root}/checkpoints"
    release_prefix="${docs_root}/release"
  fi

  link_path "${project_root}/docs/design" "${design_target}"
  link_path "${project_root}/docs/features" "${features_target}"
  link_path "${project_root}/docs/quality" "${quality_target}"
  link_path "${project_root}/checkpoints" "${checkpoints_target}"

  mkdir -p "${project_root}/docs/release"
  find "${docs_root}/release" -maxdepth 1 -type f -printf '%f\n' | sort | while read -r name; do
    case "${name}" in
      RELEASE-NOTES.md|DEPLOY-CHECKLIST.md|ROLLBACK.md|MIGRATION.md|FEEDBACK.md) continue ;;
    esac

    path="${project_root}/docs/release/${name}"
    if [[ -e "${path}" && ! -L "${path}" ]]; then
      echo "refusing to replace non-symlink release path: ${path}" >&2
      exit 2
    fi
    ln -sfn "${release_prefix}/${name}" "${path}"
  done
fi

echo "process ledger linked: ${entry_path} -> ${target}"
