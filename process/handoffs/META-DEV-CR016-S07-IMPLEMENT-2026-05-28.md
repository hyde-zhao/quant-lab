---
handoff_id: "META-DEV-CR016-S07-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-016"
story_id: "CR016-S07-docs-user-manual-and-incident-playbooks"
wave_id: "CR016-W2-LIVE-SCALE-DOCS-GATED"
status: "completed"
created_at: "2026-05-28T11:46:16+08:00"
updated_at: "2026-05-28T11:56:41+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6cb1-70eb-72c2-bdf7-94a59009789f"
  thread_id: "019e6cb1-70eb-72c2-bdf7-94a59009789f"
  agent_name: "dev-zhu the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T11:47:11+08:00"
  completed_at: "2026-05-28T11:52:52+08:00"
  closed_at: "2026-05-28T11:56:41+08:00"
---

# META-DEV CR016-S07 Implementation Handoff

## Task

Implement `CR016-S07-docs-user-manual-and-incident-playbooks` as a documentation contract and static-test Story only.

This handoff does not authorize CR016-S05 / CR016-S06 implementation. `live_readonly`、`small_live`、`scale_up` remain later-gated and must stay blocked unless a later explicit user approval opens those Stories.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR016-S07-docs-user-manual-and-incident-playbooks.md` | dev-ready |
| LLD | `process/stories/CR016-S07-docs-user-manual-and-incident-playbooks-LLD.md` | approved / confirmed |
| CP5 自动预检 | `process/checks/CP5-CR016-S07-docs-user-manual-and-incident-playbooks-LLD-IMPLEMENTABILITY.md` | PASS |
| CP5 人工确认 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| S04 CP7 | `process/checks/CP7-CR016-S04-simulation-live-runbook-and-approval-gates-VERIFICATION-DONE.md` | PASS |
| S05 contract | `process/stories/CR016-S05-live-readonly-and-small-live-admission.md` | later-gated contract input only |
| S06 contract | `process/stories/CR016-S06-scale-up-and-research-maturity-gates.md` | later-gated contract input only |

## Allowed Write Scope

- `docs/QMT-INCIDENT-PLAYBOOK.md`
- `tests/test_cr016_docs_incident_playbooks.py`
- `README.md`
- `docs/USER-MANUAL.md`
- `docs/QMT-SIMULATION-LIVE-RUNBOOK.md`
- `process/checks/CP6-CR016-S07-docs-user-manual-and-incident-playbooks-CODING-DONE.md`
- `process/stories/CR016-S07-docs-user-manual-and-incident-playbooks.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR016-S07-T1 | 创建 incident playbook，覆盖 `shadow`、`simulation`、`live_readonly`、`small_live`、`scale_up` 5 个阶段。 |
| CR016-S07-T2 | 覆盖 `heartbeat_fail`、`risk_blocked`、`recon_diff`、`manual_trigger`、`recovery_required` 5 类 incident。 |
| CR016-S07-T3 | 每类 incident 必须包含 trigger、immediate action、owner、evidence required、recovery gate、rollback target。 |
| CR016-S07-T4 | README / USER-MANUAL 增加 staged activation 与 incident playbook 入口，明确文档、CP5、CP6、CP7、Story verified 均不是默认真实操作授权。 |
| CR016-S07-T5 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` 增加 incident playbook 引用和 recovery gate 说明。 |
| CR016-S07-T6 | 创建静态 pytest，验证 5 阶段、5 incident、recovery gate、manual takeover record、禁止默认授权、unsupported claim blocked、无敏感原值。 |
| CR016-S07-T7 | 写 CP6，包含 Agent Dispatch Evidence、测试结果、安全计数、阻断项和 PASS / FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr016_docs_incident_playbooks.py tests/test_cr016_runbook_approval_gates.py tests/test_cr015_foundation_runbook_boundary.py tests/test_cr016_monitoring_kill_switch.py
```

## Forbidden Scope

- Do not implement `CR016-S05` or `CR016-S06`.
- Do not modify `trading/live_admission.py`、`trading/scale_up_gate.py`、`engine/research_dataset.py`、`pyproject.toml`、`uv.lock`、`data/**`、`reports/**`、`delivery/**`、`DEV-LOG.md`、credentials、tokens、secret values、real broker lake roots、real account snapshots or real positions.
- Do not read `.env`、token、password、cookie、session、account、holdings、private key files or any credential file.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not query a real account, pull real broker snapshots, write real broker lake data, persist real incidents, overwrite old reports, run provider fetch, write real lake data, publish current pointer, place real orders, cancel real orders, run simulation, live_readonly, small_live, scale_up, or any activation side effect.
- Do not add or endorse text that implies runbook completion, CP5, CP6, CP7, Story verified, or document presence automatically authorizes real operations.
- Do not unblock VWAP、minute、tick、Level2 or order-match claims.

## Safety Counters Required In CP6

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_operation=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_run=0`、`live_run=0`、`small_live_run=0`、`scale_up_run=0`、`real_snapshot_pull=0`、`incident_persisted=0`、`default_real_operation_authorization_claim=0`、`unsupported_execution_claim_unblocked=0`、`sensitive_raw_value_output=0`。
