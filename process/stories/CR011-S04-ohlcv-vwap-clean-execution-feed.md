---
story_id: "CR011-S04-ohlcv-vwap-clean-execution-feed"
title: "OHLCV / VWAP 干净执行 feed"
story_slug: "ohlcv-vwap-clean-execution-feed"
status: "verified"
priority: "P1"
wave: "CR011-DATA-BATCH-A"
depends_on:
  - "CR011-S03-tradability-status-and-price-limit-gates"
  - "CR010-S02-prices-adj-factor-history-backfill-loop"
dependency_contracts:
  - upstream: "CR011-S03-tradability-status-and-price-limit-gates"
    type: "contract"
    required: "tradability gate matrix、blocked reason 和 missing 行为已冻结"
  - upstream: "CR010-S02-prices-adj-factor-history-backfill-loop"
    type: "runtime"
    required: "prices / adj_factor 历史覆盖、OHLCV 字段和 quality/readiness 可被只读消费"
file_ownership:
  primary:
    - "tests/test_cr011_execution_price_policy.py"
  shared:
    - "market_data/readers.py"
    - "engine/research_dataset.py"
    - "engine/backtest.py"
  merge_owner: "CR011-S04-ohlcv-vwap-clean-execution-feed"
  forbidden:
    - "market_data/connectors/**"
    - "data/**"
    - ".env"
    - "reports/experiment_17_21/factor_strategy_report.md"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#27.7"
    - "process/HLD-DATA-LAKE.md#14.2"
    - "process/ARCHITECTURE-DECISION.md#adr-039cr-011-execution-price--vwap-缺失必须显式降级"
    - "process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md"
  status: "approved"
  cp5_batch: "CR011-DATA-BATCH-A"
  cp5_precheck: "process/checks/CP5-CR011-S04-ohlcv-vwap-clean-execution-feed-LLD-IMPLEMENTABILITY.md"
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
    - "tradability gate matrix frozen"
    - "execution_price_policy enum and degradation metadata frozen"
    - "CR011-DATA-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CR011-DATA-BATCH-A CP5 已 approved；S03 tradability gate 已 CP7 PASS / verified，CR010-S02 prices/adj_factor 历史回补闭环已 verified；S04 首次 CP7 FAIL 的 exact policy 阻断项已完成 blocker-fix CP6 PASS，并由 meta-qa/qa-hua the 2nd CP7 复验 PASS；S04 当前 verified。"
created_at: "2026-05-23"
updated_at: "2026-05-24T13:24:37+08:00"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-011"
---

# CR011-S04：OHLCV / VWAP 干净执行 feed

## 目标

定义 `open` / `close` / `vwap` / `close_proxy` 执行价 policy 和 VWAP 缺失降级合同，使新版实验可以明确区分真实执行价、可审计日频执行价代理和 close proxy。该 Story 不实现分钟级撮合，不把 close proxy 声明为 VWAP，不自动推导真实 VWAP。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-074、REQ-080、REQ-081、CR011-AC-004 |
| HLD | `process/HLD.md` §27.1、§27.4、§27.5、§27.7；`process/HLD-DATA-LAKE.md` §14.2、§14.3、§14.5 |
| ADR | ADR-039 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR011-S04；`process/DEVELOPMENT-PLAN.yaml` wave `CR011-DATA-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：旧实验使用 close 执行价代理。CR-011 需要把执行价 policy 显式写入研究输入、portfolio metadata 和报告声明，避免 VWAP/open 缺失时被静默替换为 close 并误称真实成交。

**输入文件**：`process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/USE-CASES.md`、`market_data/readers.py`、`engine/research_dataset.py`、`engine/backtest.py`。

**输出文件**：`market_data/readers.py`、`engine/research_dataset.py`、`engine/backtest.py`、`tests/test_cr011_execution_price_policy.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| execution feed reader | trade_date、symbol、OHLCV fields、VWAP status、quality/readiness | open/high/low/close/volume/amount、`vwap_or_proxy`、lineage、missing reason | VWAP 缺失时不得静默填充 |
| execution policy resolver | requested policy、feed availability、tradability matrix | `execution_price_policy`、`execution_price`、`execution_degradation_reason`、unfilled reason | policy 只允许 `open`、`close`、`vwap`、`close_proxy` |
| report metadata writer | execution result、portfolio trades、blocked claims | execution availability、degradation metadata、blocked real execution claims | `close_proxy` 时真实 VWAP/真实成交声明输出次数为 0 |

**设计约束**：

- CP3 / CP4 未通过前不得进入 LLD；`CR011-DATA-BATCH-A` CP5 批次确认前不得实现。
- `execution_price_policy` 只允许 4 个值：`open`、`close`、`vwap`、`close_proxy`。
- `close_proxy` 必须写 `execution_degradation_reason`，并同步阻断 VWAP / 真实成交声明。
- 不读取 `.env`，不触发真实 provider，不操作旧 `data/**`，不覆盖旧报告，不写 `delivery/**`。

**命名规范**：保留 `execution_price_policy`、`execution_price`、`execution_degradation_reason`、`vwap_status`、`vwap_or_proxy`、`unfilled_reason`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR011-S04-T1 | 修改 | `market_data/readers.py` | 暴露 OHLCV/VWAP availability、`vwap_status` 和 missing reason |
| CR011-S04-T2 | 修改 | `engine/research_dataset.py` | 将执行价 policy 和降级 metadata 纳入研究输入 |
| CR011-S04-T3 | 修改 | `engine/backtest.py` | 消费 execution price policy，不在缺价时前填、后填或 0 填充 |
| CR011-S04-T4 | 创建 | `tests/test_cr011_execution_price_policy.py` | 覆盖 4 值枚举、close_proxy 降级、VWAP 缺失阻断真实成交声明和 no old report overwrite |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr011_execution_price_policy.py`。

**验证方式**：OHLCV fixture、VWAP missing fixture、execution policy 参数化测试、报告 metadata 快照和 forbidden path 扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要分钟数据、不需要真实 provider、不联网。

**关键验证场景**：

- 4 个合法 policy 可解析，非法 policy fail fast。
- VWAP 缺失且选择 `vwap` 时 production_strict fail 或按 LLD 批准策略显式降级。
- `close_proxy` 必填 `execution_degradation_reason`。
- 真实 VWAP/真实成交声明在 close proxy 模式下输出次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] `execution_price_policy` 只允许 `open`、`close`、`vwap`、`close_proxy` 4 个取值。
- [ ] `close_proxy` 时 `execution_degradation_reason` 必填。
- [ ] `close_proxy` 模式下真实 VWAP、真实开盘成交、真实可成交声明输出次数为 0。
- [ ] 缺失执行价前填、后填或 0 填充次数为 0。
- [ ] 默认验证路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 阻塞说明

OPEN：CR-011 CP3 / CP4 尚未通过，本 Story 不得进入 LLD。OPEN：`CR011-DATA-BATCH-A` CP5 尚未完成，不得实现。OPEN：本 Story 依赖 CR011-S03 tradability gate 合同冻结；在 S03 合同未冻结前不得计算 dev_ready。
