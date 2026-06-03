---
handoff_id: "META-QA-CR018-S07-CP7-VERIFY-2026-05-29"
from: "meta-po"
to: "meta-qa"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S07-explicit-publish-gate-and-current-reader-smoke"
wave_id: "CR018-W3-PUBLISH-ROLLBACK"
status: "completed-closed"
created_at: "2026-05-29T10:44:38+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e719f-f89b-70a1-98f7-b5c70015fb31"
  thread_id: "019e719f-f89b-70a1-98f7-b5c70015fb31"
  agent_name: "qa-cao"
  spawned_at: "2026-05-29T10:46:13+08:00"
  completed_at: "2026-05-29T10:48:59+08:00"
  closed_at: "2026-05-29T10:53:06+08:00"
---

# META-QA Handoff: CR018-S07 CP7 Verification

## Mission

验证 `CR018-S07-explicit-publish-gate-and-current-reader-smoke` 的 CP7：确认 Explicit Publish Gate 与 current reader smoke 合同满足 LLD、CP6 与 CR018 production data lake closure 门控。

本轮只允许受控离线 / fixture / dry-run 验证。严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

你不是独自在代码库中工作：当前已有 CR018-S01..S07 的未提交修改和验证产物。不要 revert 其他 Story 的改动；QA 只允许写入本 Story CP7 结果文件，除非发现阻断项需要在报告中要求回修。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S07-explicit-publish-gate-and-current-reader-smoke.md` |
| LLD | `process/stories/CR018-S07-explicit-publish-gate-and-current-reader-smoke-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S07-explicit-publish-gate-and-current-reader-smoke-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR018-S07-explicit-publish-gate-and-current-reader-smoke-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR018-S07-IMPLEMENT-2026-05-29.md` |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR018-S07-explicit-publish-gate-and-current-reader-smoke-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果。 |

禁止修改：`market_data/**`、`engine/**`、`experiments/**`、`tests/**`、Story 卡片、`STATE.md`、`STORY-STATUS.md`、`DEVELOPMENT-PLAN.yaml`、provider connector、真实 lake 数据、真实 catalog current pointer、QMT 入口、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## Required Verification

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_publish_current_reader_smoke.py tests/test_cr018_readiness_rollback_gate.py tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr014_catalog_publish_gate.py
```

建议额外运行：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/publish.py market_data/catalog.py market_data/readers.py
git diff --check -- market_data/publish.py market_data/catalog.py market_data/readers.py tests/test_cr018_publish_current_reader_smoke.py process/checks/CP6-CR018-S07-explicit-publish-gate-and-current-reader-smoke-CODING-DONE.md
git diff --name-only -- pyproject.toml uv.lock
git status --short -- .pytest_cache tests/__pycache__ market_data/__pycache__ engine/__pycache__
```

## Acceptance Checklist

1. publish 必须显式审批；缺 `approval_id` 时 allowed 次数为 0。
2. S06 readiness P0 fail / release evidence incomplete / rollback target 缺失时，publish decision 必须 blocked，current pointer update plan 为空。
3. validate / parity / quality / DuckDB audit PASS 不得自动 publish，自动 publish 次数必须为 0。
4. current reader smoke 必须覆盖 P0 dataset group；只读 published current pointer；缺 current pointer 时返回 `catalog_not_published`。
5. current reader 不得读取 candidate 替代 current；candidate fallback 必须 blocked。
6. `current_pointer_publish`、`real_lake_write`、`credential_read`、`provider_fetch`、`qmt_operation`、`duckdb_dependency_change` 计数必须保持 0。
7. CP7 结果必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

## Expected Output

`process/checks/CP7-CR018-S07-explicit-publish-gate-and-current-reader-smoke-VERIFICATION-DONE.md`
