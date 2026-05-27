---
story_id: "STORY-010"
title: "交易状态与不可交易约束"
story_slug: "trade-status-constraints"
status: "package-ready-for-review"
priority: "P1"
wave: "W3"
depends_on: ["STORY-009"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
---

# STORY-010：交易状态与不可交易约束

## 目标

引入交易状态表，表达停牌、无成交、特殊处理和可交易性，并让组合层按状态拒绝、延后或留现金。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-043, REQ-058 |
| HLD | §10, §17 交易状态表, §16 M3 |
| ADR | ADR-004, ADR-007 |

## 开发上下文（dev_context）

**背景说明**：第一版对停牌/无成交只做 metadata 警示或可选字段处理。真实性增强需要把不可交易状态纳入组合层成交判断。

**输入文件**：`engine/portfolio.py`、`engine/data_loader.py`、`engine/quality.py`、`engine/contracts.py`、PIT 或固定股票池输出。

**输出文件**：`engine/trade_status.py`，并修改 `engine/portfolio.py`、`engine/data_loader.py`、`engine/quality.py`、`engine/contracts.py`。

**接口约定**：Trade Status Provider 接收 symbol、trade_date，返回可交易状态、原因、`available_at` 和来源 metadata；Portfolio Engine 消费该状态决定成交、留现金或延后。

**错误约定**：状态缺失按质量配置 warn/fail；显式不可交易不得被当作成交；状态可用时点晚于决策或成交时点时拒绝使用。

**设计约束**：交易状态数据必须通过独立数据准备链路进入标准化数据；不得在组合层联网查询。

**命名规范**：不可交易原因使用稳定枚举，如 `suspended`、`no_trade`、`special_treatment`、`unknown_status`。

**平台目标**：本地 Python 研究工具；真实性增强不变更第一版动量信号纯函数契约。

### 文件布局边界

```text
engine/
├── trade_status.py
├── portfolio.py
├── data_loader.py
├── quality.py
└── contracts.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S010-T1 | 创建 | `engine/trade_status.py` | 实现交易状态读取和查询接口 |
| S010-T2 | 修改 | `engine/portfolio.py` | 在成交前应用不可交易状态约束 |
| S010-T3 | 修改 | `engine/quality.py` | 增加交易状态缺失和覆盖检查 |
| S010-T4 | 修改 | `engine/reporting.py` | 输出不可交易原因统计 |

## 验证上下文（validation_context）

**验证入口**：交易状态 fixture、组合成交测试、报告统计检查。

**验证方式**：单元测试 + 回归测试。

**依赖环境**：Python 3.11+、uv、pandas；不需要联网。

**关键验证场景**：停牌买入失败留现金、停牌卖出延后或保留、无成交记录、状态缺失 warn/fail。

## 量化验收标准（acceptance_criteria）

- [ ] 显式不可交易目标 100% 不生成真实成交记录。
- [ ] 每个未成交目标均输出非空 `unfilled_reason`。
- [ ] 报告输出至少 4 类不可交易统计：停牌、无成交、特殊处理、未知状态。
- [ ] 状态数据新增字段同步进入 raw、manifest、quality、loader 四类契约。
- [ ] 回归验证中未启用交易状态时，M0-M2 第一版主路径行为保持兼容。

## 后续 LLD 输入约束

LLD 必须定义交易状态 parquet schema、状态优先级、买入/卖出限制差异、留现金或延后策略和与涨跌停约束的组合顺序。

## 阻塞说明

无。
