---
handoff_id: "META-QA-CR011-S06-CP7-VERIFY-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-qa"
agent_name: "qa-shi the 2nd"
change_id: "CR-011"
story_id: "CR011-S06-industry-market-cap-style-exposure-data"
wave_id: "CR011-DATA-BATCH-A-VERIFY-W6"
status: "completed"
created_at: "2026-05-24T14:35:02+08:00"
updated_at: "2026-05-24T14:42:33+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e58b2-9868-76c0-872f-3781379ea101"
  thread_id: "019e58b2-9868-76c0-872f-3781379ea101"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T14:36:06+08:00"
  completed_at: "2026-05-24T14:39:07+08:00"
  closed_at: "2026-05-24T14:42:33+08:00"
  result: "completed-fail"
---

# META-QA CR011-S06 CP7 验证交接

## 任务

对 `CR011-S06-industry-market-cap-style-exposure-data` 执行 CP7 独立验证。重点验证行业、市值、流通市值、style exposure availability，PIT as-of gate，neutralization / pure alpha / risk-model-adjusted claims 阻断，以及默认安全边界。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` | ready-for-verification |
| LLD | `process/stories/CR011-S06-industry-market-cap-style-exposure-data-LLD.md` | confirmed |
| CP6 | `process/checks/CP6-CR011-S06-industry-market-cap-style-exposure-data-CODING-DONE.md` | PASS |
| 实现 handoff | `process/handoffs/META-DEV-CR011-S06-IMPLEMENT-2026-05-24.md` | completed / closed |
| 上游 CR008-S06 | `process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md` | PASS |
| 上游 CR011-S02 | `process/checks/CP7-CR011-S02-pit-universe-and-stock-lifecycle-completion-VERIFICATION-DONE.md` | PASS |
| 上游 CR011-S05 | `process/checks/CP7-CR011-S05-adjustment-and-corporate-action-audit-VERIFICATION-DONE.md` | PASS |

## 允许写入范围

- `process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-VERIFICATION-DONE.md`
- `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` 的验证状态字段

## 禁止范围

- 不修改生产代码或测试代码，除非先在 CP7 写明 FAIL / BLOCKED。
- 不实现或修改 `CR011-S07`、`CR011-S08`。
- 不修改 `process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`。
- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`data/**`、`.env`、`reports/experiment_17_21/factor_strategy_report.md`、`delivery/**`。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。

## 必查项

- CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables 和 Agent Dispatch Evidence。
- 验证 CP6 调度证据：`dispatch.mode=spawn_agent`，agent/thread id=`019e589f-94d8-7073-b74b-50e2e260f6e0`，handoff 已 completed/closed。
- 验证 `ExposureInputRequest`、`read_exposure_inputs`，以及 exact capability：`industry_classification`、`market_cap`、`float_market_cap`、`style_exposure`。
- 验证 `ExposureAvailabilityEntry`、`ExposureAvailabilityMatrix`、`NeutralizationClaimGateResult`、`build_exposure_availability_matrix`、`evaluate_neutralization_claims`、`merge_exposure_claims_into_metadata`。
- 验证 4 类 availability 均进入 metadata：`industry_availability`、`market_cap_availability`、`float_market_cap_availability`、`style_exposure_availability`。
- 缺行业时必须阻断 `industry_neutral_ic`、`industry_neutral`、`industry_attribution`、`industry_zscore`、`industry_group_ic`。
- 缺市值 / 流通市值时必须阻断 `market_cap_neutral_ic`、`market_cap_neutral`、`size_neutral`、`market_cap_weighted_ic` 和容量相关 size 强声明。
- 缺 beta / style exposure 时必须阻断 `style_neutral_ic`、`style_neutral`、`pure_alpha`、`risk_model_adjusted_alpha`。
- 当前快照、缺 `effective_date`、缺 `available_at`、future availability、future effective date、上游 PIT gate 未通过，均不得证明 PIT exposure。
- 不得伪造完整风险模型或自动生成 neutralized metrics；只允许校验下游显式提供的 raw / neutralized metrics 是否可展示。
- 验证默认路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`、旧报告覆盖次数 0。

## 建议验证命令

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/readers.py engine/research_dataset.py tests/test_cr011_exposure_claims.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_exposure_claims.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_adjustment_audit.py tests/test_cr011_pit_universe_lifecycle.py tests/test_cr008_factor_auxiliary_data_contract.py tests/test_cr011_execution_price_policy.py tests/test_cr011_benchmark_policy_consumption.py`

## 期望输出

| 交付物 | 路径 |
|---|---|
| CP7 验证完成检查 | `process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-VERIFICATION-DONE.md` |
| Story 验证状态 | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` |

若验证 PASS，可将 Story 状态推进为 `verified`；若 FAIL / BLOCKED，不得标记 verified，需列明阻断项、最小修复建议和最小回归集。
