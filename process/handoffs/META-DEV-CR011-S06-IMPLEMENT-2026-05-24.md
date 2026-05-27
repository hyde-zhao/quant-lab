---
handoff_id: "META-DEV-CR011-S06-IMPLEMENT-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-dev"
agent_name: "dev-zhu the 2nd"
change_id: "CR-011"
story_id: "CR011-S06-industry-market-cap-style-exposure-data"
wave_id: "CR011-DATA-BATCH-A-DEV-W6"
status: "completed"
created_at: "2026-05-24T14:14:02+08:00"
updated_at: "2026-05-24T14:32:55+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e589f-94d8-7073-b74b-50e2e260f6e0"
  thread_id: "019e589f-94d8-7073-b74b-50e2e260f6e0"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T14:15:25+08:00"
  completed_at: "2026-05-24T14:27:31+08:00"
  closed_at: "2026-05-24T14:30:29+08:00"
  result: "completed"
---

# META-DEV CR011-S06 实现交接

## 任务

实现 `CR011-S06-industry-market-cap-style-exposure-data` 的离线代码与 CP6 自检。目标是在 reader / research dataset 层补齐行业、市值、流通市值、beta/style exposure availability 和 neutralization blocked claims，使缺 exposure、缺 PIT as-of 字段或只有当前快照时，中性化、pure alpha、风险模型调整和容量相关强声明输出次数为 0。

你不是独占代码库：当前工作树已有 CR011-S01..S05 的实现和验证结果。不得回退他人修改；若发现冲突，按现有实现适配，并在 CP6 写清楚。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` | dev-ready |
| LLD | `process/stories/CR011-S06-industry-market-cap-style-exposure-data-LLD.md` | confirmed / implementation_allowed |
| CP5 自动预检 | `process/checks/CP5-CR011-S06-industry-market-cap-style-exposure-data-LLD-IMPLEMENTABILITY.md` | PASS |
| CP5 批次人工确认 | `checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md` | approved |
| 上游 CR008-S06 | `process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md` | verified |
| 上游 CR011-S02 | `process/checks/CP7-CR011-S02-pit-universe-and-stock-lifecycle-completion-VERIFICATION-DONE.md` | verified |
| S05 CP7 | `process/checks/CP7-CR011-S05-adjustment-and-corporate-action-audit-VERIFICATION-DONE.md` | PASS |

## 允许写入范围

- `market_data/readers.py`
- `engine/research_dataset.py`
- `tests/test_cr011_exposure_claims.py`
- `process/checks/CP6-CR011-S06-industry-market-cap-style-exposure-data-CODING-DONE.md`
- `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` 的实现状态字段

## 禁止范围

- 不实现或修改 `CR011-S07`、`CR011-S08`。
- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`data/**`、`.env`、`reports/experiment_17_21/factor_strategy_report.md`、`delivery/**`。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。
- 不修改 `process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`；这些由 meta-po 回填。

## 实现要点

- 在 `market_data/readers.py` 新增或等价实现：
  - `ExposureInputRequest`
  - `read_exposure_inputs`
  - exact capability：`industry_classification`、`market_cap`、`float_market_cap`、`style_exposure`
  - typed missing / source unresolved / required columns / lineage / coverage / remediation `auto_execute=false`
- 在 `engine/research_dataset.py` 新增或等价实现：
  - `ExposureAvailabilityEntry` / `ExposureAvailabilityMatrix`
  - `NeutralizationClaimGateResult`
  - `build_exposure_availability_matrix`
  - `evaluate_neutralization_claims`
  - `merge_exposure_claims_into_metadata`
- 必须复用 CR008-S06 `auxiliary_availability` / claims 语义和 CR011-S02 PIT/lifecycle metadata。
- 缺行业时阻断 `industry_neutral_ic`、`industry_neutral`、`industry_attribution`、`industry_zscore`、`industry_group_ic`。
- 缺市值/流通市值时阻断 `market_cap_neutral_ic`、`market_cap_neutral`、`size_neutral`、`market_cap_weighted_ic`、容量相关 size 强声明。
- 缺 beta/style exposure 时阻断 `style_neutral_ic`、`style_neutral`、`pure_alpha`、`risk_model_adjusted_alpha`。
- 当前快照、缺 `effective_date`、缺 `available_at`、future availability、future effective date、PIT gate 未通过均不得证明 PIT exposure。
- 不计算完整风险模型；只校验下游已提供的 raw / neutralized metrics 是否允许展示。

## CP6 要求

CP6 文件必须写入：

- Entry Criteria、Checklist、Exit Criteria、Deliverables。
- Agent Dispatch Evidence：`spawn_agent`、agent id/thread id、handoff path、完成时间。
- 代码变更清单与 TASK-ID 对应关系。
- 验证命令和结果。
- 安全确认：`network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`、旧报告覆盖次数 0。

## 建议验证命令

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/readers.py engine/research_dataset.py tests/test_cr011_exposure_claims.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_exposure_claims.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_adjustment_audit.py tests/test_cr011_pit_universe_lifecycle.py tests/test_cr008_factor_auxiliary_data_contract.py tests/test_cr011_execution_price_policy.py`

## 期望输出

| 交付物 | 路径 |
|---|---|
| exposure reader / claims gate 实现 | `market_data/readers.py`、`engine/research_dataset.py` |
| S06 测试 | `tests/test_cr011_exposure_claims.py` |
| CP6 编码完成检查 | `process/checks/CP6-CR011-S06-industry-market-cap-style-exposure-data-CODING-DONE.md` |
| Story 实现状态 | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` |

若 CP6 PASS，请将 Story 状态推进为 `ready-for-verification`；若实现发现上游合同或授权阻断，请写 CP6 `BLOCKED` 并停止，不得扩大范围。
