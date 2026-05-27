---
story_id: "STORY-011"
title: "涨跌停与事件 available_at 增强"
story_slug: "limit-event-available-at"
status: "package-ready-for-review"
priority: "P1"
wave: "W3"
depends_on: ["STORY-009", "STORY-010"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
---

# STORY-011：涨跌停与事件 available_at 增强

## 目标

增量接入涨跌停成交约束和事件级 `available_at` 门控，防止不可成交价格和未来事件字段进入决策。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-044, REQ-045, REQ-058 |
| HLD | §9.3, §10, §17 涨跌停约束与事件级 `available_at`, §16 M3 |
| ADR | ADR-006, ADR-007 |

## 开发上下文（dev_context）

**背景说明**：第一版不强制涨跌停字段，也不把财报/公告/ST 事件作为信号输入。增强阶段需要把这些字段作为显式可选能力，并严格执行可用时点；本 Story 在成交约束顺序上依赖 STORY-010 的交易状态检查先执行。

**输入文件**：`engine/data_loader.py`、`engine/portfolio.py`、`engine/quality.py`、`engine/contracts.py`、`engine/normalizer.py`。

**输出文件**：`engine/trading_constraints.py`、`engine/events.py`，并修改 `engine/data_loader.py`、`engine/portfolio.py`、`engine/quality.py`、`engine/contracts.py`。

**接口约定**：Trading Constraints 接收 symbol、trade_date、side、execution_price，返回是否可成交和原因；Event Loader 只允许具备字段级 `available_at` 的事件进入信号或过滤。

**错误约定**：涨停买入或跌停卖出按约束拒绝或延后；事件字段缺 `available_at` 或 `available_at > decision_time` 时失败；不得用财报报告期日期替代披露日。

**设计约束**：事件字段默认不进入动量第一版信号；启用事件过滤必须有 LLD 明确配置和测试。

**命名规范**：涨跌停字段使用 `limit_up`、`limit_down`；事件字段必须包含 `event_type`、`event_date`、`available_at`、`source`。

**平台目标**：本地 Python 研究工具；增强仍保持回测主路径离线。

### 文件布局边界

```text
engine/
├── trading_constraints.py
├── events.py
├── data_loader.py
├── portfolio.py
├── quality.py
└── contracts.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S011-T1 | 创建 | `engine/trading_constraints.py` | 实现涨跌停成交约束判断 |
| S011-T2 | 创建 | `engine/events.py` | 实现事件级 `available_at` 校验接口 |
| S011-T3 | 修改 | `engine/portfolio.py` | 在成交前消费涨跌停约束 |
| S011-T4 | 修改 | `engine/quality.py` | 增加涨跌停和事件字段质量检查 |

## 验证上下文（validation_context）

**验证入口**：涨跌停 fixture、事件 fixture、组合成交测试、未来函数失败测试。

**验证方式**：单元测试 + 报告字段检查。

**依赖环境**：Python 3.11+、uv、pandas；不需要联网。

**关键验证场景**：涨停买入拒绝、跌停卖出拒绝、事件 `available_at` 晚于决策失败、事件字段未启用时不影响动量主路径。

## 量化验收标准（acceptance_criteria）

- [ ] 涨停买入和跌停卖出场景 100% 记录拒绝或延后原因。
- [ ] 事件字段缺少 `available_at` 时 100% 不允许进入信号或过滤。
- [ ] 事件 `available_at > decision_time` 时 100% 失败并输出可定位错误。
- [ ] 报告 metadata 说明启用/未启用的涨跌停和事件约束。
- [ ] 新增字段同步进入 raw、manifest、quality、loader 四类契约。

## 后续 LLD 输入约束

LLD 必须定义涨跌停成交判定细节、事件 schema、事件启用配置、与交易状态约束的顺序，以及未来函数测试矩阵。

## 阻塞说明

依赖 `STORY-009` 的 PIT/fixed 股票池增强契约和 `STORY-010` 的交易状态与不可交易约束。实现前必须确认 STORY-010 已提供组合层成交前状态检查接口或等价共享交易约束接口。
