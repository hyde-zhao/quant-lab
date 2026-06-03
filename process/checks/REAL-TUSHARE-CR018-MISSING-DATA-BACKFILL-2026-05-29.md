# REAL Tushare CR018 Missing Data Backfill — 2026-05-29

## 结论

本轮已执行真实 Tushare 读取和真实 lake candidate 写入，范围为 `2015-01-01..2026-05-28`，QMT 操作为 `0`，current pointer publish 为 `0`。

数据补齐状态：`PARTIAL_PASS_WITH_PROVIDER_GAPS`。

- 已补齐并通过本地 key / coverage 校验的数据：价格 `volume/amount`、`stock_basic` 生命周期、四类真实 benchmark 行情 / 成分 / 权重、`trade_status`、ST 事件、`daily_basic` 市值 / 换手、`liquidity_capacity` ADV20。
- 未被合法补齐的数据：`prices_limit` 对价格观测分母仍缺 `92,147` 个 pair，主要是早期 `BJ` 股票；Tushare `stk_limit` 按日期和按 symbol 均不返回这些历史涨跌停价。未用推导价格冒充官方涨跌停事实。
- 当前仍未进入 production current truth：所有新补数据均为 candidate，未更新 published/current pointer。

## 执行边界

| 项目 | 结果 |
|---|---:|
| lake root | `/mnt/ugreen-data-lake` |
| run_id | `run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529` |
| 价格刷新 run_id | `run-cr018-missing-data-backfill-20150101-20260528-prices-refresh-20260529` |
| provider | Tushare |
| 真实 provider calls | `9,222` |
| QMT operation count | `0` |
| current pointer publish count | `0` |
| 凭据输出 | `0`，未在报告中写入 token |

## 已写入数据

| dataset | rows | parts | duplicate keys | 覆盖 / 说明 |
|---|---:|---:|---:|---|
| `prices` | `11,311,360` | existing full-history parts | `0` | 已从已有 raw 重新标准化，`volume_nulls=0`，`amount_nulls=0` |
| `adj_factor` | `11,823,057` | existing full-history parts | `0` | 对 `prices` price pairs 的缺失为 `0` |
| `stock_basic` | `5,850` | `1` | `0` | `L=5,525`、`D=325`；用于 lifecycle，不单独证明 PIT universe |
| `industry_classification` | `5,524` | `1` | `0` | 来自 Tushare `stock_basic.industry` 当前快照，不是 SW 历史 PIT 行业 |
| `hs300_index` | `11,072` | `1` | `0` | 覆盖 `399300.SZ`、`000905.SH`、`000852.SH`、`000985.SH`；每个指数缺 open date 为 `0` |
| `index_weights` | `276,600` | `1` | `0` | 四类 benchmark 权重有效日数据 |
| `index_members` | `276,600` | `1` | `0` | 由 index weights 有效日派生成分事件；不是每日展开快照 |
| `prices_limit` | `13,648,694` | `12` | `0` | 对全 price pairs 仍缺 `92,147`，见下方 blocker |
| `trade_status` | `11,311,360` | `12` | `0` | 覆盖 price pairs 缺失为 `0` |
| `events` | `323,698` | `1` | `0` | ST 状态事件 |
| `market_cap` | `11,220,665` | `12` | `0` | 对 price pairs 缺 `90,695`；P1，不阻断 P0 current truth，但阻断市值中性 / pure alpha 声明 |
| `liquidity_capacity` | `11,311,360` | `12` | `0` | 覆盖 price pairs 缺失为 `0`；`turnover_rate_nulls=90,695`，`adv20_amount_nulls=23,068` |

机器校验文件：

- `/mnt/ugreen-data-lake/quality/run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529/cr018_cross_dataset_validation.json`
- `/mnt/ugreen-data-lake/quality/run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529/cr018_missing_data_backfill_summary.json`
- `/mnt/ugreen-data-lake/quality/run-cr018-missing-data-backfill-20150101-20260528-prices-refresh-20260529/cr018_missing_data_backfill_summary.json`

## prices_limit 剩余缺口

`prices_limit` 缺失对 price pairs 的分布：

| 年份 | 缺失 pairs | 主因 |
|---|---:|---|
| 2015 | `5,118` | `BJ=4,874`，`SZ=244` |
| 2016 | `10,830` | `BJ=10,655`，`SZ=175` |
| 2017 | `10,675` | `BJ=10,431`，`SZ=244` |
| 2018 | `7,197` | `BJ=6,952`，`SZ=245` |
| 2019 | `9,067` | `BJ=8,845`，`SZ=221`，`SH=1` |
| 2020 | `17,926` | `BJ=17,926` |
| 2021 | `23,542` | `BJ=23,542` |
| 2022 | `7,792` | `BJ=7,792` |
| 2023-2026 | `0` | 无缺口 |
| 合计 | `92,147` | `BJ=91,017`，`SZ=1,129`，`SH=1` |

补抓验证：

- `pro.stk_limit(trade_date=...)` 已按全部 open trade dates 抓取。
- 对样本 `920175.BJ` 使用 `pro.stk_limit(ts_code='920175.BJ', start_date='20150101', end_date='20221231')` 返回 `0` 行。
- 对样本 `001914.SZ` 使用 symbol 方式仅返回 2019 年后少量行，早期历史 price pairs 仍无法由 `stk_limit` 补齐；这更像 code-change / provider 历史映射缺口。

处理原则：

- 未使用 `pre_close * 涨跌幅比例` 生成伪官方涨跌停价。
- 未将缺失 `prices_limit` 标记为 production pass。
- 若需要关闭该 blocker，需要单独决策：排除 BJ/未解析 code-change 历史、引入第二数据源、或批准“规则推导涨跌停价”并在数据中显式标记 derived。

## readiness 结果

执行：

```bash
uv run --python 3.11 -m market_data.cli report-readiness --lake-root /mnt/ugreen-data-lake --realism-mode production_strict
```

结果：`status=fail`。

主要原因：

- 新补数据仍是 candidate，`published=false`，未更新 current pointer。
- `prices` / `adj_factor` / `trade_calendar` 的 catalog 仍指向旧的 2026 YTD 或未发布入口，尚未形成 full-history release pointer。
- `prices_limit` 对全 price pairs 有 provider coverage gap。
- `industry_classification` 是当前快照，不是历史 PIT SW 行业；只可作为 P1 辅助输入，不能支持行业中性 / pure alpha production claim。

## 已执行验证命令

```bash
uv run --python 3.11 python -m py_compile scripts/cr018_real_backfill_missing_data.py
uv run --python 3.11 pytest -q tests/test_market_data_tushare_datasets.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py
uv run --python 3.11 -m market_data.cli report-readiness --lake-root /mnt/ugreen-data-lake --realism-mode production_strict
```

结果：

- `py_compile`: PASS
- pytest targeted: `31 passed`
- production readiness: FAIL，原因见上方

## 下一步建议

1. 不发布 current pointer，先关闭 `prices_limit` 剩余缺口的决策。
2. 推荐方案 A：生产研究 universe 暂定为沪深 A 股，排除早期 BJ price-limit 缺失分母；对 `001914.SZ` 等 code-change 历史缺口进入 code-change mapping 子任务。
3. 备选方案 B：引入第二数据源补 BJ / code-change 历史涨跌停价，再重跑 `prices_limit` coverage。
4. 备选方案 C：批准规则推导涨跌停价，但所有 derived rows 必须带 `source_interface=derived_price_limit_rule` 和 `readiness_status=derived_not_official`，不得声明官方 production pass。
