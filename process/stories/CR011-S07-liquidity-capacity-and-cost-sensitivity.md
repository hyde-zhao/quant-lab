---
story_id: "CR011-S07-liquidity-capacity-and-cost-sensitivity"
title: "流动性 / 容量 / 成本敏感性"
story_slug: "liquidity-capacity-and-cost-sensitivity"
status: "verified"
priority: "P1"
wave: "CR011-RESEARCH-BATCH-B"
depends_on:
  - "CR011-S03-tradability-status-and-price-limit-gates"
  - "CR011-S04-ohlcv-vwap-clean-execution-feed"
  - "CR011-S06-industry-market-cap-style-exposure-data"
dependency_contracts:
  - upstream: "CR011-S03-tradability-status-and-price-limit-gates"
    type: "contract"
    required: "tradability gate matrix、blocked trades 和可交易声明边界已冻结"
  - upstream: "CR011-S04-ohlcv-vwap-clean-execution-feed"
    type: "contract"
    required: "execution_price_policy、OHLCV/VWAP availability 和 close_proxy 降级语义已冻结"
  - upstream: "CR011-S06-industry-market-cap-style-exposure-data"
    type: "contract"
    required: "exposure availability、neutralization blocked claims 和辅助数据缺失语义已冻结"
file_ownership:
  primary:
    - "tests/test_cr011_capacity_cost_sensitivity.py"
  shared:
    - "engine/research_dataset.py"
    - "engine/portfolio.py"
    - "experiments/run_experiment_17_21_factor_suite.py"
  merge_owner: "CR011-S07-liquidity-capacity-and-cost-sensitivity"
  forbidden:
    - "market_data/connectors/**"
    - "data/**"
    - ".env"
    - "reports/experiment_17_21/factor_strategy_report.md"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#27.7"
    - "process/ARCHITECTURE-DECISION.md#adr-042cr-011-liquidity--capacity--cost-sensitivity-使用固定网格和可审计输入"
    - "process/stories/CR011-S07-liquidity-capacity-and-cost-sensitivity.md"
  status: "approved"
  cp5_batch: "CR011-RESEARCH-BATCH-B"
  cp5_precheck: "process/checks/CP5-CR011-S07-liquidity-capacity-and-cost-sensitivity-LLD-IMPLEMENTABILITY.md"
  manual_review: "checkpoints/CP5-CR011-RESEARCH-BATCH-B-LLD-BATCH.md"
  confirmed_by: "user"
  confirmed_at: "2026-05-24T15:25:45+08:00"
  preconditions:
    - "CR-011 CP3 人工确认通过"
    - "CR-011 CP4 自动预检通过并由 meta-po 汇入 CP5"
    - "CR011-DATA-BATCH-A 相关合同冻结"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "tradability/execution/exposure contracts frozen"
    - "CR011-RESEARCH-BATCH-B CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CR011-RESEARCH-BATCH-B CP5-B 已由用户 approve；S03/S04/S06 上游合同已冻结，当前无 dev_running 文件冲突，可进入 S07 离线实现。"
created_at: "2026-05-23"
updated_at: "2026-05-24T15:55:57+08:00"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-011"
---

# CR011-S07：流动性 / 容量 / 成本敏感性

## 目标

基于 amount、volume、turnover、ADV 或等价输入输出容量与成本敏感性报告，使新版实验不再只依赖单一成本点解释策略表现。该 Story 不声明缺流动性时容量可行，不只输出单一成本点。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-077、REQ-079、REQ-080、REQ-081、CR011-AC-007 |
| HLD | `process/HLD.md` §27.1、§27.4、§27.5、§27.6、§27.7；`process/HLD-DATA-LAKE.md` §14.2、§14.5 |
| ADR | ADR-042 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR011-S07；`process/DEVELOPMENT-PLAN.yaml` wave `CR011-RESEARCH-BATCH-B` |

## 开发上下文（dev_context）

**背景说明**：实验 17-21 中部分因子和组合可能对换手、成交额和成本假设高度敏感。CR-011 需要固定成本网格和容量字段，使报告可说明收益是否被成本侵蚀，以及缺流动性数据时哪些容量声明被阻断。

**输入文件**：`process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/USE-CASES.md`、`engine/research_dataset.py`、`engine/portfolio.py`、`experiments/run_experiment_17_21_factor_suite.py`。

**输出文件**：`engine/research_dataset.py`、`engine/portfolio.py`、`experiments/run_experiment_17_21_factor_suite.py`、`tests/test_cr011_capacity_cost_sensitivity.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| liquidity input bundle | amount、volume、turnover、ADV、portfolio holdings、lineage | liquidity availability、missing reason、sample loss | 缺流动性输入时 capacity conclusion blocked |
| capacity model / helper | trades、holdings、liquidity bundle、participation limit | 成交额占比、换手、持仓数、样本损失、容量上限 | 不得以缺数据组合声明容量可行 |
| cost sensitivity runner | strategy result、fixed cost grid `[0, 5, 10, 20]` bps | cost_after_return、cost erosion、scenario status | 不允许只输出最佳成本或单一默认成本 |
| report metadata writer | capacity report、cost grid result、blocked claims | capacity/cost status、allowed/blocked claims | 缺输入时阻断容量可交易声明 |

**设计约束**：

- CP3 / CP4 未通过前不得进入 LLD；`CR011-RESEARCH-BATCH-B` CP5 批次确认前不得实现。
- LLD 起草需等待 CR011-DATA-BATCH-A 中 tradability、execution、exposure 合同冻结。
- 成本敏感性固定输出 `[0, 5, 10, 20]` bps 四档网格。
- 不读取 `.env`，不触发真实 provider，不操作旧 `data/**`，不覆盖旧报告，不写 `delivery/**`。

**命名规范**：保留 `cost_grid_bps`、`capacity_limit`、`participation_rate`、`cost_after_return`、`cost_scenario_id`、`liquidity_capacity_status`、`capacity_cost_status`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR011-S07-T1 | 修改 | `engine/research_dataset.py` | 将 liquidity / capacity inputs availability 纳入研究输入和 blocked claims |
| CR011-S07-T2 | 修改 | `engine/portfolio.py` | 增加或扩展容量成本敏感性所需的成交额占比、换手和成本侵蚀计算接口 |
| CR011-S07-T3 | 修改 | `experiments/run_experiment_17_21_factor_suite.py` | 新版实验输出固定四档成本网格和容量报告 metadata |
| CR011-S07-T4 | 创建 | `tests/test_cr011_capacity_cost_sensitivity.py` | 覆盖固定成本网格、五类容量字段、缺流动性 blocked claims 和 no old report overwrite |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr011_capacity_cost_sensitivity.py`。

**验证方式**：portfolio trades fixture、liquidity inputs fixture、missing liquidity fixture、cost grid 参数化测试和 forbidden path 扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要真实成交额数据源、不需要 token、不联网。

**关键验证场景**：

- 成本网格固定为 `[0, 5, 10, 20]` bps。
- 容量报告包含成交额占比、换手、持仓数、样本损失、成本侵蚀 5 类字段。
- 缺流动性输入时容量可交易声明输出次数为 0。
- 单一成本点不得使 `robust_validation_status` 通过。

## 量化验收标准（acceptance_criteria）

- [ ] 固定输出 `[0, 5, 10, 20]` bps 四档成本网格。
- [ ] 容量报告包含成交额占比、换手、持仓数、样本损失、成本侵蚀 5 类字段。
- [ ] 缺流动性 / 容量输入时容量可交易声明输出次数为 0。
- [ ] 只输出单一成本点时 `cost_sensitivity_status` 或等价状态必须为 fail。
- [ ] 默认验证路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 阻塞说明

已满足：S07 LLD 已输出，Story 级 CP5-B 自动预检已 PASS，`checkpoints/CP5-CR011-RESEARCH-BATCH-B-LLD-BATCH.md` 已由用户 approve；CR-011 CP3 人工确认 approved、CP4 自动预检 PASS、CR011-DATA-BATCH-A verified，且 CR011-S03/S04/S06 合同已冻结。S07 已完成离线实现，CP6=`process/checks/CP6-CR011-S07-liquidity-capacity-and-cost-sensitivity-CODING-DONE.md` PASS，CP7=`process/checks/CP7-CR011-S07-liquidity-capacity-and-cost-sensitivity-VERIFICATION-DONE.md` PASS，当前状态为 `verified`。仍不得真实联网、写真实 lake、读取凭据、操作旧 `data/**` 或覆盖旧报告。
