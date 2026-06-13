# CR-034 第三章 2000-01-01..2001-12-31 全样本实证报告

- status: `PASS`
- run_id: `run-chapter3-empirical-smoke-tstat-20260613`
- evaluation_window: `2000-01-01`..`2001-12-31`
- factor_panel_rows: `59615`
- label_rows: `22962`
- rebalance_count: `23`
- max_memory_gb: `16.0`
- max_rss_gb_observed: `0.886673`
- memory_status: `pass`
- catalog_current_pointer_publish: `0`
- qmt_operation: `0`
- simulation_or_live_run: `0`

## 单因子摘要

| factor_id | status | observations | long_short_return | long_short_t_stat | t_stat_method | RankIC | IC | ICIR | turnover | admission |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| `market_beta_252` | `pass` | 12544 | 0.001664 | 0.326809 | `newey_west` | 0.008960 | 0.017192 | 0.125951 | 0.333226 | `research_candidate` |
| `size_total_market_cap` | `pass` | 20230 | 0.029746 | 2.541501 | `newey_west` | 0.115583 | 0.096707 | 0.630826 | 0.243328 | `research_candidate` |
| `value_bm` | `pass` | 1344 | 0.019738 | 0.932225 | `newey_west` | 0.115126 | 0.096069 | 0.379098 | 0.293151 | `research_candidate` |
| `momentum_12_1` | `pass` | 9925 | 0.007252 | 1.011459 | `newey_west` | 0.021135 | 0.025329 | 0.231092 | 0.464029 | `research_candidate` |
| `profitability_roe_ttm` | `pass` | 304 | 0.007074 | 0.376451 | `newey_west` | 0.015140 | 0.112047 | 0.466283 | 0.255952 | `research_candidate` |
| `investment_asset_growth` | `pass` | 499 | -0.007646 | -0.834837 | `newey_west` | 0.057491 | 0.013813 | 0.079238 | 0.184673 | `watch_or_reweight` |
| `abnormal_turnover_21_252` | `pass` | 13659 | 0.014527 | 2.629704 | `newey_west` | 0.084603 | 0.072235 | 0.705846 | 0.724958 | `research_candidate` |

## 产物

- factor_panel: `reports/chapter3_factor_panel/run-chapter3-empirical-smoke-tstat-20260613/factor_panel.parquet`
- manifest: `reports/chapter3_factor_panel/run-chapter3-empirical-smoke-tstat-20260613/factor_panel_manifest.json`
- preprocessing_summary: `reports/chapter3_factor_panel/run-chapter3-empirical-smoke-tstat-20260613/preprocessing_summary.csv`
- metrics_csv: `process/research/chapter3_empirical/run-chapter3-empirical-smoke-tstat-20260613/factor_metrics.csv`
- portfolio_plan: `process/research/chapter3_empirical/run-chapter3-empirical-smoke-tstat-20260613/MULTIFACTOR-ADMISSION-SUMMARY.json`

## 多因子研究准入结论

本报告允许作为项目内部多因子研究输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
