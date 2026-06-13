# CR-035 第四章多因子模型定价检验报告

- run_id: `run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613`
- status: `PASS`
- provider_fetch: `0`
- lake_write: `0`
- catalog_publish: `0`
- qmt_operation: `0`
- simulation_or_live: `0`

## 样本摘要

| sample_id | status | panel_rows | label_rows | matched_rows | rebalance_count |
|---|---|---:|---:|---:|---:|
| `observation_2020_2026_ytd_warmup_corrected` | `PASS` | 2084333 | 367701 | 313441 | 75 |

## 模型准入摘要

| sample_id | model_id | admission | reason |
|---|---|---|---|
| `observation_2020_2026_ytd_warmup_corrected` | `ashare_pricing_candidate` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd_warmup_corrected` | `capm_market` | `needs_robustness_review` | 模型收益为正但显著性、冗余性或稳定性仍需第6章稳健性复验。 |
| `observation_2020_2026_ytd_warmup_corrected` | `carhart4_momentum` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd_warmup_corrected` | `ff3_equity_core` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd_warmup_corrected` | `ff5_like_profit_investment` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd_warmup_corrected` | `q_factor_like` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |
| `observation_2020_2026_ytd_warmup_corrected` | `seven_factor_full` | `baseline_candidate` | 样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。 |

## 产物

- fama_macbeth_results: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/fama_macbeth_results.csv`
- factor_model_returns: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/factor_model_returns.parquet`
- model_comparison: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/model_comparison.csv`
- factor_correlation: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/factor_correlation.csv`
- model_correlation: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/model_correlation.csv`
- model_admission_summary: `process/research/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/MODEL-ADMISSION-SUMMARY.json`

## 边界

本报告只允许作为项目内部第4章研究证据和 CR-037/CR-038/CR-039 输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
