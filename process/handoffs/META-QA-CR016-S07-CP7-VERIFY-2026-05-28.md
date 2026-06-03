---
handoff_id: "META-QA-CR016-S07-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-016"
story_id: "CR016-S07-docs-user-manual-and-incident-playbooks"
wave_id: "CR016-W2-LIVE-SCALE-DOCS-GATED-CP7"
status: "completed"
created_at: "2026-05-28T11:58:15+08:00"
updated_at: "2026-05-28T12:04:05+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6cbc-5bed-7273-87a7-a6d11a36ac88"
  thread_id: "019e6cbc-5bed-7273-87a7-a6d11a36ac88"
  agent_name: "qa-he the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T11:59:06+08:00"
  completed_at: "2026-05-28T12:01:00+08:00"
  closed_at: "2026-05-28T12:04:05+08:00"
---

# META-QA CR016-S07 CP7 Verification Handoff

## Task

Verify `CR016-S07-docs-user-manual-and-incident-playbooks` after CP6 PASS. This is a documentation contract / static-test verification only.

This handoff does not authorize CR016-S05 / CR016-S06 implementation, QMT / MiniQMT / GUI / broker API calls, real orders, cancels, account queries, provider fetches, lake writes, publish, credential reads, simulation, live_readonly, small_live, scale_up, or any activation side effect.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR016-S07-docs-user-manual-and-incident-playbooks.md` | ready-for-verification |
| LLD | `process/stories/CR016-S07-docs-user-manual-and-incident-playbooks-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR016-S07-docs-user-manual-and-incident-playbooks-LLD-IMPLEMENTABILITY.md` | PASS |
| CP5 人工确认 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| CP6 | `process/checks/CP6-CR016-S07-docs-user-manual-and-incident-playbooks-CODING-DONE.md` | PASS |
| Implementation handoff | `process/handoffs/META-DEV-CR016-S07-IMPLEMENT-2026-05-28.md` | completed |
| S04 CP7 | `process/checks/CP7-CR016-S04-simulation-live-runbook-and-approval-gates-VERIFICATION-DONE.md` | PASS |

## Allowed Write Scope

- `process/checks/CP7-CR016-S07-docs-user-manual-and-incident-playbooks-VERIFICATION-DONE.md`

Do not update Story status to `verified`; meta-po will do that after CP7 evidence is reviewed.

## Required Verification

| TASK-ID | 要求 |
|---|---|
| CR016-S07-QA1 | 校验 CP6、Story、LLD、CP5、handoff lifecycle 和 Agent Dispatch Evidence 一致。 |
| CR016-S07-QA2 | 运行指定回归命令并记录结果。 |
| CR016-S07-QA3 | 验证文档覆盖 `shadow`、`simulation`、`live_readonly`、`small_live`、`scale_up` 5 个阶段。 |
| CR016-S07-QA4 | 验证 incident playbook 覆盖 `heartbeat_fail`、`risk_blocked`、`recon_diff`、`manual_trigger`、`recovery_required`，且每类都有 trigger、immediate action、owner、evidence required、recovery gate、rollback target。 |
| CR016-S07-QA5 | 验证 recovery gate 明确 `manual_takeover_record` / 人工接管记录要求。 |
| CR016-S07-QA6 | 验证默认真实操作授权声明次数为 0，unsupported execution claim unblocked 次数为 0，文档不含敏感原值。 |
| CR016-S07-QA7 | 验证真实操作计数全部为 0，尤其 `simulation_run`、`live_run`、`small_live_run`、`scale_up_run`、`incident_persisted`。 |
| CR016-S07-QA8 | 写入 CP7，包含 Agent Dispatch Evidence、测试结果、安全计数、阻断项和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr016_docs_incident_playbooks.py tests/test_cr016_runbook_approval_gates.py tests/test_cr015_foundation_runbook_boundary.py tests/test_cr016_monitoring_kill_switch.py
```

## Forbidden Scope

- Do not modify source code, tests, docs, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not implement CR016-S05/S06.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, real account snapshots, real positions, or real broker lake roots.
- Do not query a real account, pull real broker snapshots, write real broker lake data, persist incidents to a real broker lake, overwrite old reports, run provider fetch, write real lake data, publish current pointer, place real orders, cancel real orders, run simulation, live_readonly, small_live, scale_up, or any activation side effect.
- Do not add or endorse text that implies runbook completion, incident playbook completion, CP5, CP6, CP7, Story verified, or document presence automatically authorizes real operations.
- Do not unblock VWAP、minute、tick、Level2 or order-match claims.

## Safety Counters Required In CP7

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_operation=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_run=0`、`live_run=0`、`small_live_run=0`、`scale_up_run=0`、`real_snapshot_pull=0`、`incident_persisted=0`、`default_real_operation_authorization_claim=0`、`unsupported_execution_claim_unblocked=0`、`sensitive_raw_value_output=0`。
