# CR-032 第三章因子数据缺口整改

status: completed-offline
date: 2026-06-08
branch: work/chapter3-factor-gap-remediation-20260608
baseline_commit: a5e30f5

## 背景

用户要求按照《因子投资：方法与实践》第三章的数据和流程口径，整改当前项目第三章因子复刻的 P0 缺口，并完成本地工程化落地。

本 CR 只授权本地离线代码、测试和过程文档修改；不授权读取 `.env`、真实 provider fetch、lake write、catalog publish、QMT、simulation、live、账户、订单或外部交易能力。

## 影响范围

| 类型 | 对象 |
|---|---|
| 代码 | `engine/chapter3_factor_replication.py` |
| 测试 | `tests/test_chapter3_factor_replication.py` |
| 研究文档 | `process/research/chapter3_factor_replication/README.md` |
| 检查证据 | `process/checks/CP6-CR032-chapter3-factor-gap-remediation-CODING-DONE.md`、`process/checks/CP7-CR032-chapter3-factor-gap-remediation-VERIFICATION-DONE.md` |

## 整改内容

| 缺口 | 处理 |
|---|---|
| 财务 PIT canonical schema | 新增 `canonicalize_chapter3_financials`，按 `symbol/report_period/available_at` 和第三章四类财报记录语义做稳定优先级去重。真实 revision/as-of 全历史回填仍需另行授权。 |
| 后复权口径 | 新增 `Chapter3ResearchPolicy`，价格列默认优先 `back_adjusted_close/hfq_close`，并在 `prepare_chapter3_research_data` 中记录替代列限制。 |
| 长期停牌复牌异常收益压缩 | 新增 `build_chapter3_return_matrix`，对 1996-12-16 后日收益执行 +/-10% 压缩，并把停牌日收益置缺。 |
| 黑名单和交易约束 | 新增 `build_chapter3_universe_mask` 与 `build_chapter3_tradable_mask`，覆盖 ST/风险警示、退市、净资产为负、上市不足一年、科创板、停牌、一字涨停、一字跌停。 |
| Newey-West / Fama-MacBeth | 新增 `newey_west_t_stat`、双重排序多空摘要和 `fama_macbeth_regression`。 |
| 第三章 runner 口径冻结 | 新增月末调仓日、保留金融行业、排除科创板、等权/市值加权排序和条件双重排序入口。 |

## 不授权项

| 不授权项 | 状态 |
|---|---|
| 读取 `.env` 或任何凭据 | 未执行 |
| provider fetch / 外部数据下载 | 未执行 |
| lake write / catalog publish | 未执行 |
| QMT / simulation / live / 账户 / 订单 | 未执行 |
| 真实 2000-2019 A股全市场实证重跑 | 未执行 |

## 决策

本 CR 结论为 `completed-offline`：第三章数据问题和因子复刻已具备本地离线工程入口与测试覆盖；真实数据接入、财报全历史 PIT 回填和正式实证报告仍需后续运行授权。
