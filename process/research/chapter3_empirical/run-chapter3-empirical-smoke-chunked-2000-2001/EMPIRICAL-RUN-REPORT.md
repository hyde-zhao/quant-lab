# CR-034 第三章 2000-2019 全样本实证报告

- status: `PASS`
- run_id: `run-chapter3-empirical-smoke-chunked-2000-2001`
- factor_panel_rows: `63206`
- label_rows: `22962`
- rebalance_count: `23`
- catalog_current_pointer_publish: `0`
- qmt_operation: `0`
- simulation_or_live_run: `0`

## 单因子摘要

| factor_id | status | observations | RankIC | IC | ICIR | long_short | turnover | admission |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `market_beta_252` | `pass` | 14413 | -0.001799 | 0.004028 | 0.031157 | -0.001437 | 0.315907 | `watch_or_reweight` |
| `size_total_market_cap` | `pass` | 20230 | 0.115583 | 0.096707 | 0.630826 | 0.024343 | 0.243328 | `research_candidate` |
| `value_bm` | `pass` | 1344 | 0.115126 | 0.096069 | 0.379098 | 0.016803 | 0.293151 | `research_candidate` |
| `momentum_12_1` | `pass` | 9925 | 0.021135 | 0.025329 | 0.231092 | 0.004226 | 0.464029 | `research_candidate` |
| `profitability_roe_ttm` | `pass` | 304 | 0.015140 | 0.112047 | 0.466283 | 0.036375 | 0.255952 | `research_candidate` |
| `investment_asset_growth` | `pass` | 458 | 0.037507 | 0.022983 | 0.132168 | -0.008535 | 0.270408 | `watch_or_reweight` |
| `abnormal_turnover_21_252` | `pass` | 15398 | 0.086619 | 0.070455 | 0.718098 | 0.014303 | 0.719539 | `research_candidate` |

## 产物

- factor_panel: `reports/chapter3_factor_panel/run-chapter3-empirical-smoke-chunked-2000-2001/factor_panel.parquet`
- manifest: `reports/chapter3_factor_panel/run-chapter3-empirical-smoke-chunked-2000-2001/factor_panel_manifest.json`
- preprocessing_summary: `reports/chapter3_factor_panel/run-chapter3-empirical-smoke-chunked-2000-2001/preprocessing_summary.csv`
- metrics_csv: `process/research/chapter3_empirical/run-chapter3-empirical-smoke-chunked-2000-2001/factor_metrics.csv`
- portfolio_plan: `process/research/chapter3_empirical/run-chapter3-empirical-smoke-chunked-2000-2001/MULTIFACTOR-ADMISSION-SUMMARY.json`

## 多因子研究准入结论

本报告允许作为项目内部多因子研究输入，不构成 production-valid、QMT-ready、simulation-ready 或 live-ready 声明。
