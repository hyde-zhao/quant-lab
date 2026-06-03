---
handoff_id: "META-QA-CR025-S06-CP7-REVERIFY-2026-06-02"
from: "meta-po"
to: "meta-qa"
change_id: "CR-025"
story_id: "CR025-S06-route-docs-and-follow-up-handoff"
wave_id: "CR025-W4-SAFETY-VERIFICATION-DOCS"
status: "completed-closed"
created_at: "2026-06-02T22:15:11+08:00"
updated_at: "2026-06-02T22:26:23+08:00"
---

# META-QA Handoff: CR025-S06 CP7 Reverification

## Dispatch

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `multi_agent_v1.spawn_agent` |
| agent_role | `meta-qa` |
| agent_name | `qa-wei` |
| agent_id | `019e88b1-5328-7890-961f-aa76a50de028` |
| thread_id | `019e88b1-5328-7890-961f-aa76a50de028` |
| spawned_at | `2026-06-02T22:16:28+08:00` |
| completed_at | `2026-06-02T22:22:55+08:00` |
| closed_at | `2026-06-02T22:26:23+08:00` |

## Scope

复验 `CR025-S06-route-docs-and-follow-up-handoff` 的 CP7。首轮 CP7 文件 `process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-VERIFICATION-DONE.md` 保留为 FAIL 证据，唯一阻断项为 `CR025-S06-CP7-F01`：bounded static trace scan 缺失精确 token `QuantConnect LEAN`。

`meta-dev/dev-qin` 已完成 blocker fix，CP6 blocker-fix 结果为 PASS：`process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md`。本轮 QA 只验证 blocker fix 后的 S06 是否满足 CP7，不授权真实运行、依赖变更、源码迁移、QMT、Backtrader runtime、多因子研究主框架或任何外部接口。

## Inputs

- `process/stories/CR025-S06-route-docs-and-follow-up-handoff.md`
- `process/stories/CR025-S06-route-docs-and-follow-up-handoff-LLD.md`
- `process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md`
- `process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-VERIFICATION-DONE.md`
- `process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md`
- `process/handoffs/META-DEV-CR025-S06-CP7-BLOCKER-FIX-2026-06-02.md`
- `process/handoffs/META-QA-CR025-S06-CP7-VERIFY-2026-06-02.md`
- `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`
- `README.md`
- `docs/USER-MANUAL.md`
- `docs/CR025-BACKTRADER-MODULE-REFERENCE.md`
- `process/HLD.md`
- `process/HLD-QMT-TRADING.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md`
- `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md`
- `process/changes/CR-INDEX.yaml`
- `tests/test_cr025_no_real_operation_safety.py`
- `tests/test_cr025_forbidden_source_copy.py`
- `tests/test_cr025_schema_contracts.py`
- `tests/test_cr025_order_intent_draft_contract.py`
- `tests/test_cr025_semantic_diff_contract.py`
- `tests/test_cr025_clean_feed_gate.py`
- `tests/test_cr025_backtrader_no_copy_guardrail.py`

## Allowed Write Scope

- `process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-REVERIFY-DONE.md`

## Required Verification

- Run current CR025 regression:
  - `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_no_real_operation_safety.py tests/test_cr025_forbidden_source_copy.py tests/test_cr025_schema_contracts.py tests/test_cr025_order_intent_draft_contract.py tests/test_cr025_semantic_diff_contract.py tests/test_cr025_clean_feed_gate.py tests/test_cr025_backtrader_no_copy_guardrail.py`
- Run S06 documentation / whitespace checks:
  - `git diff --check -- docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md README.md docs/USER-MANUAL.md process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md process/stories/CR025-S06-route-docs-and-follow-up-handoff.md process/handoffs/META-DEV-CR025-S06-CP7-BLOCKER-FIX-2026-06-02.md process/handoffs/META-QA-CR025-S06-CP7-REVERIFY-2026-06-02.md`
  - `git diff --name-only -- pyproject.toml uv.lock`
- Run a bounded static trace scan over only S06 docs / user docs / CP6 / Story / handoff. The scan must confirm:
  - `CR025-S01-clean-feed-gate-backend-selector`
  - `CR025-S02-semantic-diff-schema-artifact`
  - `CR025-S03-order-intent-draft-qmt-boundary`
  - `CR025-S04-backtrader-module-reference-no-copy-guardrail`
  - `CR025-S05-no-real-operation-safety-verification`
  - `CR025-S06-route-docs-and-follow-up-handoff`
  - `DQ-CP3-CR025-01` through `DQ-CP3-CR025-06`
  - `CR-020` through `CR-024` with independent / later-gated / per-run authorization wording
  - `CR-030` and multifactor follow-up CR only wording
  - `FactorSpec`, `FactorRunSpec`, `IC / RankIC`, `分层收益`, `多因子组合`, `实验追踪`, `策略准入包`
  - `Qlib`, `Alphalens`, `vectorbt`, `Zipline Reloaded`, `QuantConnect LEAN`, `RQAlpha`, `vn.py`, `PyBroker`, `bt`, `Backtrader`
- Run bounded forbidden-claim review over only S06 docs / user docs / CP6 / Story / handoff. CP7 must record zero positive claims that CR-025 authorizes:
  - true trading, broker, QMT / MiniQMT / XtQuant, gateway start, account query, order submit, cancel
  - provider fetch, lake write, broker lake write, catalog publish
  - simulation/live/live-readonly/small-live/scale-up
  - Backtrader runtime run, dependency install, Backtrader source copy/migration
  - multifactor research main framework, Qlib / Alphalens / vectorbt / Zipline Reloaded / QuantConnect LEAN / RQAlpha / vn.py / PyBroker / bt integration
- Run credential / private path review over only S06 docs / user docs / CP6 / Story / handoff. CP7 must record no real credential examples, token/cookie/session/account/private-key/trading-password values, or real private paths.

## Not Authorized

- Do not modify source code, tests, docs, README, USER-MANUAL, Story cards, STATE, STORY-STATUS, DEVELOPMENT-PLAN, CR index, CR files, `pyproject.toml`, or `uv.lock`.
- Do not install dependencies or run `uv sync`, `uv add`, `pip install`, Backtrader samples/tests, or Backtrader runtime.
- Do not read, copy, crop, rewrite, migrate, or scan `/home/hyde/download/backtrader/**`.
- Do not import or call QMT, MiniQMT, XtQuant, broker APIs, provider SDKs, network clients, or service start commands.
- Do not read `.env`, token, cookie, session, account, private key, trading password, or any credential.
- Do not trigger provider fetch, real lake write, broker lake write, catalog publish, simulation, live, live-readonly, small-live, scale-up, account query, order submit, or cancel.
- Do not implement or authorize multifactor research main framework, FactorSpec, FactorRunSpec, IC / RankIC, layered returns, multifactor combination, experiment tracking, strategy admission package, Qlib / Alphalens / vectorbt / Zipline Reloaded / QuantConnect LEAN / RQAlpha / vn.py / PyBroker / bt integration, or QMT production route.

## Expected Output

- `process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-REVERIFY-DONE.md`

The CP7 file must include Entry Criteria, Checklist, Exit Criteria, Deliverables, Agent Dispatch Evidence, test command evidence, static trace scan evidence, forbidden claim scan evidence, credential/private-path scan evidence, forbidden-operation counters, dependency diff result, and final `PASS` / `FAIL`. If any check fails, mark CP7 `FAIL` or `BLOCKED` and list the exact blocker; do not mark S06 verified.
