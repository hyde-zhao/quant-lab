---
story_id: "CR030-S07-strategy-admission-package-handoff"
title: "StrategyAdmissionPackage 与研究到执行 handoff"
story_slug: "strategy-admission-package-handoff"
status: "verified"
priority: "P0"
wave: "CR030-W4-ADMISSION-SAFETY-DOCS"
depends_on:
  - "CR030-S05-multifactor-combiner-portfolio-plan"
  - "CR030-S06-experiment-manifest-report-catalog"
  - "CR019-S01-stage6-admission-gate-package"
  - "CR025-S03-order-intent-draft-qmt-boundary"
dependency_type:
  - upstream: "CR030-S05-multifactor-combiner-portfolio-plan"
    type: "portfolio-plan-contract"
  - upstream: "CR030-S06-experiment-manifest-report-catalog"
    type: "manifest-catalog-contract"
  - upstream: "CR019-S01-stage6-admission-gate-package"
    type: "stage6-admission-contract"
  - upstream: "CR025-S03-order-intent-draft-qmt-boundary"
    type: "order-intent-draft-contract"
cp5_batch: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/strategy_admission_package.py"
    - "tests/test_cr030_strategy_admission_package.py"
  shared:
    - "engine/stage6_admission.py"
    - "engine/order_intent_draft.py"
    - "trading/stage_gate.py"
  merge_owner: "CR030-S07-strategy-admission-package-handoff"
  forbidden:
    - "QMT call"
    - "MiniQMT call"
    - "XtQuant import or call"
    - "gateway start"
    - "order submit"
    - "order cancel"
    - "account query"
    - "broker lake write"
    - "simulation/live authorization"
lld_gate:
  required_inputs:
    - "process/HLD.md#35.6"
    - "process/HLD.md#35.8"
    - "process/HLD.md#35.12"
    - "process/ARCHITECTURE-DECISION.md#ADR-085"
    - "process/stories/CR030-S07-strategy-admission-package-handoff.md"
  status: "approved"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  qmt_operation_allowed: false
  simulation_or_live_allowed: false
  credential_read_allowed: false
task_count: 5
created_at: "2026-06-03T08:30:00+08:00"
updated_at: "2026-06-03T11:12:22+08:00"
change_id: "CR-030"
dependency_unlocked_by:
  - "CR030-S05-multifactor-combiner-portfolio-plan"
  - "CR030-S06-experiment-manifest-report-catalog"
dependency_unlocked_at: "2026-06-03T10:47:33+08:00"
dev_dispatch:
  mode: "spawn_agent"
  agent_id: "019e8b66-de6b-70e0-aeca-c94b1b9d07c6"
  agent_name: "dev-lv"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-03T10:54:05+08:00"
  completed_at: "2026-06-03T11:01:17+08:00"
  closed_at: "2026-06-03T11:03:59+08:00"
  cp6_checkpoint: "process/checks/CP6-CR030-S07-strategy-admission-package-handoff-CODING-DONE.md"
  handoff_path: "process/handoffs/META-DEV-CR030-S07-IMPLEMENT-2026-06-03.md"
  cp6_status: "PASS"
qa_dispatch:
  mode: "spawn_agent"
  agent_id: "019e8b73-1a7b-72a0-b2d6-760665d5de93"
  agent_name: "qa-yan"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-03T11:07:23+08:00"
  completed_at: "2026-06-03T11:09:36+08:00"
  closed_at: "2026-06-03T11:12:22+08:00"
  cp7_checkpoint: "process/checks/CP7-CR030-S07-strategy-admission-package-handoff-VERIFICATION-DONE.md"
  handoff_path: "process/handoffs/META-QA-CR030-S07-CP7-VERIFY-2026-06-03.md"
  cp7_status: "PASS"
---

# CR030-S07：StrategyAdmissionPackage 与研究到执行 handoff

## 目标

定义 `StrategyAdmissionPackage` 与研究到执行 handoff，只输出研究准入证据、blocked reasons 和 `order_intent_draft_v1` 草稿引用，不构成 QMT / simulation / live 授权。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-27、TS-030-08、TS-030-10 |
| 需求 | REQ-181、REQ-182、REQ-185 |
| HLD | `process/HLD.md` §35.6、§35.8、§35.12 |
| ADR | ADR-085 |

## 开发上下文（dev_context）

**背景说明**：多因子研究结果需要为 Stage6 admission 和后续 QMT 路线提供证据，但真实 QMT route 已拆分为 CR-020..CR-024。CR-030 只能生成准入包和草稿边界。

**输入文件**：CR030-S05 组合计划、CR030-S06 manifest/catalog、CR019 stage6 admission 合同、CR025 `order_intent_draft_v1` 合同、HLD §35、本 Story 卡片。

**输出文件**：`engine/strategy_admission_package.py`、`tests/test_cr030_strategy_admission_package.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| 输入 | portfolio plan、manifest/catalog、Stage6 gate、blocked claims、order intent draft schema |
| 输出 | admission status、evidence refs、blocked reasons、解除条件、draft handoff refs |
| 状态 | `pass`、`warn`、`fail`、`blocked` |
| QMT boundary | 无独立 QMT CR 时 `qmt_api_call=0`、`real_order=0`、`account_query=0` |

**设计约束**：不得调用 QMT、不得生成可提交订单、不得启动 gateway、不得查询账户、不得写 broker lake。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR030-S05 | portfolio-plan-contract | 组合计划冻结 | 只消费 portfolio plan | 不生成订单 |
| CR030-S06 | manifest-catalog-contract | catalog 字段冻结 | 缺 P0 字段 blocked | admission 来源证据 |
| CR019-S01 | stage6-admission-contract | 只读引用 Stage6 gate | 不回滚 CR019 | admission gate 前置 |
| CR025-S03 | order-intent-draft-contract | 只读引用 draft schema | 不继承 CR025 授权 | handoff 草稿边界 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/strategy_admission_package.py`、`tests/test_cr030_strategy_admission_package.py` | 当前 Story 独占 |
| shared | `engine/stage6_admission.py`、`engine/order_intent_draft.py`、`trading/stage_gate.py` | 只读或串行合并 |
| forbidden | QMT call、order/cancel/account、broker lake、simulation/live | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR030-S07-T1 | 设计 | `engine/strategy_admission_package.py` | 定义 admission package schema 和状态机 |
| CR030-S07-T2 | 设计 | `tests/test_cr030_strategy_admission_package.py` | 设计 Stage6 fail、no-QMT-CR、draft-only fixture |
| CR030-S07-T3 | 兼容 | `engine/stage6_admission.py` | 说明 Stage6 gate 只读引用方式 |
| CR030-S07-T4 | 兼容 | `engine/order_intent_draft.py` | 说明 `order_intent_draft_v1` 草稿引用边界 |
| CR030-S07-T5 | 约束 | QMT route | 明确 CR-020..CR-024 独立授权前计数为 0 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr030_strategy_admission_package.py`，但本阶段不执行。

**验证方式**：admission 状态合同测试、QMT forbidden operation scan、draft-only handoff 测试。

**依赖环境**：本地 fixture；不得启动 QMT / gateway / simulation / live 或读取凭据。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| Stage6 P0 gate fail | `admission_status=blocked` |
| 无独立 QMT CR | QMT / order / account 计数均为 0 |
| 缺 manifest/catalog P0 字段 | 不生成 admission package |
| 用户要求 simulation/live | 输出 not-authorized 和后续 CR 路线 |

## 量化验收标准（acceptance_criteria）

- [ ] admission status 覆盖 pass / warn / fail / blocked。
- [ ] 任一 Stage6 P0 gate fail 或无独立 QMT CR 时 `admission_status=blocked`。
- [ ] `qmt_api_call`、`real_order`、`account_query`、`order_cancel`、`broker_lake_write` 均为 0。
- [ ] `order_intent_draft_v1` 只作为草稿引用，不生成可提交订单。
- [ ] credential read、gateway start、simulation/live run 均为 0。

## 阻塞说明

本 Story 必须等待 S05、S06、CR019-S01 和 CR025-S03 合同冻结，并通过 CP5 全量 LLD 确认。真实 QMT 或 simulation 请求必须转 CR-020..CR-024。
