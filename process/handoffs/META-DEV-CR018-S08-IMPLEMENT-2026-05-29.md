---
handoff_id: "META-DEV-CR018-S08-IMPLEMENT-2026-05-29"
from: "meta-po"
to: "meta-dev"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S08-production-current-truth-research-rerun"
wave_id: "CR018-W4-RERUN-QMT-ADMISSION"
status: "completed-closed"
created_at: "2026-05-29T10:55:42+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e71a9-6c49-79f1-aa78-b569801046d6"
  thread_id: "019e71a9-6c49-79f1-aa78-b569801046d6"
  agent_name: "dev-zhang the 2nd"
  spawned_at: "2026-05-29T10:56:39+08:00"
  completed_at: "2026-05-29T11:05:38+08:00"
  closed_at: "2026-05-29T11:10:32+08:00"
---

# META-DEV Handoff: CR018-S08 Implementation

## Mission

实现 `CR018-S08-production-current-truth-research-rerun` 的 published current truth 研究重跑离线合同。

S07 已 verified，CP5 已 approved。本 Story 只允许受控离线 / fixture / dry-run 实现；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、真实阶段三到阶段五长任务、DuckDB 依赖变更或任何 QMT 操作。

你不是独自在代码库中工作：当前已有 CR018-S01..S07 的未提交修改和验证产物。不要 revert 其他 Story 的改动；如共享文件已有 helper，请以 additive 方式兼容并复用。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S08-production-current-truth-research-rerun.md` |
| LLD | `process/stories/CR018-S08-production-current-truth-research-rerun-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S08-production-current-truth-research-rerun-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| S07 CP7 | `process/checks/CP7-CR018-S07-explicit-publish-gate-and-current-reader-smoke-VERIFICATION-DONE.md` |
| S07 reader contract | `tests/test_cr018_publish_current_reader_smoke.py`、`market_data/readers.py` |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| primary | `experiments/production_current_truth_rerun.py` | 创建 release-bound rerun entry、blocked reasons、report payload 和 QMT admission evidence helper；不得执行真实长任务。 |
| shared | `engine/research_dataset.py` | 只允许 additive production current truth loader gate / metadata；不得破坏既有 exploratory/proxy 路径。 |
| primary | `reports/production_current_truth/README.md` | 创建报告结构说明；不得覆盖旧 reports 或旧实验报告。 |
| primary | `tests/test_cr018_production_current_truth_rerun.py` | 创建 fixture-only 合同测试。 |
| process | `process/checks/CP6-CR018-S08-production-current-truth-research-rerun-CODING-DONE.md` | 写入 CP6 编码完成检查结果。 |
| process | `DEV-LOG.md` | 追加 CR018-S08 受控离线实现记录。 |

禁止修改：provider connector、真实 lake 数据、真实 catalog current pointer、QMT 入口、S01-S07 primary 测试、旧 reports/experiment_* 报告、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## Required Implementation

1. production rerun entry 必须要求 published `release_id`、strategy set、phase list、research adjustment policy 和 benchmark policy。
2. 未 published release、catalog current pointer 缺失、P0 required_missing、candidate path、proxy input 或 provider/raw fallback 均必须 blocked，allowed 次数为 0。
3. research dataset loader 必须只读 S07 published current reader / current truth metadata；不得直接读 provider raw、未发布 candidate、proxy baseline 或真实私有 lake 路径。
4. rerun report payload 必须记录 `release_id`、release scope、as_of_trade_date、benchmark、PIT universe、tradability、adjustment_policy、blocked claims、old proxy/fixed baseline diff 和 pass/fail。
5. S08 未 PASS 时，输出给 QMT admission 的 allowed 次数必须为 0。
6. old report overwrite 必须 blocked 或给出 unique target；不得覆盖旧报告。
7. `old_report_overwrite`、`provider_fetch`、`lake_write`、`credential_read`、`qmt_operation`、`candidate_read_count`、`proxy_input_allowed_count`、`duckdb_dependency_change` 均保持 0。

## Required Verification

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_production_current_truth_rerun.py tests/test_cr018_publish_current_reader_smoke.py tests/test_cr018_readiness_rollback_gate.py tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr014_catalog_publish_gate.py
```

建议额外运行：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr018-s08-pycompile-cache PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile experiments/production_current_truth_rerun.py engine/research_dataset.py
git diff --check -- experiments/production_current_truth_rerun.py engine/research_dataset.py reports/production_current_truth/README.md tests/test_cr018_production_current_truth_rerun.py
git diff --name-only -- pyproject.toml uv.lock
git status --short -- .pytest_cache tests/__pycache__ market_data/__pycache__ engine/__pycache__ experiments/__pycache__
```

## Expected Output

`process/checks/CP6-CR018-S08-production-current-truth-research-rerun-CODING-DONE.md`
