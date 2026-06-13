# 泄漏审计

**Run ID**: run-turnover-lowturnover-double-sort-20190101-20251231-v1

## 前视收益标签

```
forward_return_20d = adjusted_close[t+20] / adjusted_close[t] - 1
```

- decision_time: 调仓日收盘时刻
- label_window_start: 调仓日次日 (t+1)
- label_window_end: 调仓日后 20 个交易日 (t+20)
- label_available_at: 调仓日后 20 个交易日收盘后

## 防前视措施

1. 最后 20 个交易日从有效样本中剔除（forward_return 为 NaN）
2. 有效实验结束日 = end_date 往前推 20 个交易日
3. 因子计算仅使用调仓日当日及之前数据

## 复权泄漏风险

- 使用 adjusted_close (qfq) 计算收益
- adj_factor 的 available_at 为次日 08:00
- 若在调仓日当天使用 adj_factor，存在 ≤1 日的轻微前视
- 本实验不声明 PIT 无泄漏复权

## 结论

- forward return 标签无前视泄漏 ✅
- 因子计算无前视泄漏 ✅
- 复权存在 ex-post 偏差（已声明）⚠️
