---
handoff_id: "META-QA-CR018-S08-CP7-VERIFY-2026-05-29"
from: "meta-po"
to: "meta-qa"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S08-production-current-truth-research-rerun"
wave_id: "CR018-W4-RERUN-QMT-ADMISSION"
status: "completed-closed"
created_at: "2026-05-29T11:10:32+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e71b7-4807-7e41-8d5e-f846b07b8bdf"
  thread_id: "019e71b7-4807-7e41-8d5e-f846b07b8bdf"
  agent_name: "qa-hua the 2nd"
  spawned_at: "2026-05-29T11:11:41+08:00"
  completed_at: "2026-05-29T11:14:23+08:00"
  closed_at: "2026-05-29T11:17:58+08:00"
---

# META-QA Handoff: CR018-S08 CP7 Verification

## Mission

验证 `CR018-S08-production-current-truth-research-rerun` 的 CP7：确认 published current truth 研究重跑离线合同、production current truth loader gate、report payload、QMT admission evidence 和 report overwrite guard 满足 Story、LLD、CP6 与 CR018 production data lake closure 门控。

本轮只允许受控离线 / fixture / dry-run 验证。严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、真实阶段三到阶段五长任务、DuckDB 依赖变更或任何 QMT 操作。

你不是独自在代码库中工作：当前已有 CR018-S01..S08 的未提交修改和验证产物。不要 revert 其他 Story 的改动；QA 只允许写入本 Story CP7 结果文件，除非发现阻断项需要在报告中要求回修。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S08-production-current-truth-research-rerun.md` |
| LLD | `process/stories/CR018-S08-production-current-truth-research-rerun-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S08-production-current-truth-research-rerun-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR018-S08-production-current-truth-research-rerun-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR018-S08-IMPLEMENT-2026-05-29.md` |
| S07 CP7 | `process/checks/CP7-CR018-S07-explicit-publish-gate-and-current-reader-smoke-VERIFICATION-DONE.md` |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR018-S08-production-current-truth-research-rerun-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果。 |

禁止修改：`experiments/**`、`engine/**`、`market_data/**`、`tests/**`、`reports/**`、Story 卡片、`STATE.md`、`STORY-STATUS.md`、`DEVELOPMENT-PLAN.yaml`、provider connector、真实 lake 数据、真实 catalog current pointer、QMT 入口、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## Required Verification

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_production_current_truth_rerun.py tests/test_cr018_publish_current_reader_smoke.py tests/test_cr018_readiness_rollback_gate.py tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr014_catalog_publish_gate.py
```

建议额外运行：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr018-s08-pycompile-cache PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile experiments/production_current_truth_rerun.py engine/research_dataset.py
git diff --check -- experiments/production_current_truth_rerun.py engine/research_dataset.py reports/production_current_truth/README.md tests/test_cr018_production_current_truth_rerun.py process/checks/CP6-CR018-S08-production-current-truth-research-rerun-CODING-DONE.md
git diff --name-only -- pyproject.toml uv.lock
git status --short -- .pytest_cache tests/__pycache__ market_data/__pycache__ engine/__pycache__ experiments/__pycache__
```

## Acceptance Checklist

1. 未 published release / catalog current pointer 缺失 / P0 required_missing / candidate path / proxy input / provider raw fallback 均 blocked，allowed 次数为 0。
2. production current truth loader 只读 published current truth/current reader metadata，不读 candidate 或 proxy。
3. rerun report payload 记录 release_id、release scope、as_of_trade_date、benchmark、PIT、tradability、adjustment_policy、blocked claims、old proxy/fixed baseline diff、pass/fail。
4. S08 未 PASS 时 QMT admission allowed 次数为 0。
5. old report overwrite blocked 或 unique target；不得覆盖旧报告。
6. `old_report_overwrite`、`provider_fetch`、`lake_write`、`credential_read`、`qmt_operation`、`candidate_read_count`、`proxy_input_allowed_count`、`duckdb_dependency_change` 均为 0。
7. CP7 结果必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

## Expected Output

`process/checks/CP7-CR018-S08-production-current-truth-research-rerun-VERIFICATION-DONE.md`
