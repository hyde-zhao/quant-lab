---
story_id: "STORY-006"
title: "指标、单次回测报告与 metadata"
story_slug: "backtest-metrics-report-metadata"
status: "package-ready-for-review"
priority: "P0"
wave: "W1"
depends_on: ["STORY-005"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
---

# STORY-006：指标、单次回测报告与 metadata

## 目标

完成单次动量回测编排、绩效指标计算和报告 metadata 输出，为参数扫描提供稳定可复用入口。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-010, REQ-015, REQ-017, REQ-023, REQ-024, REQ-025, REQ-031, REQ-035, REQ-041 |
| HLD | §12.2, §13, §14, §16 M1 |
| ADR | ADR-002, ADR-003, ADR-004, ADR-007 |

## 开发上下文（dev_context）

**背景说明**：M1 的退出标志是 2019-2025 默认动量回测可输出完整净值、指标和限制项 metadata。本 Story 也为 STORY-007 扫描入口提供单组回测函数。

**输入文件**：`engine/data_loader.py`、`strategies/momentum.py`、`engine/portfolio.py`、`reports/data_quality_report.*`。

**输出文件**：`engine/backtest.py`、`engine/metrics.py`、`engine/reporting.py`。

**接口约定**：Backtest 接收日期、策略参数、成本参数和数据路径；返回 nav series、positions/trades/costs、metrics dict、metadata dict；Report Builder 可把单次结果转为扫描行或候选字段的公共 metadata。

**错误约定**：数据合同 fail 时拒绝运行；warn 可运行但报告必须披露；无质量报告时默认失败。

**设计约束**：报告 metadata 必须包含复权口径、信号/成交时点、available_at 规则、固定当前沪深 300、`is_pit_universe=false`、幸存者偏差、停牌、涨跌停、新股、退市、ST、财报披露日和历史成分变化限制。

**命名规范**：指标字段使用 `total_return`、`annual_return`、`max_drawdown`、`sharpe`、`turnover`、`final_nav`。

**平台目标**：本地 Python 研究工具；默认回测主路径离线运行。

### 文件布局边界

```text
engine/
├── backtest.py
├── metrics.py
└── reporting.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S006-T1 | 创建 | `engine/backtest.py` | 串联 loader、momentum、portfolio、metrics、reporting |
| S006-T2 | 创建 | `engine/metrics.py` | 计算累计收益、年化收益、最大回撤、Sharpe、换手 |
| S006-T3 | 创建 | `engine/reporting.py` | 统一生成 metadata 和报告行字段 |
| S006-T4 | 修改 | `engine/contracts.py` | 固化指标与 metadata 字段常量 |

## 验证上下文（validation_context）

**验证入口**：合成价格数据回测、指标 fixture、metadata 字段检查。

**验证方式**：单元测试 + 人工检查报告字典。

**依赖环境**：Python 3.11+、uv、pandas；不需要联网。

**关键验证场景**：完整区间净值、最大回撤、Sharpe、换手、质量 warn 披露、限制项 metadata 一致性。

## 量化验收标准（acceptance_criteria）

- [ ] 合规 2019-01-01 至 2025-12-31 数据可输出完整日净值序列。
- [ ] 指标至少包含 5 项：累计收益、年化收益、最大回撤、Sharpe、换手。
- [ ] metadata 至少覆盖 HLD 成功标准要求的 10 类限制项。
- [ ] 成本参数 `commission_rate`、`slippage_rate`、`sell_tax_rate` 的实际值进入报告。
- [ ] 单次回测入口可被 STORY-007 以 60 组参数重复调用，且无全局可变状态依赖。

## 后续 LLD 输入约束

LLD 必须定义回测结果对象、指标公式、年化交易日数、无风险利率默认值、metadata schema、报告 builder 与扫描层复用方式。

## 阻塞说明

无。
