---
status: captured
created_at: "2026-05-13"
created_by: "meta-po"
request_type: "new_workflow_init"
engagement_mode: "production"
scenario_subject_type: "target-artifact"
scenario_subject_id: "local-daily-backtest-layer"
---

# 原始请求登记

## 用户目标

开发一个本地量化回测项目，先不选择大型量化框架，而是在项目内实现一个轻量、透明、可调试的“本地日频组合回测层”。第一阶段重点服务实践六动量策略的本地复现、参数扫描和报告输出，后续再扩展 RSI、MACD、样本外测试、市场环境分段和聚宽少量候选参数验证。

## 建议目录结构

```text
work/studies/quant-trading/local_backtest/
  data/
    prices.parquet
    index_members.parquet
    trade_calendar.parquet
  engine/
    data_loader.py
    metrics.py
    portfolio.py
    backtest.py
  strategies/
    momentum.py
    rsi.py
    macd.py
  notebooks/
    01_momentum_local_test.ipynb
  reports/
    momentum_param_sweep.csv
```

## 核心分层

- 信号层：根据历史价格计算买卖信号或目标权重。
- 组合层：根据目标权重、当前持仓、交易成本生成组合净值。
- 分析层：计算收益、回撤、Sharpe、Alpha、Beta、分段表现。

## 第一版本地回测器最小能力

1. 读取多股票日线收盘价。
2. 读取沪深 300 成分股池，第一版可简化为当前成分股。
3. 每 N 个交易日调仓。
4. 计算过去 `lookback_days` 收益率。
5. 选排名前 `top_fraction`。
6. 持仓跌出 `sell_buffer` 后卖出。
7. 目标持仓等权。
8. 扣除手续费和滑点。
9. 输出净值曲线、累计收益、年化收益、最大回撤、Sharpe。
10. 支持参数扫描。

## 第一版明确不处理

1. 涨跌停。
2. 停牌。
3. 成分股历史变化。
4. 分红送转。
5. 分钟级撮合。
6. 真实成交量约束。

## 数据路线

学习阶段采用 AKShare 拉取数据并保存为 parquet 本地缓存。第一次联网拉取后保存到本地；后续回测只读取本地 parquet，避免每次回测都联网取数。数据至少包括股票日线行情、沪深 300 指数行情、交易日历、指数成分股、复权因子、停牌信息和涨跌停价格；其中第一版本地回测只强依赖收盘价、固定沪深 300 股票池和交易日历。

## 框架路线

第一版不直接上 RQAlpha、Backtrader 或完整事件驱动框架。当前目标是快速验证动量、RSI、MACD 等策略参数，不是搭建完整交易系统。后续当策略稳定并需要订单、账户、撮合、风控、实盘模拟或多品种支持时，再考虑迁移到 RQAlpha 或聚宽。

## 策略核心共用要求

动量策略应抽出可复用的纯函数，供本地回测器和聚宽策略复用或复制同一逻辑，避免本地和平台代码出现两套不同策略逻辑。用户给出的核心函数示意：

```python
def compute_momentum_returns(close_df, lookback_days):
    return close_df.iloc[-1] / close_df.iloc[-lookback_days - 1] - 1


def select_momentum_targets(
    momentum,
    current_positions,
    top_fraction=0.10,
    sell_buffer=0.30,
):
    ranked = momentum.dropna().sort_values(ascending=False)
    buy_count = max(1, int(len(ranked) * top_fraction))
    buy_set = set(ranked.head(buy_count).index)

    sell_threshold = max(buy_count, int(len(ranked) * sell_buffer))
    keep_set = set(ranked.head(sell_threshold).index)

    target = buy_set | (set(current_positions) & keep_set)
    return sorted(target)
```

## 推荐路线图

1. 做一个最小本地动量回测器：读取本地 parquet、每 20 个交易日调仓、计算过去 20 日收益率、买入前 10%、跌出前 30% 卖出、等权、输出净值曲线和指标。
2. 补齐参数扫描和报告：扫描 `lookbacks = [5, 10, 20, 30, 60]`、`freqs = [5, 10, 20, 30]`、`fractions = [0.05, 0.10, 0.20]` 共 60 组参数，输出 `momentum_param_sweep_local.csv`，并补充热力图、收益排名、Sharpe 排名、最大回撤排名、样本内/样本外衰减。
3. 将本地最优参数回填聚宽验证：只跑默认参数、本地 Sharpe 最优、本地收益最优、保守低换手参数，避免在聚宽上跑完整 60 组扫描。

## 第一版验收线索

1. 能跑完整 2019-2025。
2. 能输出累计收益、年化收益、最大回撤、Sharpe。
3. 能跑 60 组参数扫描。
4. 参数扫描耗时明显低于聚宽。

## 外部依据待核验项

- AKShare 适合作为学习阶段免费数据接口，但其数据声明为学术研究与参考用途，接口可能受不可控因素影响。
- RQAlpha 更适合事件驱动、订单、账户、撮合、风控、分析和更接近真实交易的后续阶段。
- vectorbt 可在参数扫描规模变大后用于指标与持仓向量化。
- bt 可在资产配置、ETF 轮动、多资产组合和定期再平衡场景中作为后续候选。

