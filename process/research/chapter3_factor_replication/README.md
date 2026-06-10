# 第三章因子复刻与数据问题审计

## 目标

本目录记录《因子投资：方法与实践》第三章 A 股主流因子复刻的项目内审计结论和实现入口。

本轮只做本地离线研究能力建设，不授权真实 provider fetch、lake write、catalog publish、QMT、simulation、live、账户、订单或凭据读取。

## 第三章关键口径

本轮重新阅读书籍 Markdown 的第3章，定位范围为 `3.1 数据和流程` 到 `3.8 换手率因子`。工程化落地遵循以下口径：

| 领域 | 第三章口径 |
|---|---|
| 价格与收益 | 收益率和历史表现使用后复权价格；后复权不可得时必须在运行限制中声明替代列。 |
| 复牌异常收益 | 1996-12-16 后日收益超过 +10% 或低于 -10% 时压缩到 +/-10%，以降低长期停牌复牌异常收益污染。 |
| 停牌处理 | 动量价格基准可使用填充后的价格逻辑；波动率、beta、收益序列不能把停牌日当成 0 收益。 |
| 最少交易日 | 滚动窗口指标有效样本数至少达到窗口的 2/3。 |
| 财务 PIT | 财报必须区分报告期、基准报告期、调整和更正；历史回溯只能使用当前时点可得的最新信息。 |
| TTM | 利润/现金流 TTM 用当前报告期 + 上年年报 - 上年同比报告期；缺少同比/年报时可年化。资产负债表可用最近值、四期均值或同比均值。 |
| 股票池 | 保留金融行业；剔除待退市、ST/风险警示、净资产为负、上市不足一年次新股。 |
| 异常值 | 截面使用左右各 1% 缩尾。 |
| 排序检验 | 单变量十分组；除规模外，目标变量与市值做 5x5 独立双重排序；投资因子另用 ROA 与总资产增长率做条件双重排序。 |
| 调仓与可交易 | 每月末换仓；调仓日剔除停牌、一字涨停、一字跌停；交易成本设为 0。 |
| 研究范围 | 2000-01-01 至 2019-12-31，沪深主板、中小板、创业板，排除科创板。 |
| 权重与显著性 | 组合收益同时报告等权和总市值加权；收益率 t 值使用 Newey-West 调整。 |
| 因子 | 市场、规模、价值 BM、动量 12-1、盈利 ROE(TTM)、投资总资产增长率、异常换手率。 |

## 当前结论

项目已经具备较强的 CR030 多因子研究合同和门禁能力，包括 `FactorSpec`、`FactorRunSpec`、`FactorPanelContract`、`LabelWindowSpec`、`FactorEvaluationReport` 和组合层 blocked claims。基线时按第三章严格实证口径衡量，项目没有完整处理好第三章全部数据问题；本轮已把第三章 P0 缺口整改为本地离线工程能力，但仍未读取真实 lake、未触发 provider、未声明真实实证结果。

2026-06-10 复核结论：书中第3章正文明确将 `3.2` 到 `3.8` 定义为七类主流因子，即市场、规模、价值、动量、盈利、投资和换手率。当前项目不需要额外新增低波动、特质波动、流动性、短期反转等第5章/第6章异象因子来满足“第三章复刻”范围。第三章因子数量已覆盖完整；本轮继续整改的是盈利和投资因子的 fallback 公式追溯性，使其在缺少直接 `roe_ttm` / `asset_growth` 字段时也按书中定义衍生。

覆盖状态摘要：

| 领域 | 状态 | 结论 |
|---|---|---|
| 复权与收益 | covered/offline | `Chapter3ResearchPolicy` 默认优先 `back_adjusted_close/hfq_close`；`prepare_chapter3_research_data` 会记录非后复权替代限制。 |
| 长期停牌复牌异常收益压缩 | covered/offline | `build_chapter3_return_matrix` 对 1996-12-16 后日收益做 +/-10% 压缩，并对停牌日收益置缺。 |
| 停牌处理 | covered/offline | `trade_status/is_suspended` 进入收益和可交易掩码；beta/市场收益不把停牌当 0 收益。 |
| 滚动窗口有效样本 | covered/offline | 滚动 beta、动量、异常换手率继续使用 `min_period_ratio`，默认窗口 2/3。 |
| 财务报告期、基准报告期、调整/更正 | partial/offline | 新增 `canonicalize_chapter3_financials`，按 PIT 可用日和记录优先级稳定去重；真实财报 revision/as-of 数据仍需调用方离线提供。 |
| 黑名单与交易约束 | covered/offline | 新增 `build_chapter3_universe_mask` 和 `build_chapter3_tradable_mask`，覆盖 ST、退市、负净资产、次新、科创板、停牌、一字涨停/跌停。 |
| 科创板边界 | covered/offline | `Chapter3ResearchPolicy.exclude_star_market=True`，默认排除 `688*` 和 board/market 标记为科创板的股票。 |
| 1%/99% 缩尾与 zscore | covered | CR030 合同和实验 17-21 已支持 raw/directional/winsorized/zscore 层。 |
| 十分组和 5x5 双重排序 | covered/offline | 新增单变量排序、独立双重排序、条件双重排序，均支持等权和总市值加权。 |
| Newey-West / Fama-MacBeth | covered/offline | 新增 `newey_west_t_stat`、`long_short_summary(..., t_stat_method="newey_west")` 和 `fama_macbeth_regression`。 |

## 2026-06-08 边界整改记录

用户审查指出：因子以 `chapter3` 作为长期命名空间不合理，且 `engine/` 目录中的第三章模块不应同时承载通用因子库、计算公式和复刻实验。整改决策如下：

1. `chapter3` 只表示书籍第三章复刻来源、数据口径和 runner policy，不作为通用因子身份。
2. 因子 ID 保持通用语义，例如 `value_bm`、`momentum_12_1`，不得改为 `chapter3_value_bm`。
3. 通用因子定义迁移到 `engine/factor_library.py`，并通过 `source_refs` 记录第三章来源。
4. 通用因子矩阵计算迁移到 `engine/factor_calculators.py`。
5. 通用排序检验和统计方法迁移到 `engine/factor_statistics.py`。
6. `engine/chapter3_factor_replication.py` 保留为第三章复刻适配层，负责后复权优先、收益压缩、停牌置缺、股票池和可交易过滤、月末调仓等第三章专用口径。
7. 长期新增因子入口已收敛为 `EquityFactorDefinition -> to_factor_spec(...) -> calculator_registry -> factor panel / evaluation`，说明见 `docs/CR030-FACTOR-RESEARCH-QUICKSTART.md`。

追溯文件：

- `process/changes/CR-033-FACTOR-LIBRARY-BOUNDARY-REMEDIATION-2026-06-08.md`
- `process/checks/CP6-CR033-factor-library-boundary-remediation-CODING-DONE.md`
- `process/checks/CP7-CR033-factor-library-boundary-remediation-VERIFICATION-DONE.md`

## 已新增实现

新增模块：

- `engine/factor_library.py`
- `engine/factor_calculators.py`
- `engine/factor_statistics.py`
- `engine/chapter3_factor_replication.py`

新增测试：

- `tests/test_factor_library.py`
- `tests/test_factor_calculators.py`
- `tests/test_factor_statistics.py`
- `tests/test_chapter3_factor_replication.py`

模块能力：

| 能力 | 入口 | 说明 |
|---|---|---|
| 通用因子定义注册 | `engine.factor_library.equity_core_factor_definitions()` | canonical 注册市场、规模、价值、动量、盈利、投资、异常换手率七个通用权益因子；第三章只写入 `source_refs`。 |
| CR030 FactorSpec 导出 | `engine.factor_library.to_factor_spec(...)` | 将通用因子定义导出为项目 CR030 `FactorSpec`，避免另造平行合同。 |
| 因子定义校验和扩展 | `engine.factor_library.validate_equity_factor_library(...)`、`build_equity_factor_library(...)` | 支持长期新增因子，拒绝 `chapter*` 章节命名空间污染因子 ID。 |
| 通用因子矩阵计算 | `engine.factor_calculators.compute_equity_factor_matrices(...)` | 生成 raw/directional/winsorized/zscore 矩阵，不绑定第三章样本口径。 |
| 通用计算器注册 | `compute_equity_factor_matrices(..., calculator_registry=...)` | 支持长期新增自定义因子计算器，不需要修改第三章模块。 |
| 通用因子面板输出 | `engine.factor_calculators.factor_matrices_to_panel(...)` | 输出包含 raw/directional/winsorized/zscore 的长表面板，便于接 CR030 合同。 |
| 通用排序和统计 | `engine.factor_statistics.*` | 单变量排序、独立双重排序、条件双重排序、Newey-West、Fama-MacBeth。 |
| 第三章数据问题审计 | `audit_chapter3_data_issues(frames)` | 对传入的离线 DataFrame 字段做 covered/partial/missing 审计。 |
| 第三章因子定义视图 | `chapter3_factor_definitions()` | 返回通用因子库中带第三章来源的七个因子定义，保留复刻入口兼容。 |
| 第三章因子复刻 | `replicate_chapter3_factors(...)` | 从本地 `prices`、`market_cap`、`financials`、`trade_calendar` 生成第三章口径下的 raw/directional/winsorized/zscore 矩阵。 |
| 第三章因子面板输出 | `factor_matrices_to_panel(result)` | 第三章兼容 wrapper，内部调用通用 `engine.factor_calculators.factor_matrices_to_panel(...)`。 |
| 第三章研究预处理 | `prepare_chapter3_research_data(...)` | 输出后复权价格、压缩收益、股票池掩码、可交易掩码、月末调仓日。 |
| 财务 PIT 规范化 | `canonicalize_chapter3_financials(...)` | 对同一 symbol/report_period/available_at 多记录按第三章 PIT 优先级去重。 |

## 第三章因子注册清单

| factor_id | 书中因子 | 当前实现口径 | 方向 |
|---|---|---|---|
| `market_beta_252` | 市场因子 / CAPM beta | 个股收益对市值加权或等权市场收益的 252 日滚动 beta | neutral |
| `size_total_market_cap` | 规模因子 | `log(total_market_cap)` 后方向取负，统一为小市值更高分 | negative |
| `value_bm` | 价值因子 | 优先使用 `book_to_market/bm`；否则 `book_equity / market_cap` | positive |
| `momentum_12_1` | 动量因子 | 日频近似 `close[t-21] / close[t-252] - 1`，排除最近 21 个交易日 | positive |
| `profitability_roe_ttm` | 盈利因子 | 优先 `roe_ttm`；否则按书中口径用 `operating_profit_ttm / 最近四个报告期平均股东权益` 衍生 | positive |
| `investment_asset_growth` | 投资因子 | 优先 `asset_growth`；否则按书中口径用 `年报总资产 / 上一年年报总资产 - 1` 衍生，方向取负 | negative |
| `abnormal_turnover_21_252` | 换手率因子 | `mean(turnover_rate, 21) / mean(turnover_rate, 252)` 后方向取负 | negative |

## 2026-06-10 因子复刻收尾整改

本轮没有新增因子 ID，原因是第三章复刻边界已经完整覆盖七个因子；新增第5章的特质波动率异象或第6章的行为金融异象会污染第三章复刻范围。整改内容如下：

| 项目 | 处理 |
|---|---|
| 第三章因子范围复核 | 重新核对书籍 Markdown：第3章说明 `3.2` 到 `3.8` 依次为市场、规模、价值、动量、盈利、投资、换手率。 |
| 盈利 fallback | `engine/chapter3_factor_replication.py` 从 PIT 财报按 `symbol/available_date/report_period` 顺序衍生 `chapter3_book_equity_avg4q` 和 `chapter3_roe_ttm`；`engine/factor_calculators.py` 在缺少直接 `roe_ttm` 时优先使用该衍生列。 |
| 投资 fallback | `engine/chapter3_factor_replication.py` 从 PIT 年报总资产衍生 `chapter3_annual_asset_growth` 并按可用日向后填充；`engine/factor_calculators.py` 在缺少直接 `asset_growth` 时优先使用该衍生列。 |
| 通用因子定义 | `engine/factor_library.py` 的盈利和投资公式说明已更新为书中口径，避免长期研究误读为简化实现。 |
| 验证 | 新增 fixture 覆盖“无直接 `roe_ttm/asset_growth` 时按书中口径衍生”的路径。 |

## 已验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' UV_PROJECT_ENVIRONMENT=/tmp/local-backtest-qa-venv uv run --python 3.11 pytest -q tests/test_chapter3_factor_replication.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' UV_PROJECT_ENVIRONMENT=/tmp/local-backtest-qa-venv uv run --python 3.11 pytest -q tests/test_factor_library.py tests/test_factor_calculators.py tests/test_factor_statistics.py tests/test_chapter3_factor_replication.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' UV_PROJECT_ENVIRONMENT=/tmp/local-backtest-qa-venv uv run --python 3.11 pytest -q tests/test_factor_library.py tests/test_factor_calculators.py tests/test_factor_statistics.py tests/test_chapter3_factor_replication.py tests/test_cr030_factor_spec_run_spec_contract.py tests/test_cr030_factor_panel_label_window_gates.py tests/test_cr030_factor_evaluation_report.py tests/test_cr030_multifactor_combiner.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' UV_PROJECT_ENVIRONMENT=/tmp/local-backtest-qa-venv uv run --python 3.11 pytest -q tests/test_cr030_factor_spec_run_spec_contract.py tests/test_cr030_factor_panel_label_window_gates.py tests/test_cr030_factor_evaluation_report.py tests/test_cr030_multifactor_combiner.py
PYTHONPYCACHEPREFIX=/tmp/local-backtest-factor-boundary-pycompile uv run --python 3.11 python -m py_compile engine/factor_library.py engine/factor_calculators.py engine/factor_statistics.py engine/chapter3_factor_replication.py tests/test_factor_library.py tests/test_factor_calculators.py tests/test_factor_statistics.py tests/test_chapter3_factor_replication.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter3_factor_replication.py tests/test_factor_library.py tests/test_factor_calculators.py tests/test_factor_statistics.py tests/test_chapter3_empirical_runner.py
```

结果：

| 验证 | 结果 |
|---|---|
| 新增第三章复刻测试 | 10 passed |
| 通用因子库/计算/统计 + 第三章测试 | 21 passed |
| 通用模块 + 第三章 + CR030 合同回归 | 44 passed |
| CR030 合同/面板/评价/组合测试 | 23 passed |
| py_compile | passed |
| 2026-06-10 第三章因子复刻收尾回归 | 26 passed |

## 剩余需授权或真实数据接入事项

1. 本轮未读取 `.env`、未触发 provider fetch、lake write、catalog publish、QMT、simulation、live、账户或订单能力，因此没有证明真实数据 lake 中已存在完整后复权、trade_status、prices_limit、stock_basic 和财报 revision/as-of 字段。
2. `canonicalize_chapter3_financials` 已补离线 PIT 记录选择规则，但真实 Wind/Tushare 四类财报记录的全历史回填、质量审计和 catalog 发布需要单独授权。
3. 后复权优先级已冻结为 `back_adjusted_close/hfq_close`，但如果当前 lake 只有 `qfq/adjusted_close`，正式实证 runner 必须把该限制写入 run metadata，不能声明严格后复权复刻。
4. 本轮落地的是离线 runner 组件，不等于已经完成 2000-01-01 至 2019-12-31 A股全市场真实实证重跑。
5. 无风险利率和 CAPM 超额收益的真实利率曲线未接入；当前市场 beta 工程入口仍可在无风险利率缺失时用普通收益近似，正式报告需补利率数据或声明限制。
