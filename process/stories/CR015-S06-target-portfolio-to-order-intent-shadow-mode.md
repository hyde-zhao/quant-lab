---
story_id: "CR015-S06-target-portfolio-to-order-intent-shadow-mode"
title: "目标组合到 order intent 的 shadow 流程"
story_slug: "target-portfolio-to-order-intent-shadow-mode"
status: "verified"
priority: "P0"
wave: "CR015-W3-SHADOW-RUNBOOK"
depends_on:
  - "CR015-S03-oms-order-state-machine"
  - "CR015-S04-pretrade-risk-gate"
  - "CR015-S05-broker-lake-schema-and-writer"
  - "CR017-S04-reader-api-and-policy-gates"
dependency_type:
  - upstream: "CR015-S03-oms-order-state-machine"
    type: "contract"
  - upstream: "CR015-S04-pretrade-risk-gate"
    type: "contract"
  - upstream: "CR015-S05-broker-lake-schema-and-writer"
    type: "contract"
  - upstream: "CR017-S04-reader-api-and-policy-gates"
    type: "contract"
cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/shadow_pipeline.py"
    - "tests/test_cr015_shadow_order_intent_pipeline.py"
  shared:
    - "trading/oms.py"
    - "trading/pretrade_risk.py"
    - "trading/broker_lake.py"
  merge_owner: "CR015-S06-target-portfolio-to-order-intent-shadow-mode"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker order or cancel call"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#7.1"
    - "process/HLD-DATA-LAKE.md#18"
    - "process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode.md"
  status: "approved"
  cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR015-S03/S04/S05 和 CR017-S04 均已 CP7 PASS / verified；CP5 已 approved；当前无 dev_running / verify_running 的共享 trading 文件冲突，可进入 shadow pipeline 离线实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T09:32:40+08:00"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR015-S06-IMPLEMENT-2026-05-28.md"
  implementation_started_at: "2026-05-28T09:13:25+08:00"
  implemented_by: "meta-dev/dev-you the 2nd"
  agent_id: "019e6c24-a307-73a2-9354-2039863031f9"
  agent_name: "dev-you the 2nd"
validation_gate:
  cp7_result: "process/checks/CP7-CR015-S06-target-portfolio-to-order-intent-shadow-mode-VERIFICATION-DONE.md"
  verified_at: "2026-05-28T09:32:40+08:00"
  verified_by: "meta-qa/qa-lv the 2nd"
  agent_id: "019e6c30-47c4-7972-86ff-2f9a24a743bf"
  agent_name: "qa-lv the 2nd"
  test_result: "38 passed in 0.16s"
change_id: "CR-015"
---

# CR015-S06：目标组合到 order intent 的 shadow 流程

## 目标

把研究目标组合、研究复权 metadata、raw 执行价引用、OMS、pre-trade risk、mock adapter 和 broker lake dry-run plan 串成 shadow 流程，证明 foundation 可离线验证且真实操作为 0。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-10 |
| 需求 | REQ-106、REQ-109、REQ-110、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §7.1 |
| ADR | ADR-055、ADR-056、ADR-057、ADR-058 |

## 开发上下文（dev_context）

**背景说明**：该 Story 是 CR-015 foundation 的最小闭环，但仅限 shadow/dry-run/mock。它不启用 simulation 或 live 阶段，不读取真实账户，不写真实 broker lake。

**输入文件**：CR015-S03/S04/S05、CR017-S04、HLD-QMT-TRADING §7.1。

**输出文件**：`trading/shadow_pipeline.py`、`tests/test_cr015_shadow_order_intent_pipeline.py`；共享 `trading/oms.py`、`trading/pretrade_risk.py`、`trading/broker_lake.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| shadow_run | target portfolio、policy metadata、fixture snapshots | order intent list、risk results、mock events、dry-run plan | any real mode blocked |
| target sizing | target weights、cash/holding fixture | target quantity / side | 非整手进入 risk blocked |
| audit summary | pipeline result | safety counters、blocked reasons | real operation counters 必须为 0 |

**设计约束**：输入 cash/position 必须是 fixture 或脱敏 snapshot contract；执行价只允许 raw reference；不触发真实 broker。

**命名规范**：`shadow_run_id`、`strategy_id`、`target_trade_date`、`safety_counters`、`dry_run_plan`.

**平台目标**：离线 foundation smoke / shadow pipeline。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR015-S03/S04/S05 | contract | OMS/risk/broker lake 合同已定义 | 共享 trading 文件，开发默认串行 | 组成 foundation 闭环 |
| CR017-S04 | contract | reader policy gate 已定义 | raw execution metadata 必填 | 防止口径混用 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR015-S06-T1 | 创建 | `trading/shadow_pipeline.py` | 串联 target portfolio -> intent -> risk -> mock event -> dry-run plan |
| CR015-S06-T2 | 创建 | `tests/test_cr015_shadow_order_intent_pipeline.py` | 覆盖全通过、risk blocked、非 raw policy blocked、安全计数 |
| CR015-S06-T3 | 修改 | `trading/oms.py` / `trading/pretrade_risk.py` | 按 LLD 接入 pipeline 返回类型 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr015_shadow_order_intent_pipeline.py`。

**验证方式**：fixture pipeline；不真实交易。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：目标组合生成 intent；risk fail 时 adapter_calls=0；mock event 推进状态机；dry-run plan 不写真实 broker lake。

## 量化验收标准（acceptance_criteria）

- [ ] shadow run 输出 intent、risk result、state transition、dry-run plan 4 类结果。
- [ ] 任一 risk fail 时 adapter_calls=0。
- [ ] 非 raw execution policy 通过次数为 0。
- [ ] real_order_call、real_cancel_call、account_write_call、credential_read、real_broker_lake_write 均为 0。

## 阻塞说明

CP5 前不得实现；simulation / live activation 由 CR016 管理。
