---
handoff_id: "META-DEV-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-2026-05-22"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest"
change_id: "CR-009"
issue_id: "ISSUE-002"
batch_id: "CR009-BUGFIX-B"
status: "completed"
created_at: "2026-05-22T08:00:33+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "spawn_agent"
  agent_id: "019e4cfd-7c50-77a2-b933-2f0541ffff63"
  agent_name: "dev-lv"
  thread_id: "019e4cfd-7c50-77a2-b933-2f0541ffff63"
  spawned_at: "2026-05-22T08:02:25+08:00"
  completed_at: "2026-05-22T08:05:23+08:00"
result:
  cp6: "process/checks/CP6-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-CODING-DONE.md"
  status: "PASS"
  tests:
    - "uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py => 11 passed"
    - "uv run --python 3.11 pytest -q tests/test_market_data_runtime_storage.py => 15 passed"
    - "uv run --python 3.11 python -m compileall -q market_data tests/test_market_data_cli_comparison.py => exit 0"
---

# Handoff：CR-009 replay lake-root 合同修复

## 修复目标

关闭 `ISSUE-002`：`replay` 子命令在未显式传入 `--lake-root` 时，应与 `validate` / `revalidate` / `read` 一样通过 `MARKET_DATA_LAKE_ROOT` 解析 lake root，满足真实复验 handoff 指定的命令合同。

## 输入

| 输入 | 路径 |
|---|---|
| ISSUE | `issues/ISSUE-002.md` |
| CR | `process/changes/CR-009-HS300-RUNTIME-SMOKE-REMEDIATION-2026-05-22.md` |
| 真实复验 FAIL | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md` |
| 实现文件 | `market_data/cli.py` |
| 测试文件 | `tests/test_market_data_cli_comparison.py` |

## 允许写入范围

- `market_data/cli.py`
- `tests/test_market_data_cli_comparison.py`
- `process/checks/CP6-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-CODING-DONE.md`

## 要求

1. 让 `replay.add_argument("--lake-root")` 不再由 argparse 强制 required。
2. 保持 `cmd_replay()` 使用 `_resolve_lake_root(args)`，因此仍允许显式 `--lake-root` 覆盖环境变量。
3. 补充离线回归：未传 `--lake-root`、仅设置 `MARKET_DATA_LAKE_ROOT` 时，`replay` 可读取 success manifest 并返回 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`。
4. 不触发真实网络、不读取 `.env`、不写真实 lake。
5. 不放宽 replay 缺失 manifest 的失败逻辑。

## 建议验证命令

```bash
uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py
uv run --python 3.11 pytest -q tests/test_market_data_runtime_storage.py
uv run --python 3.11 python -m compileall -q market_data tests/test_market_data_cli_comparison.py
```

## 输出

写入 `process/checks/CP6-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-CODING-DONE.md`，包含 Entry Criteria、Agent Dispatch Evidence、Checklist、Exit Criteria、Deliverables 和验证命令结果。
