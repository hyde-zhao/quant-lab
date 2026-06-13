# 数据合同

**Run ID**: run-turnover-lowturnover-double-sort-20190101-20251231-v1

## 数据源

- market_cap: /mnt/ugreen-data-lake/canonical/market_cap/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529
- prices: /mnt/ugreen-data-lake/canonical/prices/1.0/run_id=run-cr018-release-full-history-20150101-20260528-20260529
- trade_calendar: /mnt/ugreen-data-lake/canonical/trade_calendar/1.0/run_id=run-cr014-s14-trade-calendar-2015-2026-232302/part-trade-calendar-20150101-20260528.parquet
- stock_basic: /mnt/ugreen-data-lake/canonical/stock_basic/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529/part-stock-basic-lifecycle.parquet

## 字段覆盖

- market_cap: trade_date, symbol, market_cap, turnover_rate ✅
- prices: trade_date, symbol, adjusted_close, adj_factor, adjustment_policy ✅
- trade_calendar: trade_date, is_open ✅
- stock_basic: symbol, list_date, list_status ✅

## 日期覆盖

- 预热期: 2018-01-02 ~ 2019-01-01
- 实验期: 2019-01-01 ~ 2025-12-31
- 有效实验结束日: end_date 往前推 20 个交易日

## 复权口径

- adjustment_policy: qfq (前复权)
- adj_factor 来源: tushare adj_factor 接口，available_at 为次日 08:00
- 声明: 本实验使用 ex-post 复权价格，不声明 PIT 无泄漏复权

## 交易日历

- 来源: trade_calendar canonical (run-cr014-s14)
- 若缺失则用 market_cap/prices 交集，并在审计中声明

## 缺失处理

- ST/涨跌停/停牌: 未使用 PIT 数据，作为正式限制声明
- 行业分类: 未使用
- 风格暴露: 未使用
