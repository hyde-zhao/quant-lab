---
story_id: "CR030-S04-factor-evaluation-report"
title: "单因子评价报告标准化"
story_slug: "factor-evaluation-report"
status: "verified"
priority: "P0"
wave: "CR030-W2-PANEL-EVALUATION"
depends_on:
  - "CR030-S03-factor-panel-label-window-fail-closed"
dependency_type:
  - upstream: "CR030-S03-factor-panel-label-window-fail-closed"
    type: "panel-label-contract"
cp5_batch: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/factor_evaluation.py"
    - "reports/factor_evaluation/**"
    - "tests/test_cr030_factor_evaluation_report.py"
  shared:
    - "engine/factor_panel_contracts.py"
    - "reports/research_catalog/**"
  merge_owner: "CR030-S04-factor-evaluation-report"
  forbidden:
    - "old experiment report overwrite"
    - "Alphalens runtime"
    - "production-valid claim from single full-sample metric"
    - "provider fetch"
    - "lake write"
    - "pyproject.toml"
    - "uv.lock"
lld_gate:
  required_inputs:
    - "process/HLD.md#35.6"
    - "process/HLD.md#35.8"
    - "process/HLD.md#35.13"
    - "process/ARCHITECTURE-DECISION.md#ADR-082"
    - "process/ARCHITECTURE-DECISION.md#ADR-084"
    - "process/stories/CR030-S04-factor-evaluation-report.md"
  status: "approved"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  external_project_run_allowed: false
  credential_read_allowed: false
task_count: 5
created_at: "2026-06-03T08:30:00+08:00"
updated_at: "2026-06-03T10:21:23+08:00"
change_id: "CR-030"
---

# CR030-S04：单因子评价报告标准化

## 目标

标准化 `FactorEvaluationReport`，覆盖 coverage、IC、RankIC、ICIR、分层收益、多空收益、turnover、成本敏感性、暴露、年度 / rolling / 市场状态分层、allowed / blocked claims 和 catalog 入口。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-24、TS-030-05 |
| 需求 | REQ-178、REQ-182、REQ-185 |
| HLD | `process/HLD.md` §35.6、§35.8、§35.13 |
| ADR | ADR-082、ADR-084 |

## 开发上下文（dev_context）

**背景说明**：单因子评价需要支撑研究者判断因子能否进入组合，但不得用单一全样本 IC 或收益曲线声明生产有效，也不得覆盖旧实验报告。

**输入文件**：CR030-S03 面板 / 标签 gate、HLD §35、ADR-082/084、本 Story 卡片。

**输出文件**：`engine/factor_evaluation.py`、`reports/factor_evaluation/**`、`tests/test_cr030_factor_evaluation_report.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| report 输入 | validated panel、label、benchmark、cost、exposure、evaluation window |
| report 输出 | metrics table、layered returns、turnover、exposure、claims、status、evidence refs |
| status | `pass`、`warn`、`fail`、`blocked`、`research_limited` |
| catalog | 报告路径和 claim boundary 可被 S06 catalog 索引 |

**设计约束**：不得运行 Alphalens；不得覆盖旧 reports；输入 gate fail 时只能输出 blocked / research_limited。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR030-S03 | panel-label-contract | S03 gate 合同冻结 | gate fail 不得继续评价 | 防止泄漏进入评价报告 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/factor_evaluation.py`、`reports/factor_evaluation/**`、`tests/test_cr030_factor_evaluation_report.py` | 当前 Story 独占 |
| shared | `engine/factor_panel_contracts.py`、`reports/research_catalog/**` | 与 S06 合并 catalog 字段需串行 |
| forbidden | 旧报告覆盖、Alphalens runtime、provider/lake/依赖 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR030-S04-T1 | 设计 | `engine/factor_evaluation.py` | 定义单因子评价合同、指标和状态 |
| CR030-S04-T2 | 设计 | `reports/factor_evaluation/**` | 设计 JSON/CSV/Markdown artifact 形态 |
| CR030-S04-T3 | 设计 | `tests/test_cr030_factor_evaluation_report.py` | 设计 IC、RankIC、分层收益、blocked claims fixture |
| CR030-S04-T4 | 约束 | old reports | 说明旧实验报告只读保留，禁止覆盖 |
| CR030-S04-T5 | 约束 | claim boundary | 定义 allowed / blocked claims 和生产声明限制 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr030_factor_evaluation_report.py`，但本阶段不执行。

**验证方式**：指标字段合同测试、gate fail blocked 测试、报告声明扫描。

**依赖环境**：本地 fixture；不得运行外部项目、provider 或 lake。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| 合格 panel / label | 输出完整 metrics 和 claims |
| 输入 gate fail | status=`blocked`，不输出生产声明 |
| 缺 exposure / cost | `research_limited` 或 blocked claims |
| 单一全样本指标声明生产有效 | 扫描失败 |

## 量化验收标准（acceptance_criteria）

- [ ] `FactorEvaluationReport` 至少覆盖 coverage、IC、RankIC、ICIR、分层收益、多空收益、turnover、成本敏感性、暴露和 claims。
- [ ] 输入 gate fail 时生产有效声明次数为 0。
- [ ] 旧报告覆盖次数为 0。
- [ ] Alphalens runtime / external project run 次数为 0。
- [ ] provider fetch、lake write、credential read、QMT 调用均为 0。

## 阻塞说明

本 Story 必须等待 S03 gate 合同冻结和 CP5 全量 LLD 确认。若评价输入不足，后续实现只能输出 blocked / research_limited，不得扩大声明。
