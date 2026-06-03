---
handoff_id: "META-DEV-CR025-S06-CP7-BLOCKER-FIX-2026-06-02"
from: "meta-po"
to: "meta-dev"
change_id: "CR-025"
story_id: "CR025-S06-route-docs-and-follow-up-handoff"
wave_id: "CR025-W4-SAFETY-VERIFICATION-DOCS"
blocker_id: "CR025-S06-CP7-F01"
status: "completed-close-unavailable"
created_at: "2026-06-02T09:53:55+08:00"
updated_at: "2026-06-02T22:08:41+08:00"
---

# META-DEV Handoff: CR025-S06 CP7 Blocker Fix

## Dispatch

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `multi_agent_v1.spawn_agent` |
| agent_role | `meta-dev` |
| agent_name | `dev-qin` |
| agent_id | `019e860a-cd11-7820-b0e0-821e2133fbb2` |
| thread_id | `019e860a-cd11-7820-b0e0-821e2133fbb2` |
| spawned_at | `2026-06-02T09:55:21+08:00` |
| completed_at | `2026-06-02T10:00:17+08:00` |
| closed_at |  |
| close_attempt | `close_agent returned not_found at 2026-06-02T22:08:41+08:00; no closed_at fabricated` |

## Scope

修复 `CR025-S06-route-docs-and-follow-up-handoff` 的 CP7 阻断项 `CR025-S06-CP7-F01`。首轮 CP7 仅因 bounded static trace scan 缺失精确 token `QuantConnect LEAN` 失败；CR025 组合回归、diff check、依赖 diff、CR-020..CR-024 wording、CR-030 wording、forbidden claim scan、credential/private-path scan 和所有禁止操作计数均已 PASS。

本回修必须保持最小化：只把 CR-030 候选参考对象中当前写作的 `LEAN` 精确命名为 `QuantConnect LEAN`，并写入 blocker-fix CP6 证据。不得扩大 CR-025 范围，不得新增任何运行、依赖、源码迁移、QMT 或多因子主框架授权。

## Inputs

- `process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-VERIFICATION-DONE.md`
- `process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md`
- `process/stories/CR025-S06-route-docs-and-follow-up-handoff.md`
- `process/stories/CR025-S06-route-docs-and-follow-up-handoff-LLD.md`
- `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`
- `docs/USER-MANUAL.md`
- `README.md`
- `process/handoffs/META-QA-CR025-S06-CP7-VERIFY-2026-06-02.md`

## Allowed Write Scope

- `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`
- `docs/USER-MANUAL.md`
- `README.md`
- `process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md`
- `process/stories/CR025-S06-route-docs-and-follow-up-handoff.md`（仅允许追加 blocker fix 说明并保持 / 恢复 `status=ready-for-verification`）

## Required Fix

- 在 S06 bounded scan 文件集中确保精确 token `QuantConnect LEAN` 至少出现 1 次。
- 推荐最小改法：
  - `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md` §11 Candidate reference 表中，将 `LEAN` 行改为 `QuantConnect LEAN`。
  - 若同步用户手册有助于一致性，可将 `docs/USER-MANUAL.md` CR-025 故障说明里的 `LEAN` 改为 `QuantConnect LEAN`。
- 不得把 `QuantConnect LEAN` 写成已集成、已实现、已授权运行或默认路线；它只能是 CR-030 后续正式 CR 前的候选参考对象。

## Required Verification

- Run current CR025 regression:
  - `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_no_real_operation_safety.py tests/test_cr025_forbidden_source_copy.py tests/test_cr025_schema_contracts.py tests/test_cr025_order_intent_draft_contract.py tests/test_cr025_semantic_diff_contract.py tests/test_cr025_clean_feed_gate.py tests/test_cr025_backtrader_no_copy_guardrail.py`
- Run bounded exact trace scan over:
  - `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`
  - `README.md`
  - `docs/USER-MANUAL.md`
  - `process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md`
  - `process/stories/CR025-S06-route-docs-and-follow-up-handoff.md`
  Required exact token: `QuantConnect LEAN`.
- Run diff / dependency checks:
  - `git diff --check -- docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md docs/USER-MANUAL.md README.md process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md process/stories/CR025-S06-route-docs-and-follow-up-handoff.md`
  - `git diff --name-only -- pyproject.toml uv.lock`
- Run forbidden claim scan over the edited docs and Story to ensure no positive claim that CR-025 authorizes QuantConnect LEAN integration, Qlib / Alphalens / vectorbt / vn.py / PyBroker / bt integration, QMT, Backtrader run, dependency install, provider/lake/publish, simulation/live, or multifactor research main framework.
- Run credential/private-path scan over the edited docs and Story; real credential/private-path findings must be 0.

## Not Authorized

- Do not modify source code, tests, STATE, STORY-STATUS, DEVELOPMENT-PLAN, CR index, formal CR files, `pyproject.toml`, or `uv.lock`.
- Do not install dependencies or run `uv sync`, `uv add`, `pip install`, Backtrader samples/tests, or Backtrader runtime.
- Do not read, copy, crop, rewrite, migrate, or scan `/home/hyde/download/backtrader/**`.
- Do not import or call QMT, MiniQMT, XtQuant, broker APIs, provider SDKs, network clients, or service start commands.
- Do not read `.env`, token, cookie, session, account, private key, trading password, or any credential.
- Do not trigger provider fetch, real lake write, broker lake write, catalog publish, simulation, live, live-readonly, small-live, scale-up, account query, order submit, or cancel.
- Do not implement or authorize multifactor research main framework, FactorSpec, FactorRunSpec, IC / RankIC, layered returns, multifactor combination, experiment tracking, strategy admission package, Qlib / Alphalens / vectorbt / Zipline Reloaded / QuantConnect LEAN / RQAlpha / vn.py / PyBroker / bt integration, or QMT production route.

## Expected Output

- Minimal doc naming fix for `QuantConnect LEAN`.
- `process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md`
- Story remains / returns to `ready-for-verification`.

If any check fails, do not mark Story ready-for-verification; report the blocker and recommended fix.
