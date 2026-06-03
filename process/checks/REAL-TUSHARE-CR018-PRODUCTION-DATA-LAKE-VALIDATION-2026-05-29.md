---
check_id: "REAL-TUSHARE-CR018-PRODUCTION-DATA-LAKE-VALIDATION-2026-05-29"
type: "real_lake_production_readiness_validation"
status: "FAIL_PRODUCTION_CURRENT_TRUTH_NOT_REACHED__PASS_FULL_HISTORY_PRICES_ADJ_FACTOR_CANDIDATE"
owner: "meta-po"
created_at: "2026-05-29T11:47:00+08:00"
checked_at: "2026-05-29T11:47:00+08:00"
change_id: "CR-018"
lake_root: "<configured-env-lake-root>"
credential_policy: "read .env for runtime token only; token value not printed or persisted"
date_range_checked: "2015-01-05..2026-05-28"
publish_current_pointer: false
---

# REAL Tushare CR018 Production Data Lake Validation

## 结论

当前真实数据湖 **尚未达到 production current truth**。

已经达到的是：2015-01-05 至 2026-05-28 的全 A `prices` / `adj_factor` **candidate 数据可用性通过**，逐日 parquet、复权因子配对、重复键和 Tushare 抽样源数据比对均通过。

未达到的是：CR018 定义的 production current truth。当前 catalog / current reader / production readiness 明确显示 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`stock_basic` 仍未发布，`prices` 仍为 `quality_status=warn` 且 `pit_status=non_pit_disclosed`。因此不能将已拉取的 2015 至今候选数据声明为生产级事实源。

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 用户授权读取 `.env` token 做验证 | PASS | 当前会话用户原文 | 只用于 `uv run --env-file .env` 运行时加载，不输出、不落盘 token。 |
| lake root 可访问 | PASS | `/mnt/ugreen-data-lake` 存在 | 输出中不记录真实凭据；本报告仅使用 `<configured-env-lake-root>` 表示配置湖。 |
| Tushare token 可用 | PASS | `trade_cal` 小调用成功 | 返回 29 行交易日历；证明 token / 网络 / Tushare API 初始化可用。 |
| 不执行 publish | PASS | 本轮命令 | 未调用 `publish`，未更新 current pointer。 |
| 不执行 QMT | PASS | 本轮命令 | 未启动 QMT、未查询账户、未下单、未撤单。 |

## Full History Prices / Adj Factor Candidate Audit

| 指标 | 结果 |
|---|---:|
| 覆盖日期 | 2015-01-05..2026-05-28 |
| run 数 | 12 |
| `prices` parquet 文件数 | 2768 |
| `adj_factor` parquet 文件数 | 2768 |
| `prices` 行数 | 11,311,360 |
| `adj_factor` 行数 | 11,823,057 |
| `prices` 交易对缺失 `adj_factor` | 0 |
| `adj_factor` 额外交易对 | 511,697 |
| `prices` 重复 date+symbol | 0 |
| `adj_factor` 重复 date+symbol | 0 |
| 复权 policy | `qfq` |
| 本地逐日审计 issue 数 | 0 |

### Yearly Summary

| 年份 / run_id | 日期范围 | prices rows | adj rows | prices files | adj files | missing adj pairs | extra adj pairs |
|---|---|---:|---:|---:|---:|---:|---:|
| `run-cr014-s14-prices-adj-factor-2015-232405` | 2015-01-05..2015-12-31 | 575,184 | 675,358 | 244 | 244 | 0 | 100,174 |
| `run-cr014-s14-prices-adj-factor-2016-233430` | 2016-01-04..2016-12-30 | 652,864 | 729,185 | 244 | 244 | 0 | 76,321 |
| `run-cr014-s14-prices-adj-factor-2017-233927` | 2017-01-03..2017-12-29 | 754,372 | 834,943 | 244 | 244 | 0 | 80,571 |
| `run-cr014-s14-prices-adj-factor-2018-234359` | 2018-01-02..2018-12-28 | 824,535 | 899,558 | 243 | 243 | 0 | 75,023 |
| `run-cr014-s14-prices-adj-factor-2019-234833` | 2019-01-02..2019-12-31 | 894,177 | 936,704 | 244 | 244 | 0 | 42,527 |
| `run-cr014-s14-prices-adj-factor-2020-235353` | 2020-01-02..2020-12-31 | 964,131 | 1,003,301 | 243 | 243 | 0 | 39,170 |
| `run-cr014-s14-prices-adj-factor-2021-235843` | 2021-01-04..2021-12-31 | 1,085,445 | 1,119,157 | 243 | 243 | 0 | 33,712 |
| `run-cr014-s14-prices-adj-factor-2022-000336` | 2022-01-04..2022-12-30 | 1,179,072 | 1,208,822 | 242 | 242 | 0 | 29,750 |
| `run-cr014-s14-prices-adj-factor-2023-000913` | 2023-01-03..2023-12-29 | 1,258,734 | 1,274,480 | 242 | 242 | 0 | 15,746 |
| `run-cr014-s14-prices-adj-factor-2024-001432` | 2024-01-02..2024-12-31 | 1,293,893 | 1,303,184 | 242 | 242 | 0 | 9,291 |
| `run-cr014-s14-prices-adj-factor-2025-001949` | 2025-01-02..2025-12-31 | 1,313,898 | 1,321,761 | 243 | 243 | 0 | 7,863 |
| `run-cr014-s11-full-a-2026-ytd-date-batch-143508` | 2026-01-05..2026-05-28 | 515,055 | 516,604 | 94 | 94 | 0 | 1,549 |

## Tushare Source Spot Check

| 日期 | 本地 prices rows | Tushare daily rows | 本地 adj rows | Tushare adj rows | 样本价格 / 复权因子 |
|---|---:|---:|---:|---:|---|
| 2015-01-05 | 2,347 | 2,347 | 2,611 | 2,611 | `000001.SZ`、`600000.SH` close 与 adj_factor 均匹配 |
| 2026-05-28 | 5,506 | 5,506 | 5,524 | 5,524 | `000001.SZ`、`600000.SH` close 与 adj_factor 均匹配 |

## Catalog / Current Truth Gate

| 检查项 | 结果 | 说明 |
|---|---|---|
| production readiness | FAIL | `status=fail` |
| blocked claims | `adjustment_consistent_research`, `production_current_truth`, `quality_pass_research`, `real_benchmark_research` | 严肃研究声明仍被阻断。 |
| `prices` catalog | `published=false`, `quality_status=warn`, `pit_status=non_pit_disclosed`, `run_id=run-cr014-s11-full-a-2026-ytd-date-batch-143508` | 只指向 2026 YTD candidate，不是 2015 至今 production current truth。 |
| `adj_factor` catalog | `published=false`, `quality_status=pass`, `run_id=run-cr014-s11-full-a-2026-ytd-date-batch-143508` | 未发布 current truth。 |
| `hs300_index` catalog | `published=false`, `quality_status=pass`, 2026 YTD | 未发布；且只覆盖 HS300，不覆盖 CR018 四类 benchmark。 |
| `trade_calendar` catalog | `published=false`, 2026 YTD | 本地存在 2015..2026 calendar candidate，但 current catalog 仍指向未发布 2026 YTD。 |
| `stock_basic` catalog | `published=false`, 2026 YTD | 不能替代完整 PIT universe / 退市历史闭环。 |
| `prices` current reader | FAIL | `dataset=prices 不可读: required_missing; issues=catalog_not_published` |
| `adj_factor` current reader | FAIL | `dataset=adj_factor 不可读: required_missing; issues=catalog_not_published` |
| `published/` root | 不存在 | 当前未形成 CR018 release-level published current truth 根。 |

## P0 Production Gaps

| 缺口 | 当前状态 | 对 production 影响 |
|---|---|---|
| release-level Explicit Publish Gate | 未执行 | candidate 不能成为 current truth。 |
| PIT universe / lifecycle / code-change 全周期闭环 | 未关闭 | 仍有幸存者偏差和历史股票池污染风险。 |
| 2015 至今完整 ST / suspend / trade_status | 未关闭 | 当前只有 limited window / targeted 2026 缺口归因，不能证明全周期可交易性。 |
| 2015 至今完整 prices_limit | 未关闭 | 涨跌停买卖约束不能覆盖全周期。 |
| 四类真实 benchmark：沪深300、中证500、中证1000、中证全指 | 未关闭 | 不能严肃声明真实超额收益、指数增强或风格暴露。 |
| 指数历史成分与权重全周期 | 未关闭 | 不能避免历史回测使用未来成分，也不能做真实 tracking error / active weight。 |
| qfq / hfq / returns_adjusted publish view | 未发布 | 已有 qfq candidate 字段，但双视图派生和 publish readiness 未落到真实 release。 |
| P1 行业、市值、风格、流动性、容量 | 未关闭 | 不能声明行业/市值中性、独立 alpha、容量或 scale-up。 |

## Exit Criteria

| 条目 | 状态 | 说明 |
|---|---|---|
| 2015 至今 `prices` / `adj_factor` candidate 可用 | PASS | 全周期本地逐日审计和 Tushare 抽样比对通过。 |
| 2015 至今 production current truth | FAIL | 未 publish，current reader 阻断，P0 数据集缺口未关闭。 |
| 可进入 candidate research rerun | PASS_WITH_BOUNDARY | 可以基于候选数据做研究重跑，但报告必须标注 candidate / non-PIT / not current truth。 |
| 可进入 QMT simulation admission | FAIL | CR018-S09 仍 later-gated；production current truth 未达标前不得进入。 |

## 后续建议

1. 先不要 publish 当前 `prices` / `adj_factor` 为 production current truth。
2. 补全 2015 至今 P0：PIT universe、退市 / 改名、ST / suspend / trade_status、prices_limit、四类 benchmark 行情 / 成分 / 权重。
3. 基于补齐后的 P0 生成 release-level quality / readiness report。
4. 通过 Explicit Publish Gate 发布 release current pointer。
5. 用 published current truth 重跑阶段三到阶段五研究；PASS 后再讨论 QMT simulation admission。
