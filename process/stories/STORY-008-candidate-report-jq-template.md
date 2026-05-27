---
story_id: "STORY-008"
title: "候选报告与聚宽人工验证模板"
story_slug: "candidate-report-jq-template"
status: "package-ready-for-review"
priority: "P0"
wave: "W2"
depends_on: ["STORY-007"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
---

# STORY-008：候选报告与聚宽人工验证模板

## 目标

从扫描结果中选择不超过 4 组候选参数，输出可供用户手动回填聚宽的候选 CSV 和方向一致性差异分析字段。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-018, REQ-028, REQ-029, REQ-030, REQ-041 |
| HLD | §11, §12.3, §16 M2 |
| ADR | ADR-001, ADR-007 |

## 开发上下文（dev_context）

**背景说明**：本地扫描的价值是把 60 组平台任务降到不超过 4 组候选。第一版只支持用户手动回填聚宽，不自动调用或轮询平台。

**输入文件**：`reports/momentum_param_sweep_local.csv`、`engine/reporting.py`、质量报告摘要。

**输出文件**：`engine/candidates.py`、`reports/momentum_candidates_local.csv`。

**接口约定**：Candidate Builder 读取扫描 CSV，选择默认参数、Sharpe 最优、收益最优、保守低换手参数，去重后输出候选字段、选择理由、聚宽回填字段和差异分析字段。

**错误约定**：扫描 CSV 不存在或无成功参数时候选生成失败；候选类型去重后少于 4 组允许，但必须记录原因。

**设计约束**：不得自动调用聚宽；候选报告 metadata 必须继承扫描报告限制项；方向一致性不要求逐日净值一致。

**命名规范**：候选类型使用 `default`、`best_sharpe`、`best_return`、`conservative_low_turnover`。

**平台目标**：本地 Python 研究工具 + 聚宽人工验证边界。

### 文件布局边界

```text
engine/
└── candidates.py
reports/
└── momentum_candidates_local.csv
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S008-T1 | 创建 | `engine/candidates.py` | 实现候选选择、去重和排序 |
| S008-T2 | 创建 | `engine/candidates.py` | 生成聚宽手动回填字段和选择理由 |
| S008-T3 | 创建 | `reports/momentum_candidates_local.csv` | 由候选生成入口输出 CSV |
| S008-T4 | 修改 | `engine/reporting.py` | 复用限制项 metadata 和差异分析字段 |

## 验证上下文（validation_context）

**验证入口**：扫描 CSV fixture、候选选择测试、候选 CSV 字段检查。

**验证方式**：单元测试 + 人工检查候选理由。

**依赖环境**：Python 3.11+、uv、pandas；不需要聚宽账号或网络。

**关键验证场景**：四类候选均不同、候选去重少于 4、扫描无成功行、metadata 限制项继承。

## 量化验收标准（acceptance_criteria）

- [ ] 候选 CSV 行数 `<= 4`。
- [ ] 候选覆盖默认参数、Sharpe 最优、收益最优、保守低换手参数；若去重导致缺项，必须记录去重原因。
- [ ] 每行 `selection_reason` 非空。
- [ ] 候选报告包含聚宽手动回填所需参数字段：`lookback_days`、`rebalance_freq`、`top_fraction`、`sell_buffer`。
- [ ] 候选生成过程不调用聚宽、不联网、不创建平台任务。

## 后续 LLD 输入约束

LLD 必须定义默认参数、保守低换手排序规则、候选去重规则、差异分析字段和候选失败行为。

## 阻塞说明

无。
