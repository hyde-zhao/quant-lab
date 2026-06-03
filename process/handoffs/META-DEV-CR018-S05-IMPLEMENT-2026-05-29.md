---
handoff_id: "META-DEV-CR018-S05-IMPLEMENT-2026-05-29"
from: "meta-po"
to: "meta-dev"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness"
wave_id: "CR018-W2-P0-P1-READINESS"
status: "completed-closed"
created_at: "2026-05-29T09:39:28+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7163-bfe3-7601-8a48-a5e229e346dc"
  thread_id: "019e7163-bfe3-7601-8a48-a5e229e346dc"
  agent_name: "dev-he"
  spawned_at: "2026-05-29T09:40:27+08:00"
  completed_at: "2026-05-29T09:48:50+08:00"
  closed_at: "2026-05-29T09:53:06+08:00"
---

# META-DEV Handoff: CR018-S05 Implementation

## Mission

实现 `CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness` 的 raw / adj_factor / qfq / hfq / returns_adjusted publish readiness 合同。

S01、S02、S03、S04 已 verified，CR017-S05 已 verified，CP5 已 approved。本 Story 只允许受控离线 / fixture / dry-run 实现；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness.md` |
| LLD | `process/stories/CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| S01 CP7 | `process/checks/CP7-CR018-S01-production-current-truth-definition-and-dataset-groups-VERIFICATION-DONE.md` |
| S02 CP7 | `process/checks/CP7-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-VERIFICATION-DONE.md` |
| S03 CP7 | `process/checks/CP7-CR018-S03-real-benchmark-index-components-weights-backfill-VERIFICATION-DONE.md` |
| S04 CP7 | `process/checks/CP7-CR018-S04-industry-market-cap-liquidity-and-exposure-data-VERIFICATION-DONE.md` |
| CR017-S05 CP7 | `process/checks/CP7-CR017-S05-validation-quality-parity-and-leakage-tests-VERIFICATION-DONE.md` |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| primary | `tests/test_cr018_adjustment_publish_readiness.py` | 创建 fixture-only 合同测试。 |
| shared | `market_data/adjustment_policy.py` | 只允许 additive CR018 adjustment readiness policy helper；不得覆盖 CR017 既有合同或旧 qfq baseline。 |
| shared | `market_data/validation.py` | 只允许 additive adjustment readiness / factor coverage / publish blocked helper；不得改变 S02/S03 validation 语义。 |
| shared | `market_data/readers.py` | 只允许 additive raw/qfq/hfq/returns_adjusted policy metadata helper；不得改变 S02/S04 reader helper 语义。 |

禁止修改：provider connector、真实 lake 数据、catalog current pointer、QMT 入口、`engine/research_dataset.py`、S02/S03/S04 primary 测试、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## Required Implementation

1. raw、adj_factor、qfq、hfq、returns_adjusted 五类 readiness 字段覆盖率必须为 100% 才可 publish。
2. 缺 adj_factor 或 factor coverage 不足时 publish allowed 必须为 0。
3. QMT execution consumer 使用 qfq/hfq/returns_adjusted 的 allowed 次数必须为 0；QMT execution feed 只能 raw。
4. 旧 qfq baseline overwrite 次数必须为 0，legacy baseline 必须只读保留。
5. Reader metadata 必须记录 adjustment policy、view kind、consumer kind、legacy baseline preserved 和 blocked reason。
6. provider_fetch、lake_write、credential_read、current_pointer_publish、qmt_operation、duckdb_dependency_change 计数必须保持 0。

## Required Verification

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr017_adjustment_quality_parity.py tests/test_cr017_reader_policy_gates.py
```

建议额外运行：

```bash
git diff --check -- market_data/adjustment_policy.py market_data/validation.py market_data/readers.py tests/test_cr018_adjustment_publish_readiness.py
```

## CP6 Output

写入：

`process/checks/CP6-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-CODING-DONE.md`

CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

完成后回复修改文件、测试结果、CP6 路径和真实操作计数。
