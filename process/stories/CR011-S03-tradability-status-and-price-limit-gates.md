---
story_id: "CR011-S03-tradability-status-and-price-limit-gates"
title: "可交易性与涨跌停门控"
story_slug: "tradability-status-and-price-limit-gates"
status: "verified"
priority: "P0"
wave: "CR011-DATA-BATCH-A"
depends_on:
  - "CR011-S02-pit-universe-and-stock-lifecycle-completion"
  - "CR010-S07-trade-status-contract-reader-fail-fast"
  - "CR010-S08-prices-limit-contract-gate-fail-fast"
  - "CR010-S09-events-available-at-contract-fail-fast"
dependency_contracts:
  - upstream: "CR011-S02-pit-universe-and-stock-lifecycle-completion"
    type: "contract"
    required: "lifecycle、上市天数、退市/暂停和 as-of 可得性 gate 合同已冻结；未冻结时 min_listing_days / lifecycle gate 返回 required_missing"
  - upstream: "CR010-S07-trade-status-contract-reader-fail-fast"
    type: "contract"
    required: "trade_status reader result、suspended/ST/no_trade reason 和 fail-fast missing 语义已冻结"
  - upstream: "CR010-S08-prices-limit-contract-gate-fail-fast"
    type: "contract"
    required: "prices_limit reader result、limit_up/limit_down/can_buy/can_sell 合同已冻结"
  - upstream: "CR010-S09-events-available-at-contract-fail-fast"
    type: "contract"
    required: "events explicit available_at gate 和 missing_required 行为已冻结"
file_ownership:
  primary:
    - "tests/test_cr011_tradability_gates.py"
  shared:
    - "market_data/readers.py"
    - "engine/trade_status.py"
    - "engine/trading_constraints.py"
    - "engine/events.py"
    - "engine/research_dataset.py"
  merge_owner: "CR011-S03-tradability-status-and-price-limit-gates"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "data/**"
    - ".env"
    - "reports/experiment_17_21/factor_strategy_report.md"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#27.7"
    - "process/HLD-DATA-LAKE.md#14.2"
    - "process/ARCHITECTURE-DECISION.md#adr-038cr-011-tradability-gates-必须覆盖真实可交易约束"
    - "process/stories/CR011-S03-tradability-status-and-price-limit-gates.md"
  status: "approved"
  cp5_batch: "CR011-DATA-BATCH-A"
  cp5_precheck: "process/checks/CP5-CR011-S03-tradability-status-and-price-limit-gates-LLD-IMPLEMENTABILITY.md"
  manual_review: "checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md"
  confirmed_by: "user"
  confirmed_at: "2026-05-24T10:24:02+08:00"
  preconditions:
    - "CR-011 CP3 人工确认通过"
    - "CR-011 CP4 自动预检通过并由 meta-po 汇入 CP5"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "trade_status/prices_limit/events gate matrix frozen"
    - "CR011-S02 lifecycle / min_listing_days contract frozen"
    - "CR011-DATA-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "S02 已 verified，CR010-S07/S08/S09 均为 implemented / meta-qa CP7 PASS，CR011-DATA-BATCH-A CP5 已 approved；当前无其他 dev_running 文件冲突。meta-po 已通过 spawn_agent 调度 meta-dev/dev-he 执行离线实现，仍不得真实联网、写真实 lake、读取凭据、操作旧 data/** 或覆盖旧报告。"
created_at: "2026-05-23"
updated_at: "2026-05-24T12:34:34+08:00"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-011"
---

# CR011-S03：可交易性与涨跌停门控

## 目标

将停牌、涨跌停、ST、无成交、上市天数、事件状态纳入因子策略 gate，并在缺 source/interface、缺 `available_at` 或 quality/readiness 不合规时阻断 production_strict。该 Story 不默认全可交易、不接真实 provider、不忽略 W3 missing。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-073、REQ-080、REQ-081、CR011-AC-003 |
| HLD | `process/HLD.md` §27.1、§27.4、§27.5、§27.7；`process/HLD-DATA-LAKE.md` §14.2、§14.3、§14.5 |
| ADR | ADR-038 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR011-S03；`process/DEVELOPMENT-PLAN.yaml` wave `CR011-DATA-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：旧实验 17-21 未建模停牌、涨跌停、ST、无成交、上市天数和事件状态，不能声明真实可成交。CR-011 需要在 portfolio 前生成机器可读 gate matrix，使每个 symbol/date 的可买、可卖、阻断或延后原因都可审计。

**输入文件**：`process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/USE-CASES.md`、`market_data/readers.py`、`engine/trade_status.py`、`engine/trading_constraints.py`、`engine/events.py`、`engine/research_dataset.py`。

**输出文件**：`market_data/readers.py`、`engine/trade_status.py`、`engine/trading_constraints.py`、`engine/events.py`、`engine/research_dataset.py`、`tests/test_cr011_tradability_gates.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| tradability reader bundle | trade_date、symbol、catalog/readiness、quality policy | suspended、st_status、no_trade、status_reason、available_at、lineage | source/interface 未确认时 `source_unresolved` / `required_missing` |
| price limit gate | trade_date、symbol、limit_up、limit_down、planned side、execution price | `can_buy`、`can_sell`、blocked reason | 不得忽略涨跌停后声明真实可成交 |
| event gate | event rows、available_at、decision_time | `event_blocked`、event reason、available_at violation | 缺 explicit `available_at` 时不得进入 production_strict |
| research tradability matrix | target weights / trades、六类 gate result | executable set、blocked set、reason counts、claims | 默认全可交易和空表可用均禁止 |

**设计约束**：

- CP3 / CP4 未通过前不得进入 LLD；`CR011-DATA-BATCH-A` CP5 批次确认前不得实现。
- 六类 gate 均必须输出 `available / required_missing / blocked` 或等价结构化状态。
- production_strict 缺任一 P0 gate 时通过次数为 0；exploratory 可运行但必须写 blocked claims。
- 不读取 `.env`，不触发真实 provider，不操作旧 `data/**`，不覆盖旧报告，不写 `delivery/**`。

**命名规范**：保留 `tradability_gate_status`、`can_buy`、`can_sell`、`status_reason`、`suspended`、`limit_up`、`limit_down`、`st_status`、`no_trade`、`min_listing_days`、`event_blocked`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR011-S03-T1 | 修改 | `market_data/readers.py` | 统一读取 trade_status、prices_limit、events 的 typed missing / readiness result |
| CR011-S03-T2 | 修改 | `engine/trade_status.py` | 建立停牌、ST、无成交、上市天数等状态 gate |
| CR011-S03-T3 | 修改 | `engine/trading_constraints.py` | 建立涨跌停可买可卖 gate 和 blocked reason |
| CR011-S03-T4 | 修改 | `engine/events.py` | 建立 events explicit available_at gate |
| CR011-S03-T5 | 修改 | `engine/research_dataset.py` | 将六类 gate 聚合为 research tradability matrix 和 blocked claims |
| CR011-S03-T6 | 创建 | `tests/test_cr011_tradability_gates.py` | 覆盖六类 gate、missing fail-fast、默认全可交易禁止和 no network/no credential |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr011_tradability_gates.py`。

**验证方式**：fixture gate matrix、missing source fixtures、blocked trade reason 快照、offline monkeypatch 和 forbidden import/path 扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要真实 W3 数据源、不需要 token、不联网。

**关键验证场景**：

- 停牌、涨跌停、ST、无成交、上市天数、事件状态六类 gate 均有结构化结果。
- 任一 P0 gate 缺失时 production_strict fail。
- blocked trade 必须输出 symbol/date/reason，不允许静默删除。
- 默认全可交易、空表 available、日期推导事件可用时点均被拒绝。

## 量化验收标准（acceptance_criteria）

- [ ] 6 类 gate 均输出 `available / required_missing / blocked` 或等价结构化状态。
- [ ] production_strict 缺任一 P0 gate 时通过次数为 0。
- [ ] 每个 blocked trade 至少包含 `trade_date`、`symbol`、`side`、`blocked_reason` 4 类字段。
- [ ] 默认全可交易、空表可用和事件缺 `available_at` 进入决策的次数均为 0。
- [ ] 默认验证路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 阻塞说明

OPEN：CR-011 CP3 / CP4 尚未通过，本 Story 不得进入 LLD。OPEN：`CR011-DATA-BATCH-A` CP5 尚未完成，不得实现。OPEN：CR010-DL-BATCH-B 的 W3 合同若未冻结，将阻塞本 Story 的后续 dev_ready；当前不新增 BLOCKING 设计问题。
