---
handoff_id: "META-DEV-CR018-S07-IMPLEMENT-2026-05-29"
from: "meta-po"
to: "meta-dev"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S07-explicit-publish-gate-and-current-reader-smoke"
wave_id: "CR018-W3-PUBLISH-ROLLBACK"
status: "completed-closed"
created_at: "2026-05-29T10:28:22+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7190-bef4-77c0-aefa-e247d20ed6de"
  thread_id: "019e7190-bef4-77c0-aefa-e247d20ed6de"
  agent_name: "dev-zhang"
  spawned_at: "2026-05-29T10:29:36+08:00"
  completed_at: "2026-05-29T10:39:55+08:00"
  closed_at: "2026-05-29T10:44:38+08:00"
---

# META-DEV Handoff: CR018-S07 Implementation

## Mission

实现 `CR018-S07-explicit-publish-gate-and-current-reader-smoke` 的 Explicit Publish Gate 与 current reader smoke 合同。

S06 已 verified，CP5 已 approved。本 Story 只允许受控离线 / fixture / dry-run 实现；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

你不是独自在代码库中工作：当前已有 CR018-S01..S06 的未提交修改和验证产物。不要 revert 其他 Story 的改动；如共享文件已有新 helper，请以 additive 方式兼容并复用。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S07-explicit-publish-gate-and-current-reader-smoke.md` |
| LLD | `process/stories/CR018-S07-explicit-publish-gate-and-current-reader-smoke-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S07-explicit-publish-gate-and-current-reader-smoke-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| S06 CP7 | `process/checks/CP7-CR018-S06-production-quality-readiness-audit-and-rollback-gate-VERIFICATION-DONE.md` |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| primary | `tests/test_cr018_publish_current_reader_smoke.py` | 创建 fixture-only 合同测试。 |
| shared | `market_data/publish.py` | 只允许 additive Explicit Publish Gate、approval_id 必需校验、P0 fail blocked 和 auto-publish guard；不得执行真实 current pointer publish。 |
| shared | `market_data/catalog.py` | 只允许 additive release-level current pointer plan、publish evidence record、checksum 与 rollback target 字段；不得写真实 catalog pointer。 |
| shared | `market_data/readers.py` | 只允许 additive current reader smoke fail-fast 合同；reader 缺 published pointer 时不得读取 candidate。 |
| process | `process/checks/CP6-CR018-S07-explicit-publish-gate-and-current-reader-smoke-CODING-DONE.md` | 写入 CP6 编码完成检查结果。 |
| process | `DEV-LOG.md` | 追加 CR018-S07 受控离线实现记录。 |

禁止修改：provider connector、真实 lake 数据、真实 catalog current pointer、QMT 入口、S02/S03/S04/S05/S06 primary 测试、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## Required Implementation

1. publish 必须显式审批，缺 `approval_id` 时 allowed 次数为 0。
2. S06 readiness P0 fail / release evidence incomplete / rollback target 缺失时，publish decision 必须 blocked，current pointer update plan 为空。
3. validate / parity / quality / DuckDB audit PASS 不得自动 publish，自动 publish 次数必须为 0。
4. current reader smoke 必须覆盖 P0 dataset group；只读 published current pointer；缺 current pointer 时返回 `catalog_not_published`。
5. current reader 不得读取 candidate 替代 current；candidate fallback 必须 blocked。
6. current_pointer_publish、real_lake_write、credential_read、provider_fetch、qmt_operation、duckdb_dependency_change 计数必须保持 0。

## Required Verification

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_publish_current_reader_smoke.py tests/test_cr018_readiness_rollback_gate.py tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr014_catalog_publish_gate.py
```

建议额外运行：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/publish.py market_data/catalog.py market_data/readers.py
git diff --check -- market_data/publish.py market_data/catalog.py market_data/readers.py tests/test_cr018_publish_current_reader_smoke.py
git diff --name-only -- pyproject.toml uv.lock
git status --short -- .pytest_cache tests/__pycache__ market_data/__pycache__ engine/__pycache__
```

## CP6 Output

写入：

`process/checks/CP6-CR018-S07-explicit-publish-gate-and-current-reader-smoke-CODING-DONE.md`

CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

完成后回复修改文件、测试结果、CP6 路径和真实操作计数。
