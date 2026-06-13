# CR-036 第五章异象复刻报告

- run_id: `run-stage6-full-ch5-20260611`
- status: `PASS`
- provider_fetch: `0`
- lake_write: `0`
- catalog_publish: `0`
- qmt_operation: `0`
- simulation_or_live: `0`

## 样本摘要

| sample_id | status | panel_rows | label_rows | anomaly_panel_rows | anomaly_return_rows | alpha_test_rows |
|---|---|---:|---:|---:|---:|---:|
| `in_sample_2000_2019` | `PASS` | 2550289 | 447186 | 969286 | 633 | 9 |
| `observation_2020_2026_ytd` | `PASS` | 1957024 | 371877 | 777587 | 195 | 9 |

## 异象准入摘要

| sample_id | anomaly_id | admission | mean_long_short | t_stat | max_abs_alpha_t |
|---|---|---|---:|---:|---:|
| `in_sample_2000_2019` | `fundamental_anchor_reversal` | `watch_needs_robustness_review` | 0.002948 | 1.098460 | 2.415404 |
| `in_sample_2000_2019` | `idiosyncratic_volatility_proxy` | `reject_or_reweight` | -0.014755 | -4.703716 | 5.936464 |
| `in_sample_2000_2019` | `valuation_extreme_spread` | `reject_or_reweight` | -0.001967 | -1.531937 | 1.723286 |
| `observation_2020_2026_ytd` | `fundamental_anchor_reversal` | `watch` | 0.002251 | 0.457923 | 2.835862 |
| `observation_2020_2026_ytd` | `idiosyncratic_volatility_proxy` | `reject_or_reweight` | -0.026684 | -3.525218 | 4.241411 |
| `observation_2020_2026_ytd` | `valuation_extreme_spread` | `reject_or_reweight` | -0.006537 | -2.813429 | 3.645934 |

## 缺口登记

| sample_id | gap_id | status | severity | impact |
|---|---|---|---|---|
| `in_sample_2000_2019` | `CR036-GAP-BOOK-CHAPTER5-SOURCE` | `open-with-proxy-implemented` | `medium` | 报告不得宣称逐字严格复刻第5章，只能宣称项目内可执行复刻。 |
| `in_sample_2000_2019` | `CR036-GAP-valuation_extreme_spread` | `open-with-proxy-implemented` | `medium` | 进入 CR-037/CR-038 前必须复验或补齐字段。 |
| `in_sample_2000_2019` | `CR036-GAP-fundamental_anchor_reversal` | `open-with-proxy-implemented` | `medium` | 进入 CR-037/CR-038 前必须复验或补齐字段。 |
| `in_sample_2000_2019` | `CR036-GAP-idiosyncratic_volatility_proxy` | `open-with-proxy-implemented` | `medium` | 进入 CR-037/CR-038 前必须复验或补齐字段。 |
| `observation_2020_2026_ytd` | `CR036-GAP-BOOK-CHAPTER5-SOURCE` | `open-with-proxy-implemented` | `medium` | 报告不得宣称逐字严格复刻第5章，只能宣称项目内可执行复刻。 |
| `observation_2020_2026_ytd` | `CR036-GAP-valuation_extreme_spread` | `open-with-proxy-implemented` | `medium` | 进入 CR-037/CR-038 前必须复验或补齐字段。 |
| `observation_2020_2026_ytd` | `CR036-GAP-fundamental_anchor_reversal` | `open-with-proxy-implemented` | `medium` | 进入 CR-037/CR-038 前必须复验或补齐字段。 |
| `observation_2020_2026_ytd` | `CR036-GAP-idiosyncratic_volatility_proxy` | `open-with-proxy-implemented` | `medium` | 进入 CR-037/CR-038 前必须复验或补齐字段。 |

## 产物

- anomaly_panel: `reports/stage6_full_run_20260611/chapter5_anomalies/run-stage6-full-ch5-20260611/anomaly_panel.parquet`
- anomaly_returns: `reports/stage6_full_run_20260611/chapter5_anomalies/run-stage6-full-ch5-20260611/anomaly_returns.csv`
- alpha_tests: `reports/stage6_full_run_20260611/chapter5_anomalies/run-stage6-full-ch5-20260611/alpha_tests.csv`
- anomaly_correlation: `reports/stage6_full_run_20260611/chapter5_anomalies/run-stage6-full-ch5-20260611/anomaly_correlation.csv`
- gap_register: `reports/stage6_full_run_20260611/chapter5_anomalies/run-stage6-full-ch5-20260611/gap_register.csv`
- anomaly_admission_summary: `process/research/stage6_full_run_20260611/chapter5_anomalies/run-stage6-full-ch5-20260611/ANOMALY-ADMISSION-SUMMARY.json`

## 边界

本报告只允许作为项目内部第5章异象研究证据和 CR-037/CR-038/CR-039 输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
