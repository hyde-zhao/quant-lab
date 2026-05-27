---
handoff_id: "META-QA-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFY-2026-05-22"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest"
change_id: "CR-009"
issue_id: "ISSUE-002"
batch_id: "CR009-BUGFIX-B"
scope: "offline-regression-and-real-replay-resmoke"
status: "completed"
created_at: "2026-05-22T08:07:00+08:00"
authorization:
  authorized_by: "user"
  authorized_at: "2026-05-22T07:53:31+08:00"
  authorization_text: "授权真实复验"
dispatch:
  mode: "spawn_agent"
  tool_name: "spawn_agent"
  agent_id: "019e4d02-d57a-7bc1-a4d9-a54c21d3b3e7"
  agent_name: "qa-hua"
  thread_id: "019e4d02-d57a-7bc1-a4d9-a54c21d3b3e7"
  spawned_at: "2026-05-22T08:08:16+08:00"
  completed_at: "2026-05-22T08:09:37+08:00"
result:
  cp7: "process/checks/CP7-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFICATION-DONE.md"
  real_replay_check: "process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22.md"
  status: "PASS"
  tests:
    - "uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py => 11 passed"
    - "uv run --python 3.11 pytest -q tests/test_market_data_runtime_storage.py => 15 passed"
    - "uv run --python 3.11 python -m compileall -q market_data tests/test_market_data_cli_comparison.py => exit 0"
    - "real replay without --lake-root => status=skipped, attempts=0, network_calls=0, writes=0"
---

# Handoff：CR-009 replay lake-root 合同修复验证

## 验证目标

验证 `ISSUE-002` 修复是否关闭：`replay` 子命令在未显式传入 `--lake-root` 时，能够通过 `MARKET_DATA_LAKE_ROOT` 解析真实 lake root，并在已有 success manifest 时返回 `skipped`、零网络、零写入。

## 输入

| 输入 | 路径 |
|---|---|
| ISSUE | `issues/ISSUE-002.md` |
| CP6 | `process/checks/CP6-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-CODING-DONE.md` |
| 上次真实复验 FAIL | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md` |
| 实现文件 | `market_data/cli.py` |
| 测试文件 | `tests/test_market_data_cli_comparison.py` |

## 必须执行的离线验证命令

```bash
uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py
uv run --python 3.11 pytest -q tests/test_market_data_runtime_storage.py
uv run --python 3.11 python -m compileall -q market_data tests/test_market_data_cli_comparison.py
```

## 必须执行的真实 replay 复验命令

沿用用户已授权的真实小窗口，不扩大范围。统一前缀：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli
```

执行：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli replay --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522
```

## 通过口径

| 检查项 | 通过条件 |
|---|---|
| 离线回归 | 三条离线命令全部 PASS。 |
| parser 合同 | `replay` 未传 `--lake-root` 不再被 argparse 拒绝。 |
| 真实 replay | 退出码 0，输出 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`。 |
| 安全边界 | 不读取、打印、复制或写入 `.env` 内容；检查结果脱敏真实 lake root、token、NAS/私有路径。 |

## 写入范围

- `process/checks/CP7-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFICATION-DONE.md`
- `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22.md`

不得修改实现代码、测试代码、CR、STATE、handoff 或任何真实数据文件。
