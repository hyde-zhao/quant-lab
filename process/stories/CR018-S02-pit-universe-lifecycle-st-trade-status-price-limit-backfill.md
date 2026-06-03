---
story_id: "CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill"
title: "PIT / lifecycle / ST / suspend / trade_status / prices_limit readiness"
story_slug: "pit-universe-lifecycle-st-trade-status-price-limit-backfill"
status: "verified"
priority: "P0"
wave: "CR018-W2-P0-P1-READINESS"
depends_on:
  - "CR018-S01-production-current-truth-definition-and-dataset-groups"
dependency_type:
  - upstream: "CR018-S01-production-current-truth-definition-and-dataset-groups"
    type: "contract"
cp5_batch: "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "tests/test_cr018_pit_tradability_readiness.py"
  shared:
    - "market_data/contracts.py"
    - "market_data/validation.py"
    - "market_data/readers.py"
  merge_owner: "CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
    - "provider fetch"
    - "real lake write"
    - "catalog current pointer publish"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#19.4"
    - "process/HLD-DATA-LAKE.md#19.9"
    - "process/ARCHITECTURE-DECISION.md#ADR-063"
    - "process/stories/CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
created_at: "2026-05-29"
updated_at: "2026-05-29T09:39:28+08:00"
change_id: "CR-018"
---

# CR018-S02：PIT / lifecycle / ST / suspend / trade_status / prices_limit readiness

## 目标

将 PIT universe、上市/退市生命周期、代码变更、ST、停牌、交易状态和涨跌停 readiness 纳入 production publish gate，防止用当前快照或不可交易假设污染 current truth。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-13、UC-14 |
| 需求 | REQ-126、REQ-127、REQ-130 |
| HLD | `process/HLD-DATA-LAKE.md` §19.4、§19.9 |
| ADR | ADR-063 |

## 开发上下文（dev_context）

**背景说明**：当前 full-A candidate 仍带 non-PIT warning。production current truth 必须显式区分 PIT 缺失、lifecycle 缺失、ST / suspend / trade_status / prices_limit 缺失与可发布状态，缺失时 fail closed。

**输入文件**：CR018 HLD / ADR、S01 合同、本 Story 卡片、现有 `market_data/contracts.py`、`market_data/validation.py`、`market_data/readers.py`。

**输出文件**：`tests/test_cr018_pit_tradability_readiness.py`；共享修改 `market_data/contracts.py`、`market_data/validation.py`、`market_data/readers.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| PIT readiness validator | universe rows、available_date/effective_date/available_at | pit_status、as_of_join_violation_count | 缺 available 字段必须 fail |
| tradability readiness validator | trade_status、prices_limit、ST/suspend flags | can_buy/can_sell readiness、blocked reason | 不得假设涨停可买或跌停可卖 |
| lifecycle validator | list_date、delist_date、code_change | active universe denominator | 不得包含当时不存在或已退市证券 |

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR018-S01 | contract | S01 Story 合同已声明即可起草 LLD | 需要 S01 合同冻结且 CP5 approved | 消费 dataset group 和 claim matrix |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `tests/test_cr018_pit_tradability_readiness.py` | 当前 Story 独占 |
| shared | `market_data/contracts.py`、`market_data/validation.py`、`market_data/readers.py` | 与 S03/S05/S06/S07 冲突，开发默认串行或由 LLD 指定合并顺序 |
| forbidden | connector/runtime/凭据/真实抓取/真实写湖/publish | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR018-S02-T1 | 修改 | `market_data/contracts.py` | 增加 PIT / lifecycle / tradability readiness 字段合同 |
| CR018-S02-T2 | 修改 | `market_data/validation.py` | 增加 fail-closed readiness 校验 |
| CR018-S02-T3 | 修改 | `market_data/readers.py` | 读取层暴露 blocked reason，不扫未发布 lake |
| CR018-S02-T4 | 创建 | `tests/test_cr018_pit_tradability_readiness.py` | 覆盖 PIT、ST、停牌、涨跌停和生命周期缺失场景 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr018_pit_tradability_readiness.py`。

**验证方式**：fixture-only 合同测试；不联网、不读凭据、不写真实 lake。

**关键验证场景**：缺 PIT available 字段 fail；当前快照不能替代 PIT；ST / suspend / limit 缺失阻断 production publish；as-of join 违规计数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] P0 tradability / PIT 缺失时 production publish allowed 次数为 0。
- [ ] as-of join 违规计数必须为 0。
- [ ] 使用当前成分替代历史 PIT universe 的通过次数为 0。
- [ ] provider_fetch、lake_write、credential_read、current_pointer_publish 计数均为 0。

## 阻塞说明

CP5 已获批；真实 provider 回补和真实 lake 写入需要后续 per-run authorization，不属于本 Story 卡片阶段。
