# CR-034 第三章 2020-01-01..2026-05-28 全样本实证报告

- status: `PASS`
- run_id: `run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610`
- evaluation_window: `2020-01-01`..`2026-05-28`
- factor_panel_rows: `1957024`
- label_rows: `371877`
- rebalance_count: `76`
- max_memory_gb: `16.0`
- max_rss_gb_observed: `5.670963`
- memory_status: `pass`
- catalog_current_pointer_publish: `0`
- qmt_operation: `0`
- simulation_or_live_run: `0`

## 单因子摘要

| factor_id | status | observations | RankIC | IC | ICIR | long_short | turnover | admission |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `market_beta_252` | `pass` | 276664 | -0.021429 | -0.001520 | -0.010517 | 0.003724 | 0.274413 | `watch_or_reweight` |
| `size_total_market_cap` | `pass` | 317008 | 0.057382 | 0.041861 | 0.281601 | 0.013319 | 0.211457 | `research_candidate` |
| `value_bm` | `pass` | 304294 | 0.059445 | 0.014716 | 0.113204 | 0.010026 | 0.160105 | `research_candidate` |
| `momentum_12_1` | `pass` | 273116 | -0.032828 | -0.020360 | -0.165880 | 0.005074 | 0.437169 | `watch_or_reweight` |
| `profitability_roe_ttm` | `pass` | 303289 | 0.001547 | -0.003919 | -0.039357 | -0.001546 | 0.190698 | `watch_or_reweight` |
| `investment_asset_growth` | `pass` | 190069 | 0.013818 | 0.006931 | 0.093821 | 0.002469 | 0.345138 | `research_candidate` |
| `abnormal_turnover_21_252` | `pass` | 288157 | 0.077076 | 0.038868 | 0.341470 | 0.014574 | 0.646965 | `research_candidate` |

## 产物

- factor_panel: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/factor_panel.parquet`
- manifest: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/factor_panel_manifest.json`
- preprocessing_summary: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/preprocessing_summary.csv`
- metrics_csv: `process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/factor_metrics.csv`
- portfolio_plan: `process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd-financial-fallback-20260610/MULTIFACTOR-ADMISSION-SUMMARY.json`

## 多因子研究准入结论

本报告允许作为项目内部多因子研究输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
