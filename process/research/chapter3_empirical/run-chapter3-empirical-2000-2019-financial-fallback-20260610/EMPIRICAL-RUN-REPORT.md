# CR-034 第三章 2000-01-01..2019-12-31 全样本实证报告

- status: `PASS`
- run_id: `run-chapter3-empirical-2000-2019-financial-fallback-20260610`
- evaluation_window: `2000-01-01`..`2019-12-31`
- factor_panel_rows: `2550289`
- label_rows: `447186`
- rebalance_count: `239`
- max_memory_gb: `16.0`
- max_rss_gb_observed: `3.485092`
- memory_status: `pass`
- catalog_current_pointer_publish: `0`
- qmt_operation: `0`
- simulation_or_live_run: `0`

## 单因子摘要

| factor_id | status | observations | RankIC | IC | ICIR | long_short | turnover | admission |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `market_beta_252` | `pass` | 365273 | -0.022490 | -0.008635 | -0.060461 | -0.000207 | 0.333274 | `watch_or_reweight` |
| `size_total_market_cap` | `pass` | 407599 | 0.043877 | 0.032549 | 0.171512 | 0.008870 | 0.261349 | `research_candidate` |
| `value_bm` | `pass` | 379165 | 0.051312 | 0.030917 | 0.202208 | 0.007885 | 0.241325 | `research_candidate` |
| `momentum_12_1` | `pass` | 366687 | -0.001426 | 0.002680 | 0.015935 | 0.001503 | 0.492497 | `watch_or_reweight` |
| `profitability_roe_ttm` | `pass` | 310384 | 0.053687 | 0.044300 | 0.232226 | 0.003129 | 0.256537 | `research_candidate` |
| `investment_asset_growth` | `pass` | 269166 | -0.005518 | -0.005110 | -0.050382 | 0.000676 | 0.342994 | `watch_or_reweight` |
| `abnormal_turnover_21_252` | `pass` | 385198 | 0.073408 | 0.064554 | 0.567149 | 0.018411 | 0.692959 | `research_candidate` |

## 产物

- factor_panel: `reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019-financial-fallback-20260610/factor_panel.parquet`
- manifest: `reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019-financial-fallback-20260610/factor_panel_manifest.json`
- preprocessing_summary: `reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019-financial-fallback-20260610/preprocessing_summary.csv`
- metrics_csv: `process/research/chapter3_empirical/run-chapter3-empirical-2000-2019-financial-fallback-20260610/factor_metrics.csv`
- portfolio_plan: `process/research/chapter3_empirical/run-chapter3-empirical-2000-2019-financial-fallback-20260610/MULTIFACTOR-ADMISSION-SUMMARY.json`

## 多因子研究准入结论

本报告允许作为项目内部多因子研究输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
