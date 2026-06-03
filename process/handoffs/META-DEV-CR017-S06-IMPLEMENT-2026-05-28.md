---
handoff_id: "META-DEV-CR017-S06-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-017"
story_id: "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
wave_id: "CR017-W3-CONSUMER-MIGRATION"
status: "completed"
created_at: "2026-05-28T08:25:16+08:00"
updated_at: "2026-05-28T08:40:12+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6bfc-348d-7730-b9a1-cec5434a2646"
  thread_id: "019e6bfc-348d-7730-b9a1-cec5434a2646"
  agent_name: "dev-lv the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T08:29:17+08:00"
  completed_at: "2026-05-28T08:36:51+08:00"
  closed_at: "2026-05-28T08:40:12+08:00"
---

# META-DEV CR017-S06 Implementation Handoff

## Task

Implement `CR017-S06-research-qmt-consumer-docs-and-migration-guide` after CP5 approval and CR017-S04/S05 verification.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Story | `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide.md` | dev-ready |
| LLD | `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD-IMPLEMENTABILITY.md` | PASS |
| 上游 CP7 | `process/checks/CP7-CR017-S04-reader-api-and-policy-gates-VERIFICATION-DONE.md`、`process/checks/CP7-CR017-S05-validation-quality-parity-and-leakage-tests-VERIFICATION-DONE.md` | PASS |

## Allowed Write Scope

- `docs/ADJUSTMENT-POLICY-MIGRATION.md`
- `README.md`
- `docs/USER-MANUAL.md`
- `engine/research_dataset.py`
- `tests/test_cr017_research_qmt_consumer_boundary.py`
- `process/checks/CP6-CR017-S06-research-qmt-consumer-docs-and-migration-guide-CODING-DONE.md`
- `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR017-S06-T1 | 更新迁移指南，覆盖 chart、long-horizon research、factor research、QMT order intent 四类 consumer guidance。 |
| CR017-S06-T2 | 更新 README / USER-MANUAL 的用户可见口径边界，明确研究可用 qfq/hfq/returns_adjusted，QMT execution raw-only。 |
| CR017-S06-T3 | 在 `engine/research_dataset.py` 增加 consumer guidance / blocked claims / policy metadata helper，或按现有模式扩展等价接口。 |
| CR017-S06-T4 | 创建离线测试，验证 consumer matrix、QMT non-raw blocked、CR017 未 verified 时 scale_up blocked、旧 qfq 保留、不声明 unsupported execution features。 |
| CR017-S06-T5 | 写入 CP6，包含 Agent Dispatch Evidence、测试结果、LLD consumption、safety counters 和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr017_research_qmt_consumer_boundary.py
```

If `engine/research_dataset.py` is changed, also run the relevant CR017 reader/policy regression that covers the touched helper.

## Forbidden Scope

- Do not modify `process/HLD.md`, `process/HLD-DATA-LAKE.md`, `process/ARCHITECTURE-DECISION.md`, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, or private key files.
- Do not run provider fetch, real lake write, real broker lake write, current pointer publish, real order, real cancel, account query, dependency change, or legacy qfq overwrite.
- Do not implement CR015-S04/S05/S06/S07 or CR016.

## Safety Counters Required In CP6

`provider_fetch=0`、`lake_write=0`、`credential_read=0`、`current_pointer_publish=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`dependency_change=0`、`legacy_qfq_overwrite=0`。
