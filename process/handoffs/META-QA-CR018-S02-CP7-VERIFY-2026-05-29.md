---
handoff_id: "META-QA-CR018-S02-CP7-VERIFY-2026-05-29"
from: "meta-po"
to: "meta-qa"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill"
wave_id: "CR018-W2-P0-P1-READINESS"
status: "completed-closed"
created_at: "2026-05-29T09:33:38+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e715e-3443-7c10-a04e-07e9b87b92bb"
  thread_id: "019e715e-3443-7c10-a04e-07e9b87b92bb"
  agent_name: "qa-wei"
  spawned_at: "2026-05-29T09:34:23+08:00"
  completed_at: "2026-05-29T09:36:20+08:00"
  closed_at: "2026-05-29T09:39:10+08:00"
---

# META-QA Handoff: CR018-S02 CP7 Verification

## Mission

独立验证 `CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill` 的 CP6 交付是否满足 LLD、Story 和 CP5 已批准边界。

本验证只允许离线 / fixture / dry-run 检查；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill.md` |
| LLD | `process/stories/CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-LLD.md` |
| CP6 | `process/checks/CP6-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR018-S02-IMPLEMENT-2026-05-29.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| S01 CP7 | `process/checks/CP7-CR018-S01-production-current-truth-definition-and-dataset-groups-VERIFICATION-DONE.md` |
| S03 CP7 | `process/checks/CP7-CR018-S03-real-benchmark-index-components-weights-backfill-VERIFICATION-DONE.md` |
| S04 CP7 | `process/checks/CP7-CR018-S04-industry-market-cap-liquidity-and-exposure-data-VERIFICATION-DONE.md` |

## Verification Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| required-read | `market_data/contracts.py` | 验证 PIT / lifecycle / tradability constants、reason codes、blocked claims 和 counters。 |
| required-read | `market_data/validation.py` | 验证 PIT / lifecycle / tradability fail-closed helpers。 |
| required-read | `market_data/readers.py` | 验证 readiness reader 默认 published-only，不扫描 candidate / unpublished lake。 |
| required-read | `tests/test_cr018_pit_tradability_readiness.py` | 验证 9 个 fixture-only 合同测试覆盖 LLD §10。 |
| write | `process/checks/CP7-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-VERIFICATION-DONE.md` | 仅写 CP7 验证结果。 |

禁止修改业务代码、Story、STATE、STORY-STATUS、DEVELOPMENT-PLAN、`pyproject.toml`、`uv.lock`、`.env`、真实 lake、provider connector、catalog current pointer 或 QMT 入口。

## Required Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py
```

建议额外运行：

```bash
git diff --check -- market_data/contracts.py market_data/validation.py market_data/readers.py tests/test_cr018_pit_tradability_readiness.py process/checks/CP6-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-CODING-DONE.md
```

## CP7 Output Requirements

CP7 文件必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果、真实操作计数和结论。

验证通过时结论写 `PASS`；发现阻断项时结论写 `FAIL`，并列出可回修的最小问题。
