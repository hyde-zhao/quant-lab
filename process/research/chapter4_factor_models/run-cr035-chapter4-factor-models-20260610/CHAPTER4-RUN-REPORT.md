# CR-035 第四章多因子模型定价检验报告

- run_id: `run-cr035-chapter4-factor-models-20260610`
- status: `PASS`
- provider_fetch: `0`
- lake_write: `0`
- catalog_publish: `0`
- qmt_operation: `0`
- simulation_or_live: `0`

## 样本摘要

| sample_id | status | panel_rows | label_rows | matched_rows | rebalance_count |
|---|---|---:|---:|---:|---:|
| `in_sample_2000_2019` | `PASS` | 2550289 | 447186 | 407599 | 239 |
| `observation_2020_2026_ytd` | `PASS` | 1957024 | 371877 | 317132 | 76 |

## 模型准入摘要

| sample_id | model_id | admission | reason |
|---|---|---|---|
| `in_sample_2000_2019` | `ashare_pricing_candidate` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `in_sample_2000_2019` | `capm_market` | `reject_or_reweight` | 模型收益或显著性方向不满足进入 baseline 的下限，后续只能作为观察或重加权对象。 |
| `in_sample_2000_2019` | `carhart4_momentum` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `in_sample_2000_2019` | `ff3_equity_core` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `in_sample_2000_2019` | `ff5_like_profit_investment` | `needs_robustness_review` | 模型收益为正但显著性、冗余性或稳定性仍需第6章稳健性复验。 |
| `in_sample_2000_2019` | `q_factor_like` | `needs_robustness_review` | 模型收益为正但显著性、冗余性或稳定性仍需第6章稳健性复验。 |
| `in_sample_2000_2019` | `seven_factor_full` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd` | `ashare_pricing_candidate` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd` | `capm_market` | `needs_robustness_review` | 模型收益为正但显著性、冗余性或稳定性仍需第6章稳健性复验。 |
| `observation_2020_2026_ytd` | `carhart4_momentum` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd` | `ff3_equity_core` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd` | `ff5_like_profit_investment` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd` | `q_factor_like` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd` | `seven_factor_full` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |

## 产物

- fama_macbeth_results: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/fama_macbeth_results.csv`
- factor_model_returns: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/factor_model_returns.parquet`
- model_comparison: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/model_comparison.csv`
- factor_correlation: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/factor_correlation.csv`
- model_correlation: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/model_correlation.csv`
- model_admission_summary: `process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/MODEL-ADMISSION-SUMMARY.json`

## 边界

本报告只允许作为项目内部第4章研究证据和 CR-037/CR-038/CR-039 输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
