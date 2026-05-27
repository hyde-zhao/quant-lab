---
handoff_id: "META-QA-CR009-RUNTIME-SMOKE-REMEDIATION-VERIFY-2026-05-22"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest"
change_id: "CR-009"
batch_id: "CR009-BUGFIX-A"
status: "completed"
created_at: "2026-05-22T07:16:10+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e4cd4-02de-7353-9a08-96b6aa5e948f"
  agent_name: "qa-shi"
  thread_id: "019e4cd4-02de-7353-9a08-96b6aa5e948f"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-22T07:17:07+08:00"
  completed_at: "2026-05-22T07:19:51+08:00"
result:
  cp7: "process/checks/CP7-CR009-RUNTIME-SMOKE-REMEDIATION-VERIFICATION-DONE.md"
  status: "PASS"
  tests:
    - "uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py => 9 passed"
    - "uv run --python 3.11 pytest -q tests/test_cr007_benchmark_calendar_backfill.py tests/test_market_data_hs300_benchmark.py tests/test_market_data_tushare_datasets.py tests/test_market_data_runtime_storage.py => 35 passed"
    - "uv run --python 3.11 python -m compileall -q market_data tests/test_market_data_cli_comparison.py => exit 0"
---

# Handoff：CR-009 CP7 验证

## 验证目标

独立验证 `CR-009` 对真实 Tushare 烟测缺陷的离线修复是否成立：

- `validate --run-id` 不再跨 run 误报 `hs300_index duplicate_key`。
- `revalidate` 子命令可用，并保持零网络、零 canonical 写入。
- `replay` 子命令只做 idempotency 核验，已存在 success manifest 时返回 skipped/attempts=0/network_calls=0/writes=0，且不新增文件。
- `hs300-backfill` skipped 统计输出可用于 QA 判定。

## 输入

| 输入 | 路径 |
|---|---|
| CR | `process/changes/CR-009-HS300-RUNTIME-SMOKE-REMEDIATION-2026-05-22.md` |
| ISSUE | `issues/ISSUE-001.md` |
| 失败基线 | `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` |
| CP6 | `process/checks/CP6-CR009-RUNTIME-SMOKE-REMEDIATION-CODING-DONE.md` |
| 实现文件 | `market_data/cli.py` |
| 测试文件 | `tests/test_market_data_cli_comparison.py` |

## 建议验证命令

```bash
uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py
uv run --python 3.11 pytest -q tests/test_cr007_benchmark_calendar_backfill.py tests/test_market_data_hs300_benchmark.py tests/test_market_data_tushare_datasets.py tests/test_market_data_runtime_storage.py
uv run --python 3.11 python -m compileall -q market_data tests/test_market_data_cli_comparison.py
```

## 禁止范围

- 不读取、打印或记录 `.env`、Tushare token、NAS 凭据或私有真实路径。
- 不触发真实网络。
- 不写真实 lake；验证只能使用 `tmp_path` 或仓库内离线测试。
- 不修改实现代码；若发现问题，写 CP7 FAIL 并说明复现命令。
- 不覆盖原始 FAIL 报告 `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md`。

## 输出

- `process/checks/CP7-CR009-RUNTIME-SMOKE-REMEDIATION-VERIFICATION-DONE.md`
- 若验证 PASS，说明是否仍需要真实 Tushare 小窗口复验。
