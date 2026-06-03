---
handoff_id: "META-DEV-CR018-S06-IMPLEMENT-2026-05-29"
from: "meta-po"
to: "meta-dev"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S06-production-quality-readiness-audit-and-rollback-gate"
wave_id: "CR018-W3-PUBLISH-ROLLBACK"
status: "completed-closed"
created_at: "2026-05-29T10:03:07+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7179-7a76-7441-97e8-aa043e067fa3"
  thread_id: "019e7179-7a76-7441-97e8-aa043e067fa3"
  agent_name: "dev-zhu"
  spawned_at: "2026-05-29T10:04:10+08:00"
  completed_at: "2026-05-29T10:12:49+08:00"
  closed_at: "2026-05-29T10:17:24+08:00"
---

# META-DEV Handoff: CR018-S06 Implementation

## Mission

实现 `CR018-S06-production-quality-readiness-audit-and-rollback-gate` 的 production quality / readiness / rollback gate 合同。

S01、S02、S03、S04、S05 均已 verified，CP5 已 approved。本 Story 只允许受控离线 / fixture / dry-run 实现；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

你不是独自在代码库中工作：当前已有 CR018-S01..S05 的未提交修改和验证产物。不要 revert 其他 Story 的改动；如共享文件已有新 helper，请以 additive 方式兼容并复用。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S06-production-quality-readiness-audit-and-rollback-gate.md` |
| LLD | `process/stories/CR018-S06-production-quality-readiness-audit-and-rollback-gate-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S06-production-quality-readiness-audit-and-rollback-gate-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| S02 CP7 | `process/checks/CP7-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-VERIFICATION-DONE.md` |
| S03 CP7 | `process/checks/CP7-CR018-S03-real-benchmark-index-components-weights-backfill-VERIFICATION-DONE.md` |
| S05 CP7 | `process/checks/CP7-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-VERIFICATION-DONE.md` |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| primary | `tests/test_cr018_readiness_rollback_gate.py` | 创建 fixture-only 合同测试。 |
| shared | `market_data/validation.py` | 只允许 additive release readiness audit aggregator；不得改变 S02/S03/S05 既有 readiness 语义。 |
| shared | `market_data/catalog.py` | 只允许 additive release-level rollback metadata / event 合同；不得真实更新 current pointer。 |
| shared | `market_data/publish.py` | 只允许 additive publish 前 readiness audit hook；hook 必须 fail-closed，不执行真实 publish。 |
| process | `process/checks/CP6-CR018-S06-production-quality-readiness-audit-and-rollback-gate-CODING-DONE.md` | 写入 CP6 编码完成检查结果。 |
| process | `DEV-LOG.md` | 追加 CR018-S06 受控离线实现记录。 |

禁止修改：provider connector、真实 lake 数据、catalog current pointer、QMT 入口、S02/S03/S04/S05 primary 测试、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## Required Implementation

1. readiness audit report 必须覆盖 release、dataset、quality、blocked_claims、rollback_target、evidence_refs。
2. 任一 P0 readiness fail / required_missing / quality fail 时 publish allowed 次数必须为 0。
3. P1 auxiliary 缺失不能冒充已具备能力；必须进入 blocked_claims，但不必阻断 core publish candidate 继续评估。
4. rollback contract 必须 release-level；dataset-only rollback 必须 blocked，dataset-level rollback-only 通过次数必须为 0。
5. historical evidence 不得删除；raw / manifest / candidate / quality / release history evidence delete 次数必须为 0。
6. real_lake_write、current_pointer_publish、credential_read、provider_fetch、qmt_operation、duckdb_dependency_change 计数必须保持 0。

## Required Verification

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_readiness_rollback_gate.py tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py
```

建议额外运行：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/validation.py market_data/catalog.py market_data/publish.py
git diff --check -- market_data/validation.py market_data/catalog.py market_data/publish.py tests/test_cr018_readiness_rollback_gate.py
git diff --name-only -- pyproject.toml uv.lock
```

## CP6 Output

写入：

`process/checks/CP6-CR018-S06-production-quality-readiness-audit-and-rollback-gate-CODING-DONE.md`

CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

完成后回复修改文件、测试结果、CP6 路径和真实操作计数。
