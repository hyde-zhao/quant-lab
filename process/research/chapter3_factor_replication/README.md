# 第三章因子复刻与数据问题审计

## 目标

本目录记录《因子投资：方法与实践》第三章 A 股主流因子复刻的项目内审计结论和实现入口。

本轮只做本地离线研究能力建设，不授权真实 provider fetch、lake write、catalog publish、QMT、simulation、live、账户、订单或凭据读取。

## 当前结论

项目已经具备较强的 CR030 多因子研究合同和门禁能力，包括 `FactorSpec`、`FactorRunSpec`、`FactorPanelContract`、`LabelWindowSpec`、`FactorEvaluationReport` 和组合层 blocked claims。但按第三章严格实证口径衡量，项目此前没有完整处理好第三章全部数据问题。

覆盖状态摘要：

| 领域 | 状态 | 结论 |
|---|---|---|
| 复权与收益 | partial | 合同层支持复权政策和复权泄漏门禁；第三章复刻尚未统一到书中后复权口径，既有换手率实验仍声明 qfq/ex-post 限制。 |
| 长期停牌复牌异常收益压缩 | missing | 未发现统一的复牌异常收益按 +/-10% 压缩规则和测试。 |
| 停牌处理 | partial | 门禁层能识别停牌/交易状态缺失；因子计算层此前未形成按动量、波动、beta 等用途区分的统一策略。 |
| 滚动窗口有效样本 | partial | 换手率实验短窗口接近 2/3 规则，但长窗口门槛不足；此前没有统一规则。新增模块默认按窗口 2/3。 |
| 财务报告期、基准报告期、调整/更正 | missing/partial | 只有通用 `available_at <= decision_time` 门禁；缺少财报 canonical schema、revision/as-of 查询、基准报告期和 TTM 实现。 |
| 黑名单与交易约束 | partial | lifecycle/tradability 门禁较完整；因子组合计算层此前未实际统一剔除 ST、退市、负净资产、次新、停牌、一字板。 |
| 科创板边界 | missing | 未发现第三章复刻专用板块边界配置。 |
| 1%/99% 缩尾与 zscore | covered | CR030 合同和实验 17-21 已支持 raw/directional/winsorized/zscore 层。 |
| 十分组和 5x5 双重排序 | partial | 异常换手率已有 5x5 复刻 POC；新增模块提供通用十分组和独立双重排序函数。 |
| Newey-West / Fama-MacBeth | partial/missing | 异常换手率 POC 有 Newey-West；通用 Fama-MacBeth 仍缺。 |

## 已新增实现

新增模块：

- `engine/chapter3_factor_replication.py`

新增测试：

- `tests/test_chapter3_factor_replication.py`

模块能力：

| 能力 | 入口 | 说明 |
|---|---|---|
| 第三章数据问题审计 | `audit_chapter3_data_issues(frames)` | 对传入的离线 DataFrame 字段做 covered/partial/missing 审计。 |
| 因子定义注册 | `chapter3_factor_definitions()` | 注册市场、规模、价值、动量、盈利、投资、异常换手率七个第三章因子。 |
| 第三章因子复刻 | `replicate_chapter3_factors(...)` | 从本地 `prices`、`market_cap`、`financials`、`trade_calendar` 生成 raw/directional/winsorized/zscore 矩阵。 |
| 因子面板输出 | `factor_matrices_to_panel(result)` | 输出包含 raw/directional/winsorized/zscore 的长表面板，便于接 CR030 合同。 |
| 单变量排序 | `single_sort_returns(...)` | 支持十分组或自定义分组。 |
| 独立双重排序 | `independent_double_sort_returns(...)` | 支持市值 x 目标因子的 5x5 或自定义组数双重排序。 |
| 多空摘要 | `long_short_summary(...)` | 输出 spread 均值、t 值和观察数量。 |

## 第三章因子注册清单

| factor_id | 书中因子 | 当前实现口径 | 方向 |
|---|---|---|---|
| `market_beta_252` | 市场因子 / CAPM beta | 个股收益对市值加权或等权市场收益的 252 日滚动 beta | neutral |
| `size_total_market_cap` | 规模因子 | `log(total_market_cap)` 后方向取负，统一为小市值更高分 | negative |
| `value_bm` | 价值因子 | 优先使用 `book_to_market/bm`；否则 `book_equity / market_cap` | positive |
| `momentum_12_1` | 动量因子 | 日频近似 `close[t-21] / close[t-252] - 1`，排除最近 21 个交易日 | positive |
| `profitability_roe_ttm` | 盈利因子 | 优先 `roe_ttm`；否则 `operating_profit_ttm / book_equity` | positive |
| `investment_asset_growth` | 投资因子 | 优先 `asset_growth`；否则 `total_assets / total_assets.shift(252) - 1` 后方向取负 | negative |
| `abnormal_turnover_21_252` | 换手率因子 | `mean(turnover_rate, 21) / mean(turnover_rate, 252)` 后方向取负 | negative |

## 已验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' UV_PROJECT_ENVIRONMENT=/tmp/local-backtest-qa-venv uv run --python 3.11 pytest -q tests/test_chapter3_factor_replication.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' UV_PROJECT_ENVIRONMENT=/tmp/local-backtest-qa-venv uv run --python 3.11 pytest -q tests/test_cr030_factor_spec_run_spec_contract.py tests/test_cr030_factor_panel_label_window_gates.py tests/test_cr030_factor_evaluation_report.py tests/test_cr030_multifactor_combiner.py
PYTHONPYCACHEPREFIX=/tmp/local-backtest-pycompile uv run --python 3.11 python -m py_compile engine/chapter3_factor_replication.py tests/test_chapter3_factor_replication.py
```

结果：

| 验证 | 结果 |
|---|---|
| 新增第三章复刻测试 | 5 passed |
| CR030 合同/面板/评价/组合测试 | 23 passed |
| py_compile | passed |

## 剩余 P0 缺口

1. 财务 PIT canonical schema 仍未补齐，价值、盈利、投资因子目前只能消费调用方已处理好的离线字段。
2. 复权口径仍需决定是否新增严格后复权研究字段；当前模块接受 `adjusted_close/hfq_close/qfq_close/close`，不会自行证明复权 PIT 无泄漏。
3. 长期停牌复牌异常收益 +/-10% 压缩规则仍未实现。
4. ST、退市、负净资产、次新、停牌、一字板剔除仍需作为实际组合筛选进入 runner。
5. Fama-MacBeth 和通用 Newey-West 统计模块仍需补齐。
6. 科创板边界、金融股默认保留策略、等权/市值加权并列报告仍需在第三章正式 runner 中冻结。
