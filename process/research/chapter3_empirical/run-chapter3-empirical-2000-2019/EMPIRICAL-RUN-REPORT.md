# CR-034 第三章 2000-2019 全样本实证报告

- status: `PASS`
- run_id: `run-chapter3-empirical-2000-2019`
- factor_panel_rows: `2640077`
- label_rows: `447186`
- rebalance_count: `239`
- max_memory_gb: `16.0`
- max_rss_gb_observed: `2.152325`
- memory_status: `pass`
- catalog_current_pointer_publish: `0`
- qmt_operation: `0`
- simulation_or_live_run: `0`

## 单因子摘要

| factor_id | status | observations | RankIC | IC | ICIR | long_short | turnover | admission |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `market_beta_252` | `pass` | 364845 | -0.022554 | -0.008701 | -0.060844 | -0.000343 | 0.333112 | `watch_or_reweight` |
| `size_total_market_cap` | `pass` | 407599 | 0.043877 | 0.032549 | 0.171512 | 0.008870 | 0.261349 | `research_candidate` |
| `value_bm` | `pass` | 379165 | 0.051312 | 0.030917 | 0.202208 | 0.007885 | 0.241325 | `research_candidate` |
| `momentum_12_1` | `pass` | 366687 | -0.001426 | 0.002680 | 0.015935 | 0.001503 | 0.492497 | `watch_or_reweight` |
| `profitability_roe_ttm` | `pass` | 310384 | 0.053687 | 0.044300 | 0.232226 | 0.003129 | 0.256537 | `research_candidate` |
| `investment_asset_growth` | `pass` | 357390 | -0.005783 | -0.004401 | -0.045327 | -0.000973 | 0.297153 | `watch_or_reweight` |
| `abnormal_turnover_21_252` | `pass` | 384360 | 0.073476 | 0.064519 | 0.567668 | 0.018386 | 0.692913 | `research_candidate` |

## 产物

- factor_panel: `reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019/factor_panel.parquet`
- manifest: `reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019/factor_panel_manifest.json`
- preprocessing_summary: `reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019/preprocessing_summary.csv`
- metrics_csv: `process/research/chapter3_empirical/run-chapter3-empirical-2000-2019/factor_metrics.csv`
- portfolio_plan: `process/research/chapter3_empirical/run-chapter3-empirical-2000-2019/MULTIFACTOR-ADMISSION-SUMMARY.json`

## 多因子研究准入结论

本报告允许作为项目内部多因子研究输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
