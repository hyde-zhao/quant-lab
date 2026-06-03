---
handoff_id: "META-DEV-CR015-S07-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-015"
story_id: "CR015-S07-docs-and-foundation-runbook-boundary"
wave_id: "CR015-W3-SHADOW-RUNBOOK"
status: "completed"
created_at: "2026-05-28T09:37:17+08:00"
updated_at: "2026-05-28T09:47:32+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c3b-de29-77c3-92e3-91c9a82a3115"
  thread_id: "019e6c3b-de29-77c3-92e3-91c9a82a3115"
  agent_name: "dev-kong the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T09:38:47+08:00"
  completed_at: "2026-05-28T09:44:33+08:00"
  closed_at: "2026-05-28T09:47:32+08:00"
---

# META-DEV CR015-S07 Implementation Handoff

## Task

Implement `CR015-S07-docs-and-foundation-runbook-boundary` after CR015-S01..S06 and CR017-S06 verification.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Story | `process/stories/CR015-S07-docs-and-foundation-runbook-boundary.md` | dev-ready |
| LLD | `process/stories/CR015-S07-docs-and-foundation-runbook-boundary-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR015-S07-docs-and-foundation-runbook-boundary-LLD-IMPLEMENTABILITY.md` | PASS |
| 上游 CP7 | CR015-S01..S06、CR017-S06 CP7 | PASS |

## Allowed Write Scope

- `docs/QMT-TRADING-RUNBOOK.md`
- `README.md`
- `docs/USER-MANUAL.md`
- `tests/test_cr015_foundation_runbook_boundary.py`
- `process/checks/CP6-CR015-S07-docs-and-foundation-runbook-boundary-CODING-DONE.md`
- `process/stories/CR015-S07-docs-and-foundation-runbook-boundary.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR015-S07-T1 | 创建 `docs/QMT-TRADING-RUNBOOK.md`，覆盖 setup、shadow、dry-run、mock、handoff to CR016 五类章节。 |
| CR015-S07-T2 | 在 `README.md` 与 `docs/USER-MANUAL.md` 追加 QMT foundation 限制、CR016 后续关系和 blocked claims。 |
| CR015-S07-T3 | 创建 `tests/test_cr015_foundation_runbook_boundary.py`，验证文档章节覆盖、真实交易支持声明次数为 0、真实 VWAP/minute/tick/Level2/order-match allowed claim 次数为 0、敏感值输出次数为 0。 |
| CR015-S07-T4 | 文档必须明确 CR015 只允许 shadow / dry-run / mock，不授权 simulation、live_readonly、small_live、scale_up、真实 QMT、真实发单、撤单、账户查询、凭据读取、真实 broker lake 写入、真实抓取、真实 lake 写入或 publish。 |
| CR015-S07-T5 | 写入 CP6，包含 Agent Dispatch Evidence、LLD consumption、测试结果、safety counters 和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr015_foundation_runbook_boundary.py
```

## Forbidden Scope

- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not implement CR016 or any simulation/live activation logic.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, real account snapshots, or real broker lake roots.
- Do not run provider fetch, real lake write, real broker lake write, current pointer publish, real order, real cancel, account query, dependency change, simulation/live activation, CR016-S01, CR016-S02, CR016-S03, CR016-S04, CR016-S05, CR016-S06, or CR016-S07.

## Safety Counters Required In CP6

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_activation=0`、`live_activation=0`、`real_trading_supported_claim_count=0`、`microstructure_allowed_claim_count=0`。
