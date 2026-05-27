---
story_id: "CR011-S06-industry-market-cap-style-exposure-data"
title: "行业 / 市值 / 风格暴露"
story_slug: "industry-market-cap-style-exposure-data"
status: "verified"
priority: "P1"
wave: "CR011-DATA-BATCH-A"
depends_on:
  - "CR008-S06-factor-research-auxiliary-data-contract"
  - "CR011-S02-pit-universe-and-stock-lifecycle-completion"
dependency_contracts:
  - upstream: "CR008-S06-factor-research-auxiliary-data-contract"
    type: "contract"
    required: "行业、市值、风格暴露等辅助数据 allowed/blocked claims 合同已冻结"
  - upstream: "CR011-S02-pit-universe-and-stock-lifecycle-completion"
    type: "contract"
    required: "PIT universe gate、lifecycle 和 fixed snapshot 降级语义已冻结"
file_ownership:
  primary:
    - "tests/test_cr011_exposure_claims.py"
  shared:
    - "market_data/readers.py"
    - "engine/research_dataset.py"
  merge_owner: "CR011-S06-industry-market-cap-style-exposure-data"
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
    - "process/ARCHITECTURE-DECISION.md#adr-041cr-011-industry--market-cap--style-exposure-决定中性化声明边界"
    - "process/stories/CR011-S06-industry-market-cap-style-exposure-data.md"
  status: "approved"
  cp5_batch: "CR011-DATA-BATCH-A"
  cp5_precheck: "process/checks/CP5-CR011-S06-industry-market-cap-style-exposure-data-LLD-IMPLEMENTABILITY.md"
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
    - "PIT universe gate frozen"
    - "auxiliary allowed/blocked claims contract frozen"
    - "CR011-DATA-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CR011-S06 CP7 复验 PASS；`CR011-S06-CP7-F01` 已关闭，canonical `float_market_cap_availability` metadata 字段已写入并由测试覆盖，Story 已 verified。"
created_at: "2026-05-23"
updated_at: "2026-05-24T14:55:35+08:00"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-011"
---

# CR011-S06：行业 / 市值 / 风格暴露

## 目标

定义行业、市值、流通市值、beta/style exposure availability 和中性化 blocked claims，使新版报告只有在对应 PIT exposure 可用时才允许行业中性、市值中性、风格中性或 pure alpha 声明。该 Story 不用当前快照支撑 PIT exposure，不实现完整风险模型平台。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-076、REQ-080、REQ-081、CR011-AC-006 |
| HLD | `process/HLD.md` §27.1、§27.4、§27.5、§27.7；`process/HLD-DATA-LAKE.md` §14.2、§14.3、§14.5 |
| ADR | ADR-041 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR011-S06；`process/DEVELOPMENT-PLAN.yaml` wave `CR011-DATA-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：没有 PIT 行业、市值和风格暴露时，因子表现可能由行业、规模或风格偏置驱动。CR-011 需要把 exposure availability 写入 research metadata，并在缺数据时阻断中性化、pure alpha 和相关容量声明。

**输入文件**：`process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/USE-CASES.md`、`market_data/readers.py`、`engine/research_dataset.py`。

**输出文件**：`market_data/readers.py`、`engine/research_dataset.py`、`tests/test_cr011_exposure_claims.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| exposure availability reader | symbol/date、industry/cap/style catalog entries、quality policy | industry availability、market cap availability、float cap availability、style exposure availability、lineage | 当前快照不能证明 PIT exposure |
| neutralization claim gate | exposure availability、factor result、research mode | `neutralization_status`、raw IC、industry_neutral_ic、market_cap_neutral_ic、style_neutral_ic、blocked claims | 缺数据时对应中性化声明输出次数为 0 |
| report metadata writer | exposure matrix status、missing reason、sample counts | coverage、missing rate、neutralization status、allowed/blocked claims | 不输出 pure alpha 过强声明 |

**设计约束**：

- CP3 / CP4 未通过前不得进入 LLD；`CR011-DATA-BATCH-A` CP5 批次确认前不得实现。
- 行业分类、市值、流通市值、beta/style exposure 必须具备 effective/available_at 或明确 missing reason。
- 缺行业/市值/风格时，行业中性、市值中性、风格中性、pure alpha 声明输出次数必须为 0。
- 不读取 `.env`，不触发真实 provider，不操作旧 `data/**`，不覆盖旧报告，不写 `delivery/**`。

**命名规范**：保留 `industry_availability`、`market_cap_availability`、`float_market_cap`、`style_exposure_availability`、`neutralization_status`、`industry_neutral_ic`、`market_cap_neutral_ic`、`style_neutral_ic`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR011-S06-T1 | 修改 | `market_data/readers.py` | 暴露 industry / market cap / style exposure availability、lineage 和 missing reason |
| CR011-S06-T2 | 修改 | `engine/research_dataset.py` | 增加 exposure availability matrix 和 neutralization blocked claims |
| CR011-S06-T3 | 创建 | `tests/test_cr011_exposure_claims.py` | 覆盖缺行业/市值/风格阻断中性化、当前快照不证明 PIT exposure 和 no credential/no old data |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr011_exposure_claims.py`。

**验证方式**：exposure availability fixture、missing exposure fixture、claims snapshot、PIT effective/available_at 断言和 forbidden path 扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要真实行业/市值/风格数据源、不需要 token、不联网。

**关键验证场景**：

- PIT exposure 可用时输出 exposure availability 和 neutralization status。
- 缺行业时行业中性和行业归因声明输出次数为 0。
- 缺市值/流通市值时 size neutral、容量相关严肃结论和市值加权 IC 声明输出次数为 0。
- 缺 style exposure 时 pure alpha / 风格中性声明输出次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] 行业、市值、流通市值、beta/style exposure 4 类 availability 均进入报告 metadata。
- [ ] 缺行业/市值/风格时，对应行业中性、市值中性、风格中性、pure alpha 声明输出次数为 0。
- [ ] 当前快照用于证明 PIT exposure 的次数为 0。
- [ ] exposure 缺 effective/available_at 且进入 production_strict 决策的次数为 0。
- [ ] 默认验证路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 阻塞说明

OPEN：CR-011 CP3 / CP4 尚未通过，本 Story 不得进入 LLD。OPEN：`CR011-DATA-BATCH-A` CP5 尚未完成，不得实现。OPEN：本 Story 依赖 CR011-S02 PIT universe gate 合同冻结；S02 未冻结前不得计算 dev_ready。
