---
handoff_id: "META-DEV-CR009-RUNTIME-SMOKE-REMEDIATION-2026-05-22"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest"
change_id: "CR-009"
batch_id: "CR009-BUGFIX-A"
status: "completed"
created_at: "2026-05-22T07:08:25+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e4cce-b36a-7cb3-8519-e02fec3ceb35"
  agent_name: "Ampere"
  thread_id: "019e4cce-b36a-7cb3-8519-e02fec3ceb35"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-22T07:11:25+08:00"
  completed_at: "2026-05-22T07:14:17+08:00"
result:
  cp6: "process/checks/CP6-CR009-RUNTIME-SMOKE-REMEDIATION-CODING-DONE.md"
  status: "PASS"
  tests: "uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py => 9 passed"
---

# Handoff：CR-009 真实烟测缺陷修复

## 任务目标

关闭 `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` 中暴露的两个实现缺口：

1. `hs300_index validate --run-id` 不应跨历史 run 聚合 canonical parquet 后误报 `duplicate_key`。
2. CLI 顶层需要提供正式 `revalidate` / `replay` 子命令，替代手工近似核验。

## 允许修改范围

| 路径 | 允许动作 |
|---|---|
| `market_data/cli.py` | 添加 run_id 级 canonical 路径选择、`revalidate`、`replay`。 |
| `tests/test_market_data_cli_comparison.py` | 添加或调整 CLI 离线回归。 |
| `tests/test_cr007_benchmark_calendar_backfill.py` | 仅在需要覆盖 CR007 benchmark/calendar 场景时调整。 |

## 禁止范围

- 不读取、打印或记录 `.env`、Tushare token、NAS 凭据或私有真实路径。
- 不触发真实网络。
- 不写真实 lake；测试只能使用 `tmp_path`。
- 不修改 `README.md`、`docs/USER-MANUAL.md`、`process/HLD.md`、`process/REQUIREMENTS.md`。
- 不放宽 quality gate；不得把 `duplicate_key` 改成 warn 或忽略。

## 期望实现

- 新增 helper 使 `validate` 在传入 `--run-id` 时只读取 `canonical/<dataset>/1.0/run_id=<run-id>/**/*.parquet`。
- `revalidate` 复用 validate 逻辑，但输出 `command="revalidate"`，并支持 `hs300_index` 所需参数。
- `replay` 支持 `dataset=hs300_index` 的最小 idempotency 核验：对已存在 success manifest 的同一 `run_id/batch_id/source/interface/params_hash` 返回 `status="skipped"`、`attempts=0`、`network_calls=0`、`writes=0`；缺少 success manifest 时返回 typed unavailable / replay_missing，不得联网补数。
- `hs300-backfill` 对 skipped 结果的 `network_calls` 不应再计为 1，并应输出 `attempts`，便于 QA 判定。

## 最小回归

- 构造两个不同 run、相同 `trade_date,index_code` 的 `hs300_index` canonical；指定新 run 执行 `validate --run-id` / `revalidate --run-id` 应 PASS。
- `replay` 对已存在 success manifest 返回 skipped、attempts=0、network_calls=0、writes=0，且执行前后文件列表不变。
- `python -m market_data.cli --help` 或 parser 测试能看到 `revalidate` 与 `replay`。

## 完成输出

- 代码与测试变更。
- `process/checks/CP6-CR009-RUNTIME-SMOKE-REMEDIATION-CODING-DONE.md`，包含测试命令、结果、禁止范围确认和 Agent Dispatch Evidence。
