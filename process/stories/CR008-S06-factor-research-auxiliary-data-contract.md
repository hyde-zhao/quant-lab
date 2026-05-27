---
story_id: "CR008-S06-factor-research-auxiliary-data-contract"
title: "因子研究辅助数据合同"
story_slug: "factor-research-auxiliary-data-contract"
status: "verified"
priority: "P1"
wave: "CR008-BATCH-A"
change_id: "CR-008"
depends_on:
  - "CR008-S03-research-dataset-builder"
  - "CR008-S04-quality-adjustment-label-window-gates"
  - "CR008-S05-pit-universe-consumption-contract"
dependency_contracts:
  - upstream: "CR008-S03-research-dataset-builder"
    type: "contract"
    required: "`ResearchDataset` 和 known limitations 字段已冻结"
  - upstream: "CR008-S04-quality-adjustment-label-window-gates"
    type: "contract"
    required: "quality/adjustment/label gate 已冻结"
  - upstream: "CR008-S05-pit-universe-consumption-contract"
    type: "contract"
    required: "PIT/fixed universe 和 survivorship disclosure 已冻结"
file_ownership:
  primary:
    - "tests/test_cr008_factor_auxiliary_data_contract.py"
  shared:
    - "engine/research_dataset.py"
    - "market_data/readers.py"
    - "experiments/run_experiment_15_factor_framework.py"
  merge_owner: "CR008-S06-factor-research-auxiliary-data-contract"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "data/**"
    - "reports/data_quality_report.csv"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#25.5"
    - "process/ARCHITECTURE-DECISION.md#adr-029因子辅助数据缺失时禁止对应严肃结论"
    - "process/stories/CR008-S06-factor-research-auxiliary-data-contract.md"
  status: "cp5-approved"
  cp5_batch: "CR008-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  blocked_by: ""
  unblock_condition: "satisfied: CR008-S05 CP6/CP7 PASS"
  required_contracts:
    - "research_dataset_builder contract frozen"
    - "quality/adjustment/label gate contract frozen"
    - "PIT/fixed universe contract frozen"
    - "CR008-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  implementation_scope: "offline-only"
  dev_handoff: "process/handoffs/META-DEV-CR008-S06-IMPLEMENT-2026-05-21.md"
  dev_agent_name: "dev-xu the 2nd"
  dev_agent_id: "019e4c3c-329d-78c3-acbc-722cdac3d1af"
  dev_started_at: "2026-05-22T04:31:18+08:00"
  dev_completed_at: "2026-05-22T04:41:52+08:00"
  cp6_status: "PASS"
  cp6_checkpoint: "process/checks/CP6-CR008-S06-factor-research-auxiliary-data-contract-CODING-DONE.md"
  cp6_completed_at: "2026-05-22T04:41:52+08:00"
  qa_handoff: "process/handoffs/META-QA-CR008-S06-CP7-VERIFY-2026-05-22.md"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR008-S06-factor-research-auxiliary-data-contract-CODING-DONE.md"
cp6_completed_at: "2026-05-22T04:41:52+08:00"
cp7_handoff: "process/handoffs/META-QA-CR008-S06-CP7-VERIFY-2026-05-22.md"
cp7_status: "PASS"
cp7_agent_name: "qa-zhang the 2nd"
cp7_agent_id: "019e4c4a-2ecc-7ff2-991f-060dc23a5e9f"
cp7_started_at: "2026-05-22T04:46:34+08:00"
cp7_checkpoint: "process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md"
cp7_completed_at: "2026-05-22T04:49:11+08:00"
verified_at: "2026-05-22T04:53:48+08:00"
upstream_cp7:
  - "process/checks/CP7-CR008-S03-research-dataset-builder-VERIFICATION-DONE.md"
  - "process/checks/CP7-CR008-S04-quality-adjustment-label-window-gates-VERIFICATION-DONE.md"
  - "process/checks/CP7-CR008-S05-pit-universe-consumption-contract-VERIFICATION-DONE.md"
created_at: "2026-05-21"
updated_at: "2026-05-22T04:53:48+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
---

# CR008-S06：因子研究辅助数据合同

## 目标

定义因子研究辅助数据 availability 与 allowed claims：缺可交易性、OHLCV/VWAP、行业、市值、复权审计、流动性或风格暴露时，报告不得声明对应严肃结论。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR008-AC-011、CR008-AC-012 |
| HLD | §25.5、§25.9、§25.13 |
| ADR | ADR-029 |

## 开发上下文（dev_context）

**背景说明**：实验十五因子框架可以运行，但缺 PIT、可交易性、行业、市值和风格暴露时，不能支撑严肃因子归因或容量结论。

**输入文件**：CR008-S03/S04/S05 Story、`experiments/run_experiment_15_factor_framework.py`。

**输出文件**：`engine/research_dataset.py`、`market_data/readers.py`、`experiments/run_experiment_15_factor_framework.py`、`tests/test_cr008_factor_auxiliary_data_contract.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| auxiliary availability matrix | reader results、request requirements | availability / missing reasons | 不触发真实抓取 |
| allowed claims gate | availability matrix、requested report claims | allowed / blocked claims | 缺数据时阻断对应结论 |

**设计约束**：

- 无行业数据不得声明行业中性或行业归因。
- 无市值数据不得声明 size neutral 或容量结论。
- 无可交易性数据不得声明真实可成交。
- 无风格暴露不得声明纯 alpha。

**命名规范**：使用 `auxiliary_availability`、`allowed_claims`、`blocked_claims`、`tradability_status`、`industry_classification_status`、`market_cap_status`。

**平台目标**：因子研究报告与 future adapter 共享合同。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR008-S03 | contract | 需要 ResearchDataset 字段 | builder contract frozen | availability 写入 metadata |
| CR008-S04 | contract | 需要 quality/label gate | gate contract frozen | 限制样本与 claims |
| CR008-S05 | contract | 需要 universe mode | universe contract frozen | PIT/fixed 影响因子结论 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR008-S06-T1 | 修改 | `engine/research_dataset.py` | 增加 auxiliary availability / allowed claims 字段 |
| CR008-S06-T2 | 修改 | `market_data/readers.py` | 如需添加只读 auxiliary result contract |
| CR008-S06-T3 | 修改 | `experiments/run_experiment_15_factor_framework.py` | 报告写入缺失降级语义 |
| CR008-S06-T4 | 创建 | `tests/test_cr008_factor_auxiliary_data_contract.py` | 覆盖缺行业/市值/可交易性/风格暴露的 blocked claims |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr008_factor_auxiliary_data_contract.py`。

**验证方式**：auxiliary fixture、report metadata assertions、blocked claims matrix、no-network scan。

**依赖环境**：Python 3.11、uv、pytest；离线。

**关键验证场景**：

- 缺行业时行业中性声明被 blocked。
- 缺市值时 size neutral / 容量结论被 blocked。
- 缺可交易性时真实可成交声明被 blocked。
- 缺风格暴露时纯 alpha 声明被 blocked。

## 量化验收标准（acceptance_criteria）

- [ ] 缺对应辅助数据时对应严肃结论输出次数为 0。
- [ ] `known_limitations` 与 `blocked_claims` 100% 写入缺失原因。
- [ ] S06 不新增真实数据抓取授权或 connector 调用。
- [ ] 旧数据、旧报告、凭据操作次数为 0。
- [ ] 实验十五报告保留框架验证结论，但严肃因子结论受 allowed claims 约束。

## 阻塞说明

无 BLOCKING。S06 是 P1 合同 Story，不授权新增真实辅助数据生产。
