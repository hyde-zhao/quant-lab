# CR-034 第三章 2020-01-01..2026-05-28 全样本实证报告

- status: `PASS`
- run_id: `run-chapter3-empirical-2020-2026-ytd`
- evaluation_window: `2020-01-01`..`2026-05-28`
- factor_panel_rows: `2019002`
- label_rows: `371877`
- rebalance_count: `76`
- max_memory_gb: `16.0`
- max_rss_gb_observed: `5.549709`
- memory_status: `pass`
- catalog_current_pointer_publish: `0`
- qmt_operation: `0`
- simulation_or_live_run: `0`

## 单因子摘要

| factor_id | status | observations | RankIC | IC | ICIR | long_short | turnover | admission |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `market_beta_252` | `pass` | 276565 | -0.021523 | -0.001569 | -0.010865 | 0.003699 | 0.274592 | `watch_or_reweight` |
| `size_total_market_cap` | `pass` | 317008 | 0.057382 | 0.041861 | 0.281601 | 0.013319 | 0.211457 | `research_candidate` |
| `value_bm` | `pass` | 304294 | 0.059445 | 0.014716 | 0.113204 | 0.010026 | 0.160105 | `research_candidate` |
| `momentum_12_1` | `pass` | 273116 | -0.032828 | -0.020360 | -0.165880 | 0.005074 | 0.437169 | `watch_or_reweight` |
| `profitability_roe_ttm` | `pass` | 303289 | 0.001547 | -0.003919 | -0.039357 | -0.001546 | 0.190698 | `watch_or_reweight` |
| `investment_asset_growth` | `pass` | 251911 | 0.008630 | 0.006468 | 0.085434 | 0.001249 | 0.229588 | `research_candidate` |
| `abnormal_turnover_21_252` | `pass` | 288128 | 0.077107 | 0.039079 | 0.342262 | 0.014624 | 0.646980 | `research_candidate` |

## 产物

- factor_panel: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd/factor_panel.parquet`
- manifest: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd/factor_panel_manifest.json`
- preprocessing_summary: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd/preprocessing_summary.csv`
- metrics_csv: `process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd/factor_metrics.csv`
- portfolio_plan: `process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd/MULTIFACTOR-ADMISSION-SUMMARY.json`

## 多因子研究准入结论

本报告允许作为项目内部多因子研究输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
