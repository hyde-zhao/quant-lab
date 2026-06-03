---
handoff_id: "META-DEV-CR025-S03-IMPLEMENT-2026-06-02"
from: "meta-po"
to: "meta-dev"
change_id: "CR-025"
story_id: "CR025-S03-order-intent-draft-qmt-boundary"
wave_id: "CR025-W3-ORDER-INTENT-QMT"
status: "completed-closed"
created_at: "2026-06-02T08:26:16+08:00"
updated_at: "2026-06-02T08:39:30+08:00"
---

# META-DEV Handoff: CR025-S03 Implementation

## Dispatch

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `multi_agent_v1.spawn_agent` |
| agent_role | `meta-dev` |
| agent_name | `dev-you` |
| agent_id | `019e85ba-2dd3-79f2-835d-c324957d3776` |
| thread_id | `019e85ba-2dd3-79f2-835d-c324957d3776` |
| spawned_at | `2026-06-02T08:27:19+08:00` |
| completed_at | `2026-06-02T08:35:09+08:00` |
| closed_at | `2026-06-02T08:39:30+08:00` |

## Scope

实现 `CR025-S03-order-intent-draft-qmt-boundary` 的离线 `order_intent_draft_v1` 合同。S03 已通过 CP5，全量 LLD 已 confirmed；S02 semantic diff、CR015 OMS / shadow intent 和 CR017 raw execution policy gate 均已 verified。

## Inputs

- `process/stories/CR025-S03-order-intent-draft-qmt-boundary.md`
- `process/stories/CR025-S03-order-intent-draft-qmt-boundary-LLD.md`
- `process/checks/CP7-CR025-S02-semantic-diff-schema-artifact-VERIFICATION-DONE.md`
- `engine/semantic_diff.py`
- `process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md`
- `process/checks/CP7-CR015-S06-target-portfolio-to-order-intent-shadow-mode-VERIFICATION-DONE.md`
- `process/checks/CP7-CR017-S04-reader-api-and-policy-gates-VERIFICATION-DONE.md`
- `trading/oms.py`（只读参考）
- `trading/pretrade_risk.py`（只读参考）

## Allowed Write Scope

- `engine/order_intent_draft.py`
- `tests/test_cr025_order_intent_draft_contract.py`
- `process/checks/CP6-CR025-S03-order-intent-draft-qmt-boundary-CODING-DONE.md`
- `process/stories/CR025-S03-order-intent-draft-qmt-boundary.md`（仅允许实现完成后更新状态为 `ready-for-verification` 和 CP6 相关说明）

## Required Implementation

- 创建 clean-room `order_intent_draft_v1` schema / dataclass / mapping 合同。
- 提供 `build_order_intent_draft()`、`validate_order_intent_draft()`、`block_order_intent()`、`to_later_gated_handoff()`、`assert_no_qmt_side_effects()` 或等价接口。
- valid draft 必须固定 `qmt_allowed=false` 与 `not_authorization=true`。
- `execution_price_policy != raw` 必须 hard block。
- 缺少 `data_lineage_ref` 或 `limitations` 必须 fail closed。
- `consumer` 必须固定表达为 `CR-020..CR-024 later-gated`，且不得把 CR-025 的 CP5 通过解释为 QMT 授权。
- operation counters 必须覆盖并保持 0：QMT API、MiniQMT、XtQuant、order submit、order cancel、account query、broker lake write、service start、credential read、dependency change、Backtrader run/source copy、多因子研究框架实现。
- 测试必须 fixture-only，覆盖 LLD §10 的 T-S03-01 至 T-S03-08。
- 生成 CP6 文件，包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试命令、forbidden-operation counters 和最终 PASS / FAIL。

## Not Authorized

- 修改 `trading/oms.py`、`trading/pretrade_risk.py` 或真实交易流程。
- 修改 `pyproject.toml` / `uv.lock` 或安装依赖。
- 导入或调用 `xtquant`、QMT、MiniQMT、broker API、Backtrader runtime。
- 读取、复制、裁剪、改写或源码级迁移 `/home/hyde/download/backtrader/**`。
- 读取 `.env`、token、cookie、session、账号、私钥或交易密码。
- 发单、撤单、账户查询、broker lake 写入、服务启动、端口绑定。
- provider fetch、真实联网补数、真实 lake write、catalog publish。
- simulation、live_readonly、small_live、scale_up。
- 实现 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包，或集成 Qlib / Alphalens / vnpy.alpha。

## Required Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_order_intent_draft_contract.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_order_intent_draft_contract.py tests/test_cr025_semantic_diff_contract.py`
- `PYTHONPYCACHEPREFIX=/tmp/cr025-s03-pycompile uv run --python 3.11 python -m py_compile engine/order_intent_draft.py tests/test_cr025_order_intent_draft_contract.py`
- `git diff --check -- engine/order_intent_draft.py tests/test_cr025_order_intent_draft_contract.py process/checks/CP6-CR025-S03-order-intent-draft-qmt-boundary-CODING-DONE.md process/stories/CR025-S03-order-intent-draft-qmt-boundary.md`
- `git diff --name-only -- pyproject.toml uv.lock` 必须无输出。

## Expected Output

- `engine/order_intent_draft.py`
- `tests/test_cr025_order_intent_draft_contract.py`
- `process/checks/CP6-CR025-S03-order-intent-draft-qmt-boundary-CODING-DONE.md`
- `process/stories/CR025-S03-order-intent-draft-qmt-boundary.md` status=`ready-for-verification`

若任何检查失败，不得把 Story 标记为 ready-for-verification；报告 blocker 和建议修复路线。
