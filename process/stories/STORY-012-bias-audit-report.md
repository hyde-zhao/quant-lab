---
story_id: "STORY-012"
title: "偏差审计报告"
story_slug: "bias-audit-report"
status: "package-ready-for-review"
priority: "P1"
wave: "W3"
depends_on: ["STORY-010", "STORY-011"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
---

# STORY-012：偏差审计报告

## 目标

输出真实性增强前后的偏差审计报告，量化非 PIT、幸存者偏差、停牌、涨跌停、事件时点和成交假设对结果的影响。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-046, REQ-058 |
| HLD | §14, §17 偏差审计报告, §16 M3 |
| ADR | ADR-007 |

## 开发上下文（dev_context）

**背景说明**：M3 增强不仅要增加约束，还要解释约束对收益、回撤、换手和候选排序的影响。本 Story 是 M3 的收敛审计输出。

**输入文件**：增强前后回测结果、`engine/universe.py`、`engine/trade_status.py`、`engine/trading_constraints.py`、`engine/events.py`、`engine/reporting.py`。

**输出文件**：`engine/bias_audit.py`、`reports/bias_audit_report.*`。

**接口约定**：Bias Audit 接收 baseline result 和 enhanced result，输出启用约束清单、未启用限制项、受影响样本数、核心指标变化和候选排序变化。

**错误约定**：缺少 baseline 或 enhanced result 时审计失败；某类增强未启用时必须标记为未启用，而不是静默省略。

**设计约束**：审计报告不自动调用聚宽；不新增交易规则；仅消费已有回测与增强结果。

**命名规范**：报告字段使用 `constraint_name`、`enabled`、`affected_samples`、`metric_delta`、`candidate_rank_delta`。

**平台目标**：本地 Python 研究工具；为后续聚宽人工验证提供解释材料。

### 文件布局边界

```text
engine/
└── bias_audit.py
reports/
└── bias_audit_report.*
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S012-T1 | 创建 | `engine/bias_audit.py` | 实现 baseline/enhanced 结果对比 |
| S012-T2 | 创建 | `engine/bias_audit.py` | 汇总约束启用、样本影响和指标变化 |
| S012-T3 | 创建 | `reports/bias_audit_report.*` | 由审计入口输出报告 |
| S012-T4 | 修改 | `engine/reporting.py` | 复用 metadata 限制项字段 |

## 验证上下文（validation_context）

**验证入口**：baseline/enhanced 结果 fixture、候选排序 fixture、报告字段检查。

**验证方式**：单元测试 + 人工检查审计解释。

**依赖环境**：Python 3.11+、uv、pandas；不需要联网。

**关键验证场景**：启用 PIT 后候选变化、启用不可交易约束后换手变化、某类约束未启用的报告披露。

## 量化验收标准（acceptance_criteria）

- [ ] 审计报告至少覆盖 5 类限制项：非 PIT/幸存者偏差、停牌/无成交、涨跌停、事件时点、成交假设。
- [ ] 对每类启用约束输出 `enabled`、`affected_samples`、`impact_summary`。
- [ ] 至少输出 4 类指标变化：收益、回撤、换手、候选排序。
- [ ] 未启用约束不得省略，必须标记剩余限制。
- [ ] 报告生成不触发网络调用或聚宽任务。

## 后续 LLD 输入约束

LLD 必须定义审计输入对象、指标 delta 计算、候选排序比较、报告输出格式和缺失增强结果的失败行为。

## 阻塞说明

无。
