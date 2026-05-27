---
story_id: "CR011-S08-factor-panel-audit-and-robust-validation"
title: "因子审计面板与稳健性验证"
story_slug: "factor-panel-audit-and-robust-validation"
status: "verified"
priority: "P1"
wave: "CR011-VALIDATION-BATCH-C"
depends_on:
  - "CR011-S01-real-benchmark-and-policy-consumption"
  - "CR011-S02-pit-universe-and-stock-lifecycle-completion"
  - "CR011-S05-adjustment-and-corporate-action-audit"
  - "CR011-S07-liquidity-capacity-and-cost-sensitivity"
dependency_contracts:
  - upstream: "CR011-S01-real-benchmark-and-policy-consumption"
    type: "contract"
    required: "benchmark policy result、hs300/proxy 字段隔离和 missing reason 合同已冻结"
  - upstream: "CR011-S02-pit-universe-and-stock-lifecycle-completion"
    type: "contract"
    required: "PIT universe gate、fixed snapshot 降级和 lifecycle missing 行为已冻结"
  - upstream: "CR011-S05-adjustment-and-corporate-action-audit"
    type: "contract"
    required: "adjustment policy、adj_factor lineage 和 corporate action status 合同已冻结"
  - upstream: "CR011-S07-liquidity-capacity-and-cost-sensitivity"
    type: "contract"
    required: "capacity/cost sensitivity report、固定成本网格和 blocked claims 合同已冻结"
file_ownership:
  primary:
    - "reports/experiment_17_21_cr011/**"
    - "tests/test_cr011_factor_panel_robust_validation.py"
  shared:
    - "experiments/run_experiment_17_21_factor_suite.py"
    - "engine/research_dataset.py"
  merge_owner: "CR011-S08-factor-panel-audit-and-robust-validation"
  forbidden:
    - "reports/experiment_17_21/factor_strategy_report.md"
    - "market_data/connectors/**"
    - "data/**"
    - ".env"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#27.10"
    - "process/ARCHITECTURE-DECISION.md#adr-043cr-011-factor-panel-audit-与-robust-validation-是结论升级前置"
    - "process/stories/CR011-S08-factor-panel-audit-and-robust-validation.md"
  status: "approved"
  lld: "process/stories/CR011-S08-factor-panel-audit-and-robust-validation-LLD.md"
  auto_precheck: "process/checks/CP5-CR011-S08-factor-panel-audit-and-robust-validation-LLD-IMPLEMENTABILITY.md"
  auto_precheck_status: "PASS"
  cp5_batch: "CR011-VALIDATION-BATCH-C"
  manual_review: "checkpoints/CP5-CR011-VALIDATION-BATCH-C-LLD-BATCH.md"
  manual_status: "approved"
  confirmed_by: "user"
  confirmed_at: "2026-05-24T16:34:46+08:00"
  handoff: "process/handoffs/META-DEV-CR011-S08-LLD-2026-05-24.md"
  agent_name: "dev-qin the 2nd"
  agent_id: "019e58fe-0cb3-7d02-9bea-73d78492b7b5"
  started_at: "2026-05-24T15:58:31+08:00"
  preconditions:
    - "CR-011 CP3 人工确认通过"
    - "CR-011 CP4 自动预检通过并由 meta-po 汇入 CP5"
    - "CR011-DATA-BATCH-A 与 CR011-RESEARCH-BATCH-B 合同冻结"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "benchmark/PIT/adjustment/capacity contracts frozen"
    - "CR011-VALIDATION-BATCH-C CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CR011-S01/S02/S05/S07 均已 verified；CR011-S08 LLD 与 Story 级 CP5-C 自动预检 PASS；CP5-C 批次人工确认已 approved，可进入离线实现。旧报告不得覆盖。"
implementation:
  status: "coding-done"
  handoff: "process/handoffs/META-DEV-CR011-S08-IMPLEMENT-2026-05-24.md"
  agent_name: "dev-qin the 2nd"
  agent_id: "019e58fe-0cb3-7d02-9bea-73d78492b7b5"
  started_at: "2026-05-24T16:37:05+08:00"
  completed_at: "2026-05-24T16:47:41+08:00"
  cp6_check: "process/checks/CP6-CR011-S08-factor-panel-audit-and-robust-validation-CODING-DONE.md"
  cp6_status: "PASS"
  next_status: "verified"
verification:
  status: "verified"
  handoff: "process/handoffs/META-QA-CR011-S08-CP7-VERIFY-2026-05-24.md"
  agent_name: "qa-lv the 2nd"
  agent_id: "019e5931-551d-7a41-bdf9-cbf98b0829fb"
  started_at: "2026-05-24T16:54:32+08:00"
  completed_at: "2026-05-24T16:58:37+08:00"
  closed_at: "2026-05-24T17:04:06+08:00"
  cp7_check: "process/checks/CP7-CR011-S08-factor-panel-audit-and-robust-validation-VERIFICATION-DONE.md"
  cp7_status: "PASS"
created_at: "2026-05-23"
updated_at: "2026-05-24T17:04:06+08:00"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-011"
---

# CR011-S08：因子审计面板与稳健性验证

## 目标

版本化保存 raw / directional / winsorized / zscore factor panel，并输出 rolling、年度、市场状态、参数敏感性、成本敏感性五类稳健性验证。新版报告必须使用 `reports/experiment_17_21_cr011/**`，不得覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-078、REQ-079、REQ-080、REQ-081、REQ-082、CR011-AC-008 |
| HLD | `process/HLD.md` §27.1、§27.4、§27.5、§27.6、§27.10、§27.12；`process/HLD-DATA-LAKE.md` §14.2、§14.5、§14.7 |
| ADR | ADR-043 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR011-S08；`process/DEVELOPMENT-PLAN.yaml` wave `CR011-VALIDATION-BATCH-C` |

## 开发上下文（dev_context）

**背景说明**：实验 17-21 已有因子保留和策略化结果，但缺 panel 级审计和分层稳健性验证。CR-011 需要保存四阶段 factor panel、预处理 metadata、过滤原因和 lineage，并通过五类稳健性视图限制报告结论只能来自 `allowed_claims`。

**输入文件**：`process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/USE-CASES.md`、`experiments/run_experiment_17_21_factor_suite.py`、`engine/research_dataset.py`。旧报告路径 `reports/experiment_17_21/factor_strategy_report.md` 仅可作为 `baseline_report_path` 元数据引用，不是可写输出。

**输出文件**：`experiments/run_experiment_17_21_factor_suite.py`、`reports/experiment_17_21_cr011/**`、`tests/test_cr011_factor_panel_robust_validation.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| factor panel writer | factor values、universe、benchmark kind、preprocessing config、lineage | raw、directional、winsorized、zscore 四阶段 panel、panel manifest | 任一阶段缺失时 `factor_audit_incomplete` |
| robust validation runner | factor panel、strategy result、market state labels、parameter grid、cost grid | rolling、annual、market_state、parameter_grid、cost_grid 五类视图 | 单一区间单一参数结果不得通过 robust validation |
| versioned report writer | gate results、panel manifest、validation views、baseline path | `reports/experiment_17_21_cr011/**`、allowed/blocked claims、report metadata | 不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md` |

**设计约束**：

- CP3 / CP4 未通过前不得进入 LLD；`CR011-VALIDATION-BATCH-C` CP5 批次确认前不得实现。
- LLD 需消费 CR011-S01/S02/S05/S07 合同；开发需等待 DATA-BATCH-A 与 RESEARCH-BATCH-B 对应 CP5 和依赖满足。
- 新版报告、factor panel、稳健性表和 metadata 一律输出到 `reports/experiment_17_21_cr011/**` 或其下版本化 run 目录。
- 不读取 `.env`，不触发真实 provider，不操作旧 `data/**`，不覆盖旧报告，不写 `delivery/**`。

**命名规范**：保留 `factor_panel_stage`、`raw_value`、`directional_value`、`winsorized_value`、`zscore_value`、`preprocessing_version`、`robust_validation_status`、`baseline_report_path`、`allowed_claims`、`blocked_claims`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR011-S08-T1 | 修改 | `experiments/run_experiment_17_21_factor_suite.py` | 新版实验写出四阶段 factor panel、panel manifest 和 versioned report metadata |
| CR011-S08-T2 | 修改 | `engine/research_dataset.py` | 将 factor audit readiness、allowed/blocked claims 和 upstream gate result 汇入验证输入 |
| CR011-S08-T3 | 创建 | `reports/experiment_17_21_cr011/**` | 仅在实现阶段由新版实验生成版本化报告、factor panel 和稳健性验证产物；不得覆盖旧报告 |
| CR011-S08-T4 | 创建 | `tests/test_cr011_factor_panel_robust_validation.py` | 覆盖四阶段 panel、五类 robust validation、old report overwrite count=0 和 no credential/no old data |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr011_factor_panel_robust_validation.py`。

**验证方式**：factor panel fixture、validation view fixture、versioned report path guard、old report overwrite sentinel 和 forbidden path 扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要真实 lake、不需要 token、不联网。

**关键验证场景**：

- raw、directional、winsorized、zscore 四阶段 panel 均存在且有 preprocessing metadata。
- rolling、年度、市场状态、参数敏感性、成本敏感性五类视图均输出。
- 旧报告覆盖次数为 0；新版报告路径必须位于 `reports/experiment_17_21_cr011/**`。
- 缺任一 panel 阶段或缺任一稳健性视图时 robust validation fail。

## 量化验收标准（acceptance_criteria）

- [x] 四阶段 factor panel 均存在：raw、directional、winsorized、zscore。
- [x] 稳健性报告包含 rolling、年度、市场状态、参数敏感性、成本敏感性 5 个视图。
- [x] 新版报告、panel 和验证表输出路径匹配 `reports/experiment_17_21_cr011/**`。
- [x] 旧 `reports/experiment_17_21/factor_strategy_report.md` 覆盖次数为 0。
- [x] 默认验证路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 阻塞说明

已满足：CR-011 CP3 人工确认 approved、CP4 自动预检 PASS；`CR011-DATA-BATCH-A` 的 S01/S02/S05 已 verified，`CR011-RESEARCH-BATCH-B` 的 S07 已完成 CP6/CP7 并 verified。S08 已完成 `CR011-VALIDATION-BATCH-C` LLD、Story 级 CP5-C 自动预检、批次人工确认、离线实现、CP6 与 CP7；CP7=`process/checks/CP7-CR011-S08-factor-panel-audit-and-robust-validation-VERIFICATION-DONE.md` 结论 PASS。旧报告 forbidden path 仍生效，不得覆盖 `reports/experiment_17_21/factor_strategy_report.md`。
