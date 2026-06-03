---
story_id: "CR015-S04-pretrade-risk-gate"
title: "pre-trade hard risk gate"
story_slug: "pretrade-risk-gate"
status: "verified"
priority: "P0"
wave: "CR015-W2-OMS-RISK-LAKE"
depends_on:
  - "CR015-S03-oms-order-state-machine"
  - "CR017-S02-raw-prices-and-adj-factor-contract-hardening"
  - "CR017-S04-reader-api-and-policy-gates"
dependency_type:
  - upstream: "CR015-S03-oms-order-state-machine"
    type: "contract"
  - upstream: "CR017-S02-raw-prices-and-adj-factor-contract-hardening"
    type: "contract"
  - upstream: "CR017-S04-reader-api-and-policy-gates"
    type: "contract"
cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/pretrade_risk.py"
    - "tests/test_cr015_pretrade_risk_gate.py"
  shared:
    - "trading/oms.py"
  merge_owner: "CR015-S04-pretrade-risk-gate"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker adapter call on risk failure"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#7.4"
    - "process/ARCHITECTURE-DECISION.md#ADR-058"
    - "process/stories/CR015-S04-pretrade-risk-gate.md"
  status: "approved"
  cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR015-S03、CR017-S02、CR017-S04 均已 CP7 PASS / verified；CP5 已 approved；当前未启动共享 `trading/oms.py` 的并发实现，可进入 pre-trade hard risk gate 离线实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T08:48:50+08:00"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR015-S04-IMPLEMENT-2026-05-28.md"
  implementation_started_at: "2026-05-28T08:29:17+08:00"
  implementation_completed_at: "2026-05-28T08:36:38+08:00"
  implemented_by: "meta-dev/dev-shi the 2nd"
  agent_id: "019e6bfc-34e1-7c93-9358-1b97db2cb08a"
  agent_name: "dev-shi the 2nd"
  cp6: "process/checks/CP6-CR015-S04-pretrade-risk-gate-CODING-DONE.md"
  cp6_status: "PASS"
  test_result: "22 passed in 0.09s"
  safety_counters:
    qmt_api_call: 0
    real_order_call: 0
    real_cancel_call: 0
    account_query_call: 0
    account_write_call: 0
    credential_read: 0
    real_broker_lake_write: 0
    real_lake_write: 0
    provider_fetch: 0
    publish: 0
    dependency_change: 0
    adapter_calls_on_block: 0
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR015-S04-pretrade-risk-gate-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR015-S04-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-yan the 2nd"
  verified_at: "2026-05-28T08:45:18+08:00"
  agent_id: "019e6c08-71c1-7f22-b5ce-80726a751f30"
  agent_name: "qa-yan the 2nd"
change_id: "CR-015"
---

# CR015-S04：pre-trade hard risk gate

## 目标

实现 pre-trade hard block 合同，覆盖现金、100 股整手、T+1 可卖、可用持仓、价格口径、重复 intent、单票 / 组合限额和异常价格；失败时 adapter_calls 必须为 0。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-10 |
| 需求 | REQ-109、REQ-110、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §7.1、§7.4 |
| ADR | ADR-058 |

## 开发上下文（dev_context）

**背景说明**：warn-only 风控不可接受。任何规则失败都必须在 adapter 前阻断，并输出 rule_id、blocked reason、risk profile 和审计事件。

**输入文件**：CR015-S03 order intent、CR017-S02 raw price contract、CR017-S04 reader policy gate、ADR-058。

**输出文件**：`trading/pretrade_risk.py`、`tests/test_cr015_pretrade_risk_gate.py`；共享 `trading/oms.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| evaluate_intent | order intent、cash snapshot、position snapshot、risk profile、raw price | pass / blocked | rule fail 时 adapter_calls=0 |
| duplicate guard | idempotency_key、run_id | duplicate / unique | duplicate blocked |
| price policy guard | execution policy、price source | pass / blocked | qfq/hfq execution price blocked |

**设计约束**：不读取真实账户；所有 cash/position 使用 fixture 或脱敏 snapshot contract；真实账户查询属于 CR016 后续授权范围。

**命名规范**：`risk_rule_id`、`blocked_reason`、`adapter_calls`、`cash_available_ref`、`position_available_ref`。

**平台目标**：OMS adapter 前置硬风控。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR015-S03 | contract | intent schema 已定义 | 风控消费 intent，不反向改状态机 | OMS 前置 |
| CR017-S02/S04 | contract | raw price 与 policy gate 已定义 | 复权价执行 blocked | 价格安全边界 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR015-S04-T1 | 创建 | `trading/pretrade_risk.py` | 定义风险规则、hard block result 和 reason enum |
| CR015-S04-T2 | 创建 | `tests/test_cr015_pretrade_risk_gate.py` | 覆盖现金、整手、T+1、重复、限额、非 raw 价格 |
| CR015-S04-T3 | 修改 | `trading/oms.py` | 按 LLD 在 intent 流程中接入 risk result |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr015_pretrade_risk_gate.py`。

**验证方式**：离线 fixture；不查询真实账户。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：现金不足 blocked；非 100 股 blocked；T+1 不可卖 blocked；重复 intent blocked；非 raw execution blocked；任一 fail 时 adapter_calls=0。

## 量化验收标准（acceptance_criteria）

- [ ] ADR-058 中 9 类规则覆盖率 100%。
- [ ] 任一风控失败时 adapter_calls 等于 0。
- [ ] blocked result 必含 rule_id、reason、intent id 和 risk profile。
- [ ] 默认验证 real_order_call、real_cancel_call、account_write_call、credential_read 均为 0。

## 阻塞说明

CP5 前不得实现；真实账户 snapshot 获取必须后续 per-run 授权。
