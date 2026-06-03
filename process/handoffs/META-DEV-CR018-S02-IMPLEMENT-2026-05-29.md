---
handoff_id: "META-DEV-CR018-S02-IMPLEMENT-2026-05-29"
from: "meta-po"
to: "meta-dev"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill"
wave_id: "CR018-W2-P0-P1-READINESS"
status: "completed-closed"
created_at: "2026-05-29T09:20:34+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7152-23c8-7b42-b4e5-29bb8c6be49b"
  thread_id: "019e7152-23c8-7b42-b4e5-29bb8c6be49b"
  agent_name: "dev-shi"
  spawned_at: "2026-05-29T09:21:13+08:00"
  completed_at: "2026-05-29T09:33:00+08:00"
  closed_at: "2026-05-29T09:33:17+08:00"
---

# META-DEV Handoff: CR018-S02 Implementation

## Mission

实现 `CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill` 的 PIT / lifecycle / ST / suspend / trade_status / prices_limit readiness 合同。

S01、S03、S04 已 verified，CP5 已 approved。本 Story 只允许受控离线 / fixture / dry-run 实现；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill.md` |
| LLD | `process/stories/CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| S01 CP7 | `process/checks/CP7-CR018-S01-production-current-truth-definition-and-dataset-groups-VERIFICATION-DONE.md` |
| S03 CP7 | `process/checks/CP7-CR018-S03-real-benchmark-index-components-weights-backfill-VERIFICATION-DONE.md` |
| S04 CP7 | `process/checks/CP7-CR018-S04-industry-market-cap-liquidity-and-exposure-data-VERIFICATION-DONE.md` |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| primary | `tests/test_cr018_pit_tradability_readiness.py` | 创建 fixture-only 合同测试。 |
| shared | `market_data/contracts.py` | 只允许 additive PIT / lifecycle / tradability readiness schema、reason code 和 counters；不得删除 S03 常量。 |
| shared | `market_data/validation.py` | 只允许 additive fail-closed PIT / lifecycle / tradability validation helper；不得改变 S03 benchmark helper 语义。 |
| shared | `market_data/readers.py` | 只允许 additive readiness blocked reason exposure helper；不得改变 S04 P1 helper 语义，不扫描未发布 lake。 |

禁止修改：`market_data/connectors/**`、`market_data/runtime.py`、provider connector、真实 lake 数据、catalog current pointer、QMT 入口、`engine/research_dataset.py`、S03/S04 primary 测试、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## Required Implementation

1. 增加 PIT readiness result / reason code：缺 `available_at` / `available_date` / `effective_date` 时 fail closed，production publish allowed count 必须为 0。
2. 当前快照不得替代历史 PIT universe；`current_snapshot_not_pit` 必须结构化阻断。
3. 增加 lifecycle readiness：缺 `list_date`、`delist_date`、code change 或 active denominator 不可算时 fail closed。
4. 增加 tradability readiness：缺 ST、suspend、trade_status、prices_limit 时 fail closed；不得假设涨停可买或跌停可卖。
5. Reader helper 默认 published-only，只暴露 structured blocked reason，不扫描 candidate / unpublished lake。
6. provider_fetch、lake_write、credential_read、current_pointer_publish、qmt_operation、duckdb_dependency_change 计数必须保持 0。

## Required Verification

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py
```

建议额外运行：

```bash
git diff --check -- market_data/contracts.py market_data/validation.py market_data/readers.py tests/test_cr018_pit_tradability_readiness.py
```

## CP6 Output

写入：

`process/checks/CP6-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-CODING-DONE.md`

CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

完成后回复修改文件、测试结果、CP6 路径和真实操作计数。
