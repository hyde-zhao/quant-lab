# 第四章多因子模型 GRS 检验

- chapter4_run_id: `run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613`
- input_panel: `reports/chapter3_factor_panel/run-chapter3-empirical-2020-2026-warmup-corrected-for-chapter4-20260613/factor_panel.parquet`
- label_root: `process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-warmup-corrected-for-chapter4-20260613/label_parts`
- test_portfolios: `size_value_5x5`, `size_turnover_5x5`
- RHS 因子收益：各因子 5 分组最高组减最低组月度收益
- GRS 原假设：全部测试组合 alpha 联合为 0；p 值越小，越拒绝模型完全解释测试组合收益。

| test_set | model_id | N | K | T | GRS_F | p_value | alpha_mean_abs | alpha_max_abs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| size_value_5x5 | `capm_market` | 25 | 1 | 75 | 2.197336 | 0.009215 | 0.012952 | 0.026921 |
| size_value_5x5 | `ff3_equity_core` | 25 | 3 | 75 | 2.061043 | 0.016081 | 0.004306 | 0.013332 |
| size_value_5x5 | `carhart4_momentum` | 25 | 4 | 75 | 1.934515 | 0.025922 | 0.005716 | 0.014502 |
| size_value_5x5 | `ff5_like_profit_investment` | 25 | 5 | 74 | 1.544784 | 0.101808 | 0.005653 | 0.015713 |
| size_value_5x5 | `q_factor_like` | 25 | 4 | 74 | 1.379062 | 0.170994 | 0.008097 | 0.013600 |
| size_value_5x5 | `ashare_pricing_candidate` | 25 | 6 | 74 | 1.634346 | 0.076986 | 0.011819 | 0.018976 |
| size_value_5x5 | `seven_factor_full` | 25 | 7 | 74 | 1.375612 | 0.177108 | 0.005327 | 0.014511 |
| size_turnover_5x5 | `capm_market` | 25 | 1 | 75 | 3.893614 | 0.000024 | 0.013120 | 0.026216 |
| size_turnover_5x5 | `ff3_equity_core` | 25 | 3 | 75 | 3.506231 | 0.000103 | 0.004998 | 0.009616 |
| size_turnover_5x5 | `carhart4_momentum` | 25 | 4 | 75 | 3.633111 | 0.000075 | 0.006904 | 0.010000 |
| size_turnover_5x5 | `ff5_like_profit_investment` | 25 | 5 | 74 | 3.424515 | 0.000176 | 0.006059 | 0.010028 |
| size_turnover_5x5 | `q_factor_like` | 25 | 4 | 74 | 4.099635 | 0.000019 | 0.008389 | 0.013114 |
| size_turnover_5x5 | `ashare_pricing_candidate` | 25 | 6 | 74 | 3.825040 | 0.000056 | 0.011873 | 0.016867 |
| size_turnover_5x5 | `seven_factor_full` | 25 | 7 | 74 | 3.316955 | 0.000297 | 0.005556 | 0.010753 |

## 产物

- grs_results: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/grs_results.csv`
- grs_alpha_detail: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/grs_alpha_detail.csv`
- grs_factor_returns: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/grs_factor_returns.csv`
- size_value returns: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/grs_test_portfolio_returns_size_value_5x5.csv`
- size_turnover returns: `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-2020-2026-warmup-corrected-20260613/grs_test_portfolio_returns_size_turnover_5x5.csv`
