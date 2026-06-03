---
story_id: "CR030-S05-multifactor-combiner-portfolio-plan"
title: "多因子组合与组合计划"
story_slug: "multifactor-combiner-portfolio-plan"
status: "verified"
priority: "P0"
wave: "CR030-W3-COMBINATION-MANIFEST"
depends_on:
  - "CR030-S04-factor-evaluation-report"
dependency_type:
  - upstream: "CR030-S04-factor-evaluation-report"
    type: "evaluation-report-contract"
cp5_batch: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/multifactor_combiner.py"
    - "tests/test_cr030_multifactor_combiner.py"
  shared:
    - "engine/factor_evaluation.py"
    - "engine/order_intent_draft.py"
  merge_owner: "CR030-S05-multifactor-combiner-portfolio-plan"
  forbidden:
    - "optimizer / cvxpy dependency"
    - "Qlib EnhancedIndexing runtime"
    - "vectorbt optimizer runtime"
    - "broker order generation"
    - "pyproject.toml"
    - "uv.lock"
lld_gate:
  required_inputs:
    - "process/HLD.md#35.6"
    - "process/HLD.md#35.8"
    - "process/HLD.md#35.13"
    - "process/ARCHITECTURE-DECISION.md#ADR-083"
    - "process/stories/CR030-S05-multifactor-combiner-portfolio-plan.md"
  status: "approved"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  qmt_operation_allowed: false
  credential_read_allowed: false
task_count: 5
created_at: "2026-06-03T08:30:00+08:00"
updated_at: "2026-06-03T10:47:33+08:00"
change_id: "CR-030"
dev_dispatch:
  mode: "spawn_agent"
  agent_id: "019e8b4e-a692-7f00-aa91-7c748ddd6a33"
  agent_name: "dev-qin"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-03T10:27:37+08:00"
  completed_at: "2026-06-03T10:35:14+08:00"
  closed_at: "2026-06-03T10:38:08+08:00"
  cp6_checkpoint: "process/checks/CP6-CR030-S05-multifactor-combiner-portfolio-plan-CODING-DONE.md"
  handoff_path: "process/handoffs/META-DEV-CR030-S05-IMPLEMENT-2026-06-03.md"
  cp6_status: "PASS"
qa_dispatch:
  mode: "spawn_agent"
  agent_id: "019e8b5b-e2a5-7ee1-ac1d-ce832731cccf"
  agent_name: "qa-kong"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-03T10:42:02+08:00"
  completed_at: "2026-06-03T10:43:26+08:00"
  closed_at: "2026-06-03T10:47:33+08:00"
  cp7_checkpoint: "process/checks/CP7-CR030-S05-multifactor-combiner-portfolio-plan-VERIFICATION-DONE.md"
  handoff_path: "process/handoffs/META-QA-CR030-S05-CP7-VERIFY-2026-06-03.md"
  cp7_status: "PASS"
---

# CR030-S05：多因子组合与组合计划

## 目标

定义 P0 `MultiFactorCombiner` 和 `MultiFactorPortfolioPlan`，采用可解释规则权重或轻量线性组合，记录标准化、winsorization、中性化、正交化、缺失值处理、约束、成本、容量、调仓频率和 blocked reason。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-25、TS-030-06 |
| 需求 | REQ-179、REQ-182、REQ-185 |
| HLD | `process/HLD.md` §35.6、§35.8、§35.13 |
| ADR | ADR-083 |

## 开发上下文（dev_context）

**背景说明**：CR-030 需要从单因子评价进入多因子组合，但 CP3 已确认 P0 不采用 optimizer / ML workflow。组合输出只能是组合计划或 draft handoff 输入，不能生成 broker order。

**输入文件**：CR030-S04 评价报告合同、HLD §35、ADR-083、本 Story 卡片。

**输出文件**：`engine/multifactor_combiner.py`、`tests/test_cr030_multifactor_combiner.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| 输入 | 多个 `FactorEvaluationReport`、组合配置、benchmark、universe、cost、exposure、rebalance |
| 输出 | `MultiFactorPortfolioPlan`、权重来源、约束、成本容量说明、blocked claims |
| P0 策略 | 规则权重 / 轻量线性组合 |
| Spike | optimizer、cvxpy、EnhancedIndexing、ML weighting 仅登记后续条件 |

**设计约束**：不得新增 optimizer 依赖；不得调用 Qlib / vectorbt runtime；不得生成真实订单。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR030-S04 | evaluation-report-contract | 评价报告字段冻结 | 评价报告不足时组合 blocked | 组合只消费合格或 research_limited 报告 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/multifactor_combiner.py`、`tests/test_cr030_multifactor_combiner.py` | 当前 Story 独占 |
| shared | `engine/factor_evaluation.py`、`engine/order_intent_draft.py` | 只写组合计划，不写订单 |
| forbidden | optimizer dependency、Qlib runtime、vectorbt runtime、broker order | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR030-S05-T1 | 设计 | `engine/multifactor_combiner.py` | 定义 combiner、portfolio plan 和约束合同 |
| CR030-S05-T2 | 设计 | `tests/test_cr030_multifactor_combiner.py` | 设计规则权重、缺失值、约束和 optimizer blocked fixture |
| CR030-S05-T3 | 约束 | optimizer Spike | 明确 optimizer 后置条件 |
| CR030-S05-T4 | 约束 | order boundary | 确认组合计划不是 broker order |
| CR030-S05-T5 | 约束 | cost/capacity | 定义成本、换手、容量和 benchmark 偏离字段 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr030_multifactor_combiner.py`，但本阶段不执行。

**验证方式**：合同测试、optimizer forbidden scan、order generation forbidden scan。

**依赖环境**：本地 fixture；不得安装 optimizer 依赖或运行外部项目。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| 多个合格 report | 输出可解释 portfolio plan |
| 需要 optimizer | 输出 Spike / blocked reason |
| 缺成本或暴露 | `research_limited` 或 blocked claims |
| 生成 broker order | 测试失败 |

## 量化验收标准（acceptance_criteria）

- [ ] P0 组合只使用规则权重或轻量线性组合。
- [ ] optimizer / cvxpy / EnhancedIndexing / vectorbt runtime 启用次数为 0。
- [ ] `MultiFactorPortfolioPlan` 包含权重、约束、成本、容量、调仓和 claims 字段。
- [ ] 真实 broker order 生成次数为 0。
- [ ] 依赖变更、QMT 调用、credential read 均为 0。

## 阻塞说明

本 Story 必须等待 S04 评价合同冻结和 CP5 全量 LLD 确认。任何 optimizer 或 ML workflow 请求必须转后续 Spike。
