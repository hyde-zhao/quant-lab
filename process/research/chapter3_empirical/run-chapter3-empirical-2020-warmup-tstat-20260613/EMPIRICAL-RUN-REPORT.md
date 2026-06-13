# CR-034 第三章 2018-07-01..2020-12-31 全样本实证报告

- status: `PASS`
- run_id: `run-chapter3-empirical-2020-warmup-tstat-20260613`
- evaluation_window: `2018-07-01`..`2020-12-31`
- factor_panel_rows: `520530`
- label_rows: `107784`
- rebalance_count: `29`
- max_memory_gb: `16.0`
- max_rss_gb_observed: `3.954872`
- memory_status: `pass`
- catalog_current_pointer_publish: `0`
- qmt_operation: `0`
- simulation_or_live_run: `0`

## 单因子摘要

| factor_id | status | observations | long_short_return | long_short_t_stat | t_stat_method | RankIC | IC | ICIR | turnover | admission |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| `market_beta_252` | `pass` | 70857 | 0.000343 | 0.051854 | `newey_west` | -0.019091 | 0.004251 | 0.051715 | 0.228427 | `watch_or_reweight` |
| `size_total_market_cap` | `pass` | 99972 | 0.002646 | 0.377465 | `newey_west` | -0.000009 | -0.001075 | -0.009340 | 0.225642 | `watch_or_reweight` |
| `value_bm` | `pass` | 94257 | -0.005024 | -0.601354 | `newey_west` | 0.012860 | -0.011036 | -0.102806 | 0.208751 | `watch_or_reweight` |
| `momentum_12_1` | `pass` | 58988 | 0.017380 | 1.324678 | `newey_west` | 0.015141 | 0.031352 | 0.217661 | 0.401242 | `research_candidate` |
| `profitability_roe_ttm` | `pass` | 94234 | 0.010853 | 1.388971 | `newey_west` | 0.042768 | 0.023131 | 0.231921 | 0.214907 | `research_candidate` |
| `investment_asset_growth` | `pass` | 27668 | 0.000569 | 0.038391 | `newey_west` | -0.069770 | -0.034229 | -0.213947 | 0.320417 | `watch_or_reweight` |
| `abnormal_turnover_21_252` | `pass` | 72911 | 0.009020 | 1.245064 | `newey_west` | 0.034326 | 0.024381 | 0.231363 | 0.625358 | `research_candidate` |

## 产物

- factor_panel: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-warmup-tstat-20260613/factor_panel.parquet`
- manifest: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-warmup-tstat-20260613/factor_panel_manifest.json`
- preprocessing_summary: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-warmup-tstat-20260613/preprocessing_summary.csv`
- metrics_csv: `process/research/chapter3_empirical/run-chapter3-empirical-2020-warmup-tstat-20260613/factor_metrics.csv`
- portfolio_plan: `process/research/chapter3_empirical/run-chapter3-empirical-2020-warmup-tstat-20260613/MULTIFACTOR-ADMISSION-SUMMARY.json`

## 多因子研究准入结论

本报告允许作为项目内部多因子研究输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
