---
handoff_id: "META-QA-CR018-S06-CP7-VERIFY-2026-05-29"
from: "meta-po"
to: "meta-qa"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S06-production-quality-readiness-audit-and-rollback-gate"
wave_id: "CR018-W3-PUBLISH-ROLLBACK"
status: "completed-closed"
created_at: "2026-05-29T10:17:24+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7186-d771-7fa0-8622-958915a43d98"
  thread_id: "019e7186-d771-7fa0-8622-958915a43d98"
  agent_name: "qa-hua"
  spawned_at: "2026-05-29T10:18:47+08:00"
  completed_at: "2026-05-29T10:21:20+08:00"
  closed_at: "2026-05-29T10:24:36+08:00"
---

# META-QA Handoff: CR018-S06 CP7 Verification

## Mission

独立验证 `CR018-S06-production-quality-readiness-audit-and-rollback-gate` 的 CP6 交付是否满足 LLD、Story 和 CP5 已批准边界。

本验证只允许离线 / fixture / dry-run 检查；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S06-production-quality-readiness-audit-and-rollback-gate.md` |
| LLD | `process/stories/CR018-S06-production-quality-readiness-audit-and-rollback-gate-LLD.md` |
| CP6 | `process/checks/CP6-CR018-S06-production-quality-readiness-audit-and-rollback-gate-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR018-S06-IMPLEMENT-2026-05-29.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| S02 CP7 | `process/checks/CP7-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-VERIFICATION-DONE.md` |
| S03 CP7 | `process/checks/CP7-CR018-S03-real-benchmark-index-components-weights-backfill-VERIFICATION-DONE.md` |
| S05 CP7 | `process/checks/CP7-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-VERIFICATION-DONE.md` |

## Verification Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| required-read | `market_data/validation.py` | 验证 `ReleaseReadinessAuditReport` 与 `build_release_readiness_audit_report()`，P0 fail / required_missing / quality fail 必须 fail-closed。 |
| required-read | `market_data/catalog.py` | 验证 `build_cr018_release_rollback_contract()`，rollback 必须 release-level，dataset-only rollback blocked。 |
| required-read | `market_data/publish.py` | 验证 `validate_release_publish_readiness_audit()`，只返回 dry-run 合同，不写 current pointer。 |
| required-read | `tests/test_cr018_readiness_rollback_gate.py` | 验证 S06 fixture-only 合同测试覆盖 LLD §10。 |
| write | `process/checks/CP7-CR018-S06-production-quality-readiness-audit-and-rollback-gate-VERIFICATION-DONE.md` | 仅写 CP7 验证结果。 |

禁止修改业务代码、Story、STATE、STORY-STATUS、DEVELOPMENT-PLAN、`pyproject.toml`、`uv.lock`、`.env`、真实 lake、provider connector、catalog current pointer 或 QMT 入口。

## Required Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_readiness_rollback_gate.py tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr014_catalog_publish_gate.py
```

建议额外运行：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/validation.py market_data/catalog.py market_data/publish.py
git diff --check -- market_data/validation.py market_data/catalog.py market_data/publish.py tests/test_cr018_readiness_rollback_gate.py process/checks/CP6-CR018-S06-production-quality-readiness-audit-and-rollback-gate-CODING-DONE.md
git diff --name-only -- pyproject.toml uv.lock
git status --short -- .pytest_cache tests/__pycache__ market_data/__pycache__ engine/__pycache__
```

## CP7 Output Requirements

CP7 文件必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果、真实操作计数和结论。

验证通过时结论写 `PASS`；发现阻断项时结论写 `FAIL`，并列出可回修的最小问题。
