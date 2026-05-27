---
story_id: "STORY-007"
title: "60 组参数扫描报告"
story_slug: "parameter-sweep-report"
status: "package-ready-for-review"
priority: "P0"
wave: "W2"
depends_on: ["STORY-006"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
---

# STORY-007：60 组参数扫描报告

## 目标

实现默认动量参数网格扫描，输出 60 行 `reports/momentum_param_sweep_local.csv`，失败组合保留行并记录错误。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-011, REQ-012, REQ-026, REQ-027, REQ-032, REQ-034 |
| HLD | §12.3, §13, §16 M2 |
| ADR | ADR-001, ADR-006, ADR-007 |

## 开发上下文（dev_context）

**背景说明**：M2 的第一部分是把单次回测变成可重复扫描的本地研究能力，减少聚宽任务数量。扫描主路径必须离线。

**输入文件**：`engine/backtest.py`、`engine/reporting.py`、`reports/data_quality_report.*`、本地 parquet/manifest。

**输出文件**：`engine/scanner.py`、`reports/momentum_param_sweep_local.csv`。

**接口约定**：Scanner 接收 `lookbacks`、`rebalance_freqs`、`fractions`、成本参数和回测区间；对每组参数调用单次回测入口；输出每组参数、指标、metadata、`scan_elapsed_seconds`、`status`、`error_message`。

**错误约定**：数据合同 fail 终止全局扫描；单组参数失败保留一行 `status=failed`，其他组合继续；失败行指标可为空但参数字段、状态和错误信息必须非空。

**设计约束**：默认网格为 `5 * 4 * 3 = 60`；扫描不得联网，不得因缺口调用 data_prep；样本内过拟合警示必须进入报告。

**命名规范**：扫描列表参数为 `lookbacks`、`rebalance_freqs`、`fractions`；输出行字段为 `lookback_days`、`rebalance_freq`、`top_fraction`。

**平台目标**：本地 Python 研究工具；CSV 是必需输出，Notebook/热力图不是阻塞项。

### 文件布局边界

```text
engine/
└── scanner.py
reports/
└── momentum_param_sweep_local.csv
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S007-T1 | 创建 | `engine/scanner.py` | 构造默认 60 组参数网格 |
| S007-T2 | 创建 | `engine/scanner.py` | 调用单次回测并捕获单组失败 |
| S007-T3 | 创建 | `engine/scanner.py` | 写出扫描 CSV 和 `scan_elapsed_seconds` |
| S007-T4 | 修改 | `engine/reporting.py` | 复用单次 metadata 并补充过拟合警示 |

## 验证上下文（validation_context）

**验证入口**：fake backtest 函数、参数网格测试、扫描 CSV 字段检查。

**验证方式**：单元测试 + CSV 结构检查 + 无网络检查。

**依赖环境**：Python 3.11+、uv、pandas；不要求真实 AKShare。

**关键验证场景**：60 组全部成功、部分组合失败保留行、数据合同 fail 全局终止、断网扫描。

## 量化验收标准（acceptance_criteria）

- [ ] 默认参数网格输出恰好 60 行。
- [ ] CSV 至少包含需求报告 schema 中的 26 类字段，包括 `status`、`error_message`、`scan_elapsed_seconds`、`data_quality_status`。
- [ ] 单组失败不会减少总行数，失败行 `status=failed` 且 `error_message` 非空。
- [ ] 扫描主路径网络调用次数为 0。
- [ ] 报告包含样本内选择或过拟合警示字段。

## 后续 LLD 输入约束

LLD 必须定义扫描入口签名、默认参数来源、CSV 写入策略、失败行 schema、耗时统计口径和无网络验证方式。

## 阻塞说明

无。
