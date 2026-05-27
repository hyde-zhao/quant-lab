---
story_id: "STORY-009"
title: "PIT 股票池 Provider 增强契约"
story_slug: "pit-universe-provider-contract"
status: "package-ready-for-review"
priority: "P1"
wave: "W3"
depends_on: ["STORY-008"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md"
---

# STORY-009：PIT 股票池 Provider 增强契约

## 目标

在第一版固定当前沪深 300 股票池之后，增量设计并实现按日期返回当时可用成分股的 PIT universe provider。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-042, REQ-058 |
| HLD | §14 R3, §17 PIT universe provider, §16 M3 |
| ADR | ADR-007 |

## 开发上下文（dev_context）

**背景说明**：固定当前沪深 300 是第一版可接受偏差，但 HLD 把 PIT universe 列为首个真实性增强项。本 Story 必须同步扩展 raw、manifest、质量报告和离线读取契约。

**输入文件**：`engine/data_prep.py`、`engine/normalizer.py`、`engine/quality.py`、`engine/data_loader.py`、`engine/contracts.py`。

**输出文件**：`engine/universe.py`，并修改 `engine/normalizer.py`、`engine/quality.py`、`engine/data_loader.py`、`engine/contracts.py`。

**接口约定**：Universe Provider 接收 decision_date 或 trade_date，返回当时可用股票池、`available_at`、index_code、PIT 标记和覆盖 metadata。

**错误约定**：成分股数据缺少可用时点或覆盖不足时按质量状态 fail/warn 处理；不得把当前快照伪装为 PIT。

**设计约束**：新增联网数据只进入 data_prep；回测仍离线读取标准化 parquet 和质量报告。

**命名规范**：PIT 字段使用 `is_pit_universe=true`、`index_code`、`effective_date`、`available_at`。

**平台目标**：本地 Python 研究工具；真实性增强不阻塞 M0-M2 第一版主路径。

### 文件布局边界

```text
engine/
├── universe.py
├── normalizer.py
├── quality.py
├── data_loader.py
└── contracts.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S009-T1 | 创建 | `engine/universe.py` | 实现按日期查询股票池的 provider 接口 |
| S009-T2 | 修改 | `engine/normalizer.py` | 扩展历史成分股标准化派生规则 |
| S009-T3 | 修改 | `engine/quality.py` | 增加成分覆盖和可用时点质量检查 |
| S009-T4 | 修改 | `engine/data_loader.py` | 支持按决策日读取 PIT 股票池 |

## 验证上下文（validation_context）

**验证入口**：历史成分股 fixture、按日期查询测试、质量报告扩展字段检查。

**验证方式**：单元测试 + 回归检查固定快照路径仍可用。

**依赖环境**：Python 3.11+、uv、pandas、pyarrow；不要求真实网络。

**关键验证场景**：同一股票池日期前后成分变化、`available_at` 晚于 decision_time 拒绝、PIT 和 fixed 模式 metadata 区分。

## 量化验收标准（acceptance_criteria）

- [ ] Provider 可对任一回测交易日返回股票池列表和 `available_at`。
- [ ] PIT 模式报告 `is_pit_universe=true`，固定快照模式仍输出 `false`。
- [ ] 质量报告增加成分覆盖字段和缺失统计。
- [ ] 新增数据字段同步进入 raw、manifest、quality、loader 四类契约。
- [ ] PIT 增强不引入回测主路径联网调用。

## 后续 LLD 输入约束

LLD 必须定义历史成分股 schema、provider 查询算法、缺失日期处理、PIT/fixed 模式切换参数和回归策略。

## 阻塞说明

无。
