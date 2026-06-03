---
handoff_id: "META-QA-CR018-S05-CP7-VERIFY-2026-05-29"
from: "meta-po"
to: "meta-qa"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness"
wave_id: "CR018-W2-P0-P1-READINESS"
status: "completed-closed"
created_at: "2026-05-29T09:53:06+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7170-3bc8-79d0-917d-23cc7b41b9e6"
  thread_id: "019e7170-3bc8-79d0-917d-23cc7b41b9e6"
  agent_name: "qa-kong"
  spawned_at: "2026-05-29T09:54:07+08:00"
  completed_at: "2026-05-29T09:56:03+08:00"
  closed_at: "2026-05-29T09:59:41+08:00"
---

# META-QA Handoff: CR018-S05 CP7 Verification

## Mission

独立验证 `CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness` 的 CP6 交付是否满足 LLD、Story 和 CP5 已批准边界。

本验证只允许离线 / fixture / dry-run 检查；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness.md` |
| LLD | `process/stories/CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-LLD.md` |
| CP6 | `process/checks/CP6-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR018-S05-IMPLEMENT-2026-05-29.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| CR017-S05 CP7 | `process/checks/CP7-CR017-S05-validation-quality-parity-and-leakage-tests-VERIFICATION-DONE.md` |

## Verification Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| required-read | `market_data/adjustment_policy.py` | 验证 CR018 adjustment publish policy metadata helper、operation counters 和 legacy qfq readonly metadata。 |
| required-read | `market_data/validation.py` | 验证 adjustment readiness / factor coverage / QMT raw-only helper。 |
| required-read | `market_data/readers.py` | 验证 raw/qfq/hfq/returns_adjusted reader policy metadata，不扫描 unpublished lake。 |
| required-read | `tests/test_cr018_adjustment_publish_readiness.py` | 验证 6 个 fixture-only 合同测试覆盖 LLD §10。 |
| write | `process/checks/CP7-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-VERIFICATION-DONE.md` | 仅写 CP7 验证结果。 |

禁止修改业务代码、Story、STATE、STORY-STATUS、DEVELOPMENT-PLAN、`pyproject.toml`、`uv.lock`、`.env`、真实 lake、provider connector、catalog current pointer 或 QMT 入口。

## Required Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr017_adjustment_quality_parity.py tests/test_cr017_reader_policy_gates.py
```

建议额外运行：

```bash
git diff --check -- market_data/adjustment_policy.py market_data/validation.py market_data/readers.py tests/test_cr018_adjustment_publish_readiness.py process/checks/CP6-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-CODING-DONE.md
```

## CP7 Output Requirements

CP7 文件必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果、真实操作计数和结论。

验证通过时结论写 `PASS`；发现阻断项时结论写 `FAIL`，并列出可回修的最小问题。
