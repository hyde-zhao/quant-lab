---
story_id: "STORY-005"
title: "动量信号与组合成交引擎"
story_slug: "momentum-portfolio-engine"
status: "package-ready-for-review"
priority: "P0"
wave: "W1"
depends_on: ["STORY-004"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
---

# STORY-005：动量信号与组合成交引擎

## 目标

实现动量策略纯函数、目标持仓选择、T+1 收盘成交、成本扣除、现金留存和缺失/不可交易原因记录。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-039, REQ-040 |
| HLD | §9.2, §10, §12.2, §16 M1 |
| ADR | ADR-002, ADR-004 |

## 开发上下文（dev_context）

**背景说明**：动量策略是本地回测层的核心业务规则。策略层必须保持纯函数；组合层负责成交、成本、现金和净值，不计算选股信号。

**输入文件**：`engine/data_loader.py` 输出对象、`engine/contracts.py`、HLD §9.2 成交口径。

**输出文件**：`strategies/momentum.py`、`engine/portfolio.py`。

**接口约定**：动量函数接收 `close_df` 历史窗口、当前持仓、`lookback_days`、`top_fraction`、`sell_buffer`，返回 target_symbols 和 filtering_stats；组合函数接收目标、价格、成本参数和当前持仓，返回 nav、positions、trades、costs、unfilled reasons。

**错误约定**：历史窗口不足和信号端点价格缺失在信号层剔除；成交价缺失、显式停牌或未知不可交易在组合层留现金并记录原因；关键输入完全缺失时失败。

**设计约束**：成交日不得早于 T+1；成本包含 `commission_rate`、`slippage_rate`、`sell_tax_rate`；不得静默填充价格。

**命名规范**：策略参数名使用 `lookback_days`、`rebalance_freq`、`top_fraction`、`sell_buffer`；扫描列表名留给 STORY-007 使用 `lookbacks`、`rebalance_freqs`、`fractions`。

**平台目标**：本地 Python 研究工具；不引入完整订单簿或实盘接口。

### 文件布局边界

```text
strategies/
└── momentum.py
engine/
└── portfolio.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S005-T1 | 创建 | `strategies/momentum.py` | 实现动量收益、排名、top_fraction 和 sell_buffer 纯函数 |
| S005-T2 | 创建 | `engine/portfolio.py` | 实现等权目标、T+1 成交、现金留存和成本扣除 |
| S005-T3 | 创建 | `engine/portfolio.py` | 实现未成交原因、成本明细和持仓更新记录 |
| S005-T4 | 修改 | `engine/contracts.py` | 补充交易、成本、过滤原因常量 |

## 验证上下文（validation_context）

**验证入口**：小型价格矩阵 fixture、已知排名结果、缺失成交价 fixture。

**验证方式**：单元测试 + 人工检查交易明细。

**依赖环境**：Python 3.11+、uv、pandas；不需要真实行情和网络。

**关键验证场景**：20 日动量公式、top 10% 选择、sell_buffer 保留、T+1 成交、买卖成本扣除、缺失成交价留现金。

## 量化验收标准（acceptance_criteria）

- [ ] 动量计算公式固定为 `close[T] / close[T-lookback_days] - 1`。
- [ ] 历史窗口不足或端点价格缺失的股票 100% 不参与排名。
- [ ] 任一成交记录的成交日不早于信号日后第 1 个可成交交易日。
- [ ] 成本明细至少包含佣金、滑点、卖出税 3 类字段。
- [ ] 缺失成交价、无成交或不可交易目标不得作为真实成交，且未成交原因非空。

## 后续 LLD 输入约束

LLD 必须定义目标权重算法、现金收益处理、成本扣除顺序、持仓数据结构、过滤原因枚举和与 STORY-006 指标层的结果接口。

## 阻塞说明

无。
