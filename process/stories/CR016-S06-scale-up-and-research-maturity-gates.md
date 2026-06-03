---
story_id: "CR016-S06-scale-up-and-research-maturity-gates"
title: "scale_up 与研究成熟度 gate"
story_slug: "scale-up-and-research-maturity-gates"
status: "lld-approved"
priority: "P0"
wave: "CR016-W2-LIVE-SCALE-DOCS-GATED"
depends_on:
  - "CR016-S05-live-readonly-and-small-live-admission"
  - "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
  - "CR011-S08-factor-panel-audit-and-robust-validation"
dependency_type:
  - upstream: "CR016-S05-live-readonly-and-small-live-admission"
    type: "runtime"
  - upstream: "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
    type: "runtime"
  - upstream: "CR011-S08-factor-panel-audit-and-robust-validation"
    type: "contract"
cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
implementation_allowed: false
file_ownership:
  primary:
    - "trading/scale_up_gate.py"
    - "tests/test_cr016_scale_up_research_maturity_gates.py"
  shared:
    - "trading/live_admission.py"
    - "engine/research_dataset.py"
  merge_owner: "CR016-S06-scale-up-and-research-maturity-gates"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker operation without explicit authorization"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#7.4"
    - "process/ARCHITECTURE-DECISION.md#ADR-059"
    - "process/stories/CR016-S06-scale-up-and-research-maturity-gates.md"
  status: "approved"
  cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: false
  file_conflict_free: false
  implementation_allowed: false
  requires_cr017_verified: true
  later_gated_real_operation: true
created_at: "2026-05-28"
updated_at: "2026-05-28T06:24:15+08:00"
change_id: "CR-016"
---

# CR016-S06：scale_up 与研究成熟度 gate

## 目标

定义资金放大前的研究成熟度和运行稳定性 gate。CR-017 未实现验证前，scale_up 和生产策略复权治理完成声明必须 blocked；真实执行价、VWAP、minute/tick/Level2 等声明继续 blocked。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-11、UC-12 |
| 需求 | REQ-118、REQ-119、REQ-120、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §7.4、§11 |
| ADR | ADR-059、ADR-060 |

## 开发上下文（dev_context）

**背景说明**：scale_up 不只是交易链路问题，还依赖研究口径、PIT、benchmark、exposure、capacity、cost、execution claim 和 CR-017 复权治理状态。

**输入文件**：CR016-S05 live stage gate、CR017-S06 consumer boundary、CR011-S08 robust validation baseline。

**输出文件**：`trading/scale_up_gate.py`、`tests/test_cr016_scale_up_research_maturity_gates.py`；共享 `trading/live_admission.py`、`engine/research_dataset.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| scale_up_gate | small_live evidence、research maturity summary、CR017 status | pass / blocked_claims | 任一 P0 gate 缺失 blocked |
| claim evaluator | allowed/blocked claims | scale_up_claim_status | unsupported claims 不得 counted as pass |
| maturity checklist | strategy version、params、success/failure criteria | maturity_status | 缺实验注册 blocked |

**设计约束**：该 Story 不能让 scale_up 成为当前可直接实现项；只定义 gate 和 blocked claims。CR017 verified 是 scale_up 前置。

**命名规范**：`scale_up_gate_status`、`research_maturity_status`、`blocked_claims`、`cr017_adjustment_verified`。

**平台目标**：运行治理 + 研究治理交叉 gate。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR016-S05 | runtime | small_live gate 已定义 | small_live evidence 前置 | 运行稳定性 |
| CR017-S06 | runtime | adjustment consumer boundary 已定义 | CR017 verified 前 blocked | 复权治理前置 |
| CR011-S08 | contract | 研究稳健性基线可引用 | 不回滚 CR011 | 研究成熟度输入 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR016-S06-T1 | 创建 | `trading/scale_up_gate.py` | 定义 scale_up gate 和 research maturity checklist |
| CR016-S06-T2 | 创建 | `tests/test_cr016_scale_up_research_maturity_gates.py` | 覆盖 CR017 未验证、PIT/benchmark/capacity 缺失、unsupported claims |
| CR016-S06-T3 | 修改 | `engine/research_dataset.py` | 按 LLD 输出可供 gate 消费的 maturity summary |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr016_scale_up_research_maturity_gates.py`。

**验证方式**：fixture gate；不真实运行。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：CR017 未 verified blocked；缺实验注册 blocked；unsupported execution claim blocked；small_live 稳定性缺失 blocked。

## 量化验收标准（acceptance_criteria）

- [ ] scale_up gate 至少检查 CR017 verified、small_live stability、reconciliation pass、kill switch drill、research maturity 5 类前置。
- [ ] CR017 未 verified 时 scale_up allowed 次数为 0。
- [ ] unsupported VWAP / minute / tick / Level2 / order-match claim 被计入 allowed 的次数为 0。
- [ ] 默认验证 real_order_call、real_cancel_call、account_write_call、credential_read 均为 0。

## 阻塞说明

当前为 later-gated；CR017 verified、小资金阶段稳定和用户授权前不得实现真实 scale_up。
