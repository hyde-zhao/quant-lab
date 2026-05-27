---
handoff_id: "META-QA-CR007-S02-CP7-VERIFY-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-qa"
recommended_agent_name: "qa-yan"
status: "completed"
created_at: "2026-05-21T08:20:00+08:00"
workflow_id: "local_backtest"
change_id: "CR-007"
linked_change: "CR-008"
batch_id: "CR007-BATCH-A"
wave_id: "CR007-VERIFY-W2"
story_id: "CR007-S02-benchmark-calendar-backfill"
reuse_key: "meta-qa|local_backtest|CR-007|CR007-S02-benchmark-calendar-backfill|CR007-VERIFY-W2"
dispatch:
  required: true
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".codex/agents/meta-qa.toml"
  tool_name: "spawn_agent"
  agent_id: "019e47b6-1b60-7761-a79b-71b38ff2c11e"
  agent_name: "qa-yan"
  thread_id: "019e47b6-1b60-7761-a79b-71b38ff2c11e"
  spawned_at: "2026-05-21T07:29:00+08:00"
  resumed_at: ""
  completed_at: "2026-05-21T07:29:00+08:00"
  evidence: "主线程通过 spawn_agent 真实调度 meta-qa/qa-yan 执行 CR007-S02 CP7，agent_id/thread_id=019e47b6-1b60-7761-a79b-71b38ff2c11e；输出 process/checks/CP7-CR007-S02-benchmark-calendar-backfill-VERIFICATION-DONE.md，结论 PASS。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Meta-QA Handoff: CR007-S02 CP7 Verification

## 任务目标

验证 `CR007-S02-benchmark-calendar-backfill` 的 CP7。当前 S02 已由 `meta-dev/dev-zhang` 通过 `resume_agent + send_input` 完成离线实现，CP6 结论为 PASS。CP7 只验证 S02 benchmark/calendar 离线合同、reader/resolver/validation 兼容性和安全边界；不得把 CR008 或 CR007-S03/S04/S05 标记为已验证。

## 必读输入

- `process/STATE.md`
- `process/checks/CP6-CR007-S02-benchmark-calendar-backfill-CODING-DONE.md`
- `process/handoffs/META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20.md`
- `process/stories/CR007-S02-benchmark-calendar-backfill.md`
- `process/stories/CR007-S02-benchmark-calendar-backfill-LLD.md`
- `process/checks/CP5-CR007-S02-benchmark-calendar-backfill-LLD-IMPLEMENTABILITY.md`
- `checkpoints/CP5-CR007-BATCH-A-LLD-BATCH.md`
- `process/checks/CP7-CR007-S01-prices-long-horizon-backfill-planner-VERIFICATION-DONE.md`
- `process/checks/CR007-CR008-VALIDATION-STRATEGY-2026-05-21.md`
- `process/checks/CR007-CR008-DEV-CONFLICT-ANALYSIS-2026-05-21.md`
- `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md`
- `process/changes/CR-008-RESEARCH-DATA-LAYER-HARDENING-2026-05-20.md`

## 输出文件

- `process/checks/CP7-CR007-S02-benchmark-calendar-backfill-VERIFICATION-DONE.md`

输出必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果、安全确认和结论。

## 验证范围

必须覆盖：

- S02 CP6 为 PASS，且 CP6 dispatch evidence 为 `resume_agent + send_input`，agent_id/thread_id=`019e45c2-383c-7cc1-a732-ee1b7652e423`。
- `benchmark-calendar-backfill` dry-run 规划默认 `network_calls=0`、`writes=0`。
- `trade_calendar.is_open=true` 作为 benchmark coverage denominator；不得用自然日 denominator 声明通过。
- `resolve_hs300_benchmark` 的可用、缺失、coverage gap、price overlap missing、policy unconfirmed、quality failed 等结构化路径。
- `market_data/readers.py` 与 `market_data/benchmarks.py` 不导入 connector/runtime/storage，不触发 fetch/backfill。
- 与既有 HS300 CLI / benchmark reader 回归兼容。
- CR008 compatibility pending：S02 可作为 CR008 上游 benchmark/calendar contract，但不得声明 CR008 research input、proxy/real 字段拆分、PIT 或报告 metadata 已完成。

## 建议离线验证命令

可按 `process/checks/CR007-CR008-VALIDATION-STRATEGY-2026-05-21.md` 和 CP6 记录执行以下离线命令：

```bash
uv run --python 3.11 pytest -q tests/test_cr007_benchmark_calendar_backfill.py
uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py::test_hs300_index_cli_normalize_validate_and_read
uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py
```

如需补充静态 import 边界检查，只能使用仓库内离线 fixture / AST / monkeypatch，不得触发真实数据命令。

## 禁止事项

- 不批准 CR008 CP3/CP4，不进入 CR008 LLD、CP5 或实现。
- 不调度或验证 CR007-S03/S04/S05。
- 不执行真实 Tushare 抓取、真实联网 backfill、真实 lake read/write、normalize/revalidate/replay/backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取、打开、覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、Tushare token、NAS 凭据或真实私有路径。
- 不修改业务代码、测试、README、USER-MANUAL、HLD、ADR、Story Backlog、Development Plan。

## 完成标准

- `process/checks/CP7-CR007-S02-benchmark-calendar-backfill-VERIFICATION-DONE.md` 结论为 PASS / FAIL / BLOCKED 之一。
- 若 PASS，只能将 S02 推进为 `verified`；完成回填后，S03 仍需等待 CR008 CP3/CP4 approved 和文件所有权复核后才可重新判定 dev gate。
- 若 FAIL 或 BLOCKED，必须列出 BLOCKING / REQUIRED 项，并保持 S02 未 verified。
- 输出中必须记录真实 meta-qa dispatch evidence；仅有本 handoff 不足以推进 Story。
