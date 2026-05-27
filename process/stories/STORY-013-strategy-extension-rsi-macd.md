---
story_id: "STORY-013"
title: "策略扩展接口与 RSI/MACD 示例"
story_slug: "strategy-extension-rsi-macd"
status: "package-ready-for-review"
priority: "P2"
wave: "W4"
depends_on: ["STORY-008"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
---

# STORY-013：策略扩展接口与 RSI/MACD 示例

## 目标

在不改变组合层、指标层和扫描层主契约的前提下，预留并示范 RSI/MACD 等策略纯函数接口。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-019, REQ-033 |
| HLD | §16 M4, §17 RSI/MACD 策略扩展 |
| ADR | ADR-002 |

## 开发上下文（dev_context）

**背景说明**：HLD 要求第一版先完成动量主路径，再复用同一研究底座扩展指标型策略。此 Story 不应把回测层重构成大型框架。

**输入文件**：`strategies/momentum.py`、`engine/backtest.py`、`engine/scanner.py`、`engine/reporting.py`。

**输出文件**：`strategies/base.py`、`strategies/rsi.py`、`strategies/macd.py`，必要时修改 `engine/scanner.py` 和 `engine/reporting.py` 以支持 `strategy_name` 字段。

**接口约定**：策略函数接收 price matrix、当前持仓和策略参数，返回目标股票集合或目标权重前置集合；组合层仍只消费目标，不关心策略实现。

**错误约定**：策略参数非法时单组扫描失败并保留失败行；策略函数不得读写文件或联网。

**设计约束**：Notebook、热力图和图形化展示不是阻塞项；新增策略必须复用 Data Loader、Portfolio、Metrics 和 Reporting。

**命名规范**：策略名使用 `momentum`、`rsi`、`macd`；通用参数字段增加 `strategy_name`。

**平台目标**：本地 Python 研究工具；扩展不阻塞 M0-M2 第一版本地主路径。

### 文件布局边界

```text
strategies/
├── base.py
├── rsi.py
└── macd.py
engine/
├── scanner.py
└── reporting.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S013-T1 | 创建 | `strategies/base.py` | 定义策略纯函数接口和结果对象 |
| S013-T2 | 创建 | `strategies/rsi.py` | 实现 RSI 示例策略函数 |
| S013-T3 | 创建 | `strategies/macd.py` | 实现 MACD 示例策略函数 |
| S013-T4 | 修改 | `engine/scanner.py` | 支持按 `strategy_name` 分派策略 |
| S013-T5 | 修改 | `engine/reporting.py` | 报告增加策略名和策略参数字段 |

## 验证上下文（validation_context）

**验证入口**：策略函数单元测试、扫描分派测试、报告字段检查。

**验证方式**：单元测试 + 回归测试动量策略仍可运行。

**依赖环境**：Python 3.11+、uv、pandas；不需要联网。

**关键验证场景**：RSI 示例输出目标集合、MACD 示例输出目标集合、动量主路径回归、策略参数非法失败行保留。

## 量化验收标准（acceptance_criteria）

- [ ] 至少 2 个新策略函数示例：RSI 与 MACD。
- [ ] 新策略函数 100% 不读写文件、不联网、不依赖回测全局状态。
- [ ] 组合层和指标层主接口无需为 RSI/MACD 单独改造。
- [ ] 扫描或报告可区分 `strategy_name`。
- [ ] Notebook、热力图或图形化展示缺失不阻塞验收。

## 后续 LLD 输入约束

LLD 必须定义策略接口对象、RSI/MACD 参数、策略分派机制、报告 schema 扩展和动量回归验证范围。

## 阻塞说明

无。
