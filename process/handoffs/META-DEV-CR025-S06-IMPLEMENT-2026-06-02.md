---
handoff_id: "META-DEV-CR025-S06-IMPLEMENT-2026-06-02"
from: "meta-po"
to: "meta-dev"
change_id: "CR-025"
story_id: "CR025-S06-route-docs-and-follow-up-handoff"
wave_id: "CR025-W4-SAFETY-VERIFICATION-DOCS"
status: "completed-closed"
created_at: "2026-06-02T09:22:57+08:00"
updated_at: "2026-06-02T09:37:34+08:00"
---

# META-DEV Handoff: CR025-S06 Implementation

## Dispatch

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `multi_agent_v1.spawn_agent` |
| agent_role | `meta-dev` |
| agent_name | `dev-kong` |
| agent_id | `019e85ee-1bae-7351-b198-92d269939f1b` |
| thread_id | `019e85ee-1bae-7351-b198-92d269939f1b` |
| spawned_at | `2026-06-02T09:23:59+08:00` |
| completed_at | `2026-06-02T09:33:25+08:00` |
| closed_at | `2026-06-02T09:35:40+08:00` |

## Scope

实现 `CR025-S06-route-docs-and-follow-up-handoff`。S01、S04、S02、S03、S05 均已 CP6 / CP7 PASS 并 verified；S06 已通过 CP5，全量 LLD 已 confirmed，调度时为 `dev-ready`，当前 CP6 已 PASS 并进入 `ready-for-verification`。本 Story 只做文档与后续路线边界收敛，不实现真实运行、QMT、Backtrader runtime、多因子研究主框架或任何外部接口。

## Inputs

- `process/stories/CR025-S06-route-docs-and-follow-up-handoff.md`
- `process/stories/CR025-S06-route-docs-and-follow-up-handoff-LLD.md`
- `process/checks/CP7-CR025-S01-clean-feed-gate-backend-selector-VERIFICATION-DONE.md`
- `process/checks/CP7-CR025-S02-semantic-diff-schema-artifact-VERIFICATION-DONE.md`
- `process/checks/CP7-CR025-S03-order-intent-draft-qmt-boundary-VERIFICATION-DONE.md`
- `process/checks/CP7-CR025-S04-backtrader-module-reference-no-copy-guardrail-VERIFICATION-DONE.md`
- `process/checks/CP7-CR025-S05-no-real-operation-safety-verification-VERIFICATION-DONE.md`
- `docs/CR025-BACKTRADER-MODULE-REFERENCE.md`
- `process/HLD.md` §34
- `process/HLD-QMT-TRADING.md` §18
- `process/ARCHITECTURE-DECISION.md` ADR-074..ADR-078
- `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md`
- `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md`
- `process/changes/CR-INDEX.yaml`
- `README.md`
- `docs/USER-MANUAL.md`

## Allowed Write Scope

- `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`
- `README.md`
- `docs/USER-MANUAL.md`
- `process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md`
- `process/stories/CR025-S06-route-docs-and-follow-up-handoff.md`（仅允许实现完成后更新 status=`ready-for-verification`、updated_at 和 CP6 相关说明）

## Required Implementation

- 创建 CR-025 专题文档 `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`，至少覆盖：
  - CR-025 是 research execution semantic alignment，不是 QMT route activation、simulation/live 或多因子研究主框架。
  - 6 个 CP3 DQ 与 6 个 CR025 Story 的 traceability。
  - semantic diff 的 baseline/reference 双轨、limitations、unavailable、非 production truth、非 simulation-ready。
  - `order_intent_draft_v1` 的 not order、not authorization、later-gated consumer、QMT forbidden boundary。
  - Backtrader optional dependency、lazy import、no-copy、`migration_candidate=[]`、no runtime default。
  - no-real-operation 表，覆盖 LLD、实现、依赖变更、Backtrader run、Backtrader source copy、broker、QMT / MiniQMT / XtQuant、provider、lake、broker lake、publish、simulation/live、credential read。
  - CR-020..CR-024 QMT 后续路线必须独立 CR / CP / stage gate / per-run authorization，不继承 CR-025 授权。
  - CR-030 多因子研究框架借鉴候选：FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包另起后续 CR；Qlib / Alphalens / vectorbt / Zipline Reloaded / LEAN / RQAlpha / vn.py / PyBroker / bt / Backtrader 只作为正式 CR 前需重验 license / 维护状态 / 适配边界的参考方向。
- 在 `README.md` 添加最小入口和不授权摘要；不得添加依赖安装、Backtrader run、QMT gateway start、publish、simulation/live 或多因子框架启用步骤。
- 在 `docs/USER-MANUAL.md` 添加用户视角边界和故障说明；不得添加真实凭据示例、账户号、token、cookie、session、私钥、交易密码或真实私有路径。
- 写入 CP6 文件，包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、静态扫描证据、forbidden authorization / forbidden claim scan 结论、依赖 diff、最终 PASS / FAIL。

## Not Authorized

- 修改业务源码、测试文件、`pyproject.toml`、`uv.lock`、CR index、STATE、STORY-STATUS、DEVELOPMENT-PLAN、HLD、ADR 或其他 Story。
- 安装依赖，运行 `uv sync` / `uv add` / `pip install`，或引入 Qlib / Alphalens / vectorbt / Backtrader 依赖。
- 运行 Backtrader backend、samples、tests、runtime 或任何 broker/live store。
- 读取、复制、裁剪、改写、迁移或扫描 `/home/hyde/download/backtrader/**`。
- 启动 gateway、绑定端口、调用 QMT / MiniQMT / XtQuant、发单、撤单、查询账户或写 broker lake。
- 读取 `.env`、token、cookie、session、账号、私钥、交易密码或任何凭据。
- 触发 provider fetch、真实 lake write、broker lake write、catalog publish、simulation、live、live-readonly、small-live、scale-up。
- 实现 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包，或集成 Qlib / Alphalens / vectorbt / vnpy.alpha。

## Required Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_no_real_operation_safety.py tests/test_cr025_forbidden_source_copy.py tests/test_cr025_schema_contracts.py tests/test_cr025_order_intent_draft_contract.py tests/test_cr025_semantic_diff_contract.py tests/test_cr025_clean_feed_gate.py tests/test_cr025_backtrader_no_copy_guardrail.py`
- `git diff --check -- docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md README.md docs/USER-MANUAL.md process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md process/stories/CR025-S06-route-docs-and-follow-up-handoff.md`
- `git diff --name-only -- pyproject.toml uv.lock`
- Static docs boundary scan must verify:
  - CR025-S01..S06 and DQ-CP3-CR025-01..06 traceability present.
  - CR-020..CR-024 each appears with independent authorization / later-gated / separate CR wording.
  - CR-030 / multifactor route appears with follow-up CR only wording.
  - No positive claim that CR-025 authorizes true trading, QMT, broker, provider fetch, lake write, publish, simulation/live, dependency install, Backtrader run, or multifactor research main framework.
  - No credential examples or real private paths.

## Expected Output

- `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`
- README / USER-MANUAL minimal CR-025 boundary entry
- `process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md`
- `process/stories/CR025-S06-route-docs-and-follow-up-handoff.md` status=`ready-for-verification`

If any check fails, do not mark Story ready-for-verification; report the blocker and recommended fix route.
