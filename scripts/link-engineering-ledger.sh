#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ledger_root="${PROCESS_LEDGER_ROOT:-/home/hyde/workspace/process/quant-lab}"
entry_path="${project_root}/process"

if [[ ! -d "${ledger_root}" ]]; then
  echo "process ledger root not found: ${ledger_root}" >&2
  exit 1
fi

if [[ -e "${entry_path}" && ! -L "${entry_path}" ]]; then
  echo "refusing to replace non-symlink process path: ${entry_path}" >&2
  exit 2
fi

# 使用相对路径，保持 quant-lab 与 sibling process 目录整体搬迁时仍可读。
if [[ "${ledger_root}" == "/home/hyde/workspace/process/quant-lab" ]]; then
  target="../process/quant-lab"
else
  target="${ledger_root}"
fi

ln -sfn "${target}" "${entry_path}"

if [[ ! -f "${entry_path}/STATE.md" ]]; then
  echo "process symlink created but STATE.md is not readable: ${entry_path}/STATE.md" >&2
  exit 3
fi

echo "process ledger linked: ${entry_path} -> ${target}"
