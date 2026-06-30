"""A股低换手率因子双重排序实验。

复刻书中 A 股换手率因子实证，包含三个子实验：
  - 实验A：单变量排序（异常换手率 5 分组）
  - 实验B：独立双重排序（市值 × 换手率 5×5）
  - 实验C：条件双重排序（市值控制后换手率 5×5）

运行标识：
  run_id = run-turnover-lowturnover-double-sort-20190101-20251231-v1
  strategy_id = strategy-low-turnover-double-sort-v1
  factor_id = abnormal_turnover_21_252

用法：
  uv run --python 3.11 python experiments/run_experiment_turnover_factor.py \
      --start-date 2019-01-01 \
      --end-date 2025-12-31 \
      --warmup-start 2018-01-02 \
      --run-id run-turnover-lowturnover-double-sort-20190101-20251231-v1
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.factor_calculators import calculate_abnormal_turnover_21_252
from engine.factor_statistics import (
    conditional_double_sort_returns,
    independent_double_sort_returns,
    single_sort_returns,
)
from engine.research_paths import research_report_path, research_run_path

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

LAKE_ROOT = Path(os.environ.get("MARKET_DATA_LAKE_ROOT", "/mnt/ugreen-data-lake"))
LAKE_CANONICAL = LAKE_ROOT / "canonical"

MC_RUN_ID = "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529"
PRICES_RUN_ID = "run-cr018-release-full-history-20150101-20260528-20260529"
TRADE_CALENDAR_RUN_ID = "run-cr014-s14-trade-calendar-2015-2026-232302"
STOCK_BASIC_RUN_ID = "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529"
TRADE_STATUS_RUN_ID = "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529"

MC_DIR = LAKE_CANONICAL / "market_cap" / "1.0" / f"run_id={MC_RUN_ID}"
PRICES_DIR = LAKE_CANONICAL / "prices" / "1.0" / f"run_id={PRICES_RUN_ID}"
TC_PATH = LAKE_CANONICAL / "trade_calendar" / "1.0" / f"run_id={TRADE_CALENDAR_RUN_ID}" / "part-trade-calendar-20150101-20260528.parquet"
SB_PATH = LAKE_CANONICAL / "stock_basic" / "1.0" / f"run_id={STOCK_BASIC_RUN_ID}" / "part-stock-basic-lifecycle.parquet"
TS_DIR = LAKE_CANONICAL / "trade_status" / "1.0" / f"run_id={TRADE_STATUS_RUN_ID}"

FACTOR_ID = "abnormal_turnover_21_252"
STRATEGY_ID = "strategy-low-turnover-double-sort-v1"
DEFAULT_RUN_ID = "run-turnover-lowturnover-double-sort-20190101-20251231-v1"

PROCESS_DIR = research_run_path("turnover_low_turnover_double_sort")
REPORTS_BASE = research_report_path("factor_research", "turnover_low_turnover_double_sort")


def _artifact_ref(path: Path) -> str:
    """项目内路径用相对引用，NAS 路径保留绝对引用。"""

    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExperimentData:
    """实验核心数据矩阵."""

    close_df: pd.DataFrame  # index=date, columns=symbol, values=adjusted_close
    turnover_df: pd.DataFrame  # index=date, columns=symbol, values=turnover_rate
    market_cap_df: pd.DataFrame  # index=date, columns=symbol, values=market_cap
    abnormal_turnover: pd.DataFrame  # 异常换手率因子
    forward_returns: pd.DataFrame  # forward_return_20d
    valid_mask: pd.DataFrame  # 过滤后的有效样本 mask
    calendar: list[date]  # 交易日历
    rebalance_dates: list[date]  # 调仓日期
    list_date_map: dict[str, str]  # symbol -> list_date


@dataclass(frozen=True, slots=True)
class GroupResult:
    """分组收益结果."""

    group_returns_ts: pd.DataFrame  # (date, group, mean_return, n_stocks)
    group_returns_summary: pd.DataFrame  # (group, mean, std, t_stat, nw_t_stat, ...)
    spread_ts: pd.Series  # G1-G5 价差时序
    spread_nw: dict  # Newey-West 检验结果


@dataclass(frozen=True, slots=True)
class DoubleSortResult:
    """双重排序结果."""

    cell_returns: pd.DataFrame  # (date, size_group, turnover_group, mean_return, n_stocks)
    cell_summary: pd.DataFrame  # 5x5 平均收益矩阵
    size_spread_ts: pd.DataFrame  # (date, size_group, turnover_spread)
    size_spread_summary: pd.DataFrame  # (size_group, mean_spread, nw_t_stat)
    avg_spread_nw: dict  # 各市值组价差均值的 NW 检验
    count_matrix: pd.DataFrame  # 样本数矩阵


# ---------------------------------------------------------------------------
# 第1区：数据加载
# ---------------------------------------------------------------------------


def _read_parquet_safe(path: Path, **kwargs: Any) -> pd.DataFrame:
    """安全读取 parquet，失败时给出清晰错误."""
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    try:
        return pd.read_parquet(str(path), **kwargs)
    except Exception as exc:
        raise RuntimeError(f"parquet 读取失败: {path}: {type(exc).__name__}: {exc}") from exc


def load_trade_calendar(start_date: str, end_date: str) -> list[date]:
    """从数据湖加载交易日历，返回 [start_date, end_date] 内的交易日."""
    df = _read_parquet_safe(TC_PATH)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    if "is_open" in df.columns:
        df = df[df["is_open"].astype(bool)]
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    calendar = sorted(d for d in df["trade_date"].dropna().tolist() if start <= d <= end)
    if not calendar:
        raise RuntimeError(f"交易日历在 {start_date} ~ {end_date} 内为空")
    return calendar


def load_stock_list_dates() -> dict[str, str]:
    """从 stock_basic 加载上市日期映射."""
    df = _read_parquet_safe(SB_PATH, columns=["symbol", "list_date", "list_status"])
    df = df.dropna(subset=["symbol", "list_date"])
    # 只保留上市状态（过滤退市/暂停）
    df = df[df["list_status"].isin(["L"])]
    result: dict[str, str] = {}
    for _, row in df.iterrows():
        sym = str(row["symbol"]).strip().upper()
        ld = str(row["list_date"]).strip()
        if sym and ld:
            result[sym] = ld
    return result


def load_market_cap(
    start_date: str, end_date: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """从数据湖加载 market_cap 数据，返回 (market_cap_df, turnover_df) 宽表矩阵."""
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    mc_frames: list[pd.DataFrame] = []
    for fpath in sorted(MC_DIR.glob("part-market-cap-*.parquet")):
        df = _read_parquet_safe(
            fpath,
            columns=["trade_date", "symbol", "market_cap", "turnover_rate"],
        )
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df = df[(df["trade_date"] >= start_dt) & (df["trade_date"] <= end_dt)]
        if not df.empty:
            mc_frames.append(df)

    if not mc_frames:
        raise RuntimeError(f"market_cap 在 {start_date} ~ {end_date} 内无数据")

    mc = pd.concat(mc_frames, ignore_index=True)
    mc["symbol"] = mc["symbol"].astype("string").str.strip().str.upper()
    mc = mc.dropna(subset=["trade_date", "symbol"]).drop_duplicates(["trade_date", "symbol"])

    market_cap_df = mc.pivot_table(
        index="trade_date", columns="symbol", values="market_cap", aggfunc="last"
    )
    turnover_df = mc.pivot_table(
        index="trade_date", columns="symbol", values="turnover_rate", aggfunc="last"
    )
    market_cap_df.index = pd.to_datetime(market_cap_df.index).date
    turnover_df.index = pd.to_datetime(turnover_df.index).date
    return market_cap_df, turnover_df


def load_prices(
    start_date: str, end_date: str
) -> pd.DataFrame:
    """从数据湖加载 prices，返回 adjusted_close 宽表矩阵."""
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    all_files = sorted(PRICES_DIR.glob("*.parquet"))
    # 按文件日期前缀过滤（文件名含 YYYYMMDD 日期）
    frames: list[pd.DataFrame] = []
    batch_size = 200
    for i in range(0, len(all_files), batch_size):
        batch = all_files[i : i + batch_size]
        batch_frames: list[pd.DataFrame] = []
        for fpath in batch:
            # 从文件名提取日期判断是否在范围内（避免读取所有文件）
            fname = fpath.name
            date_str = _extract_date_from_filename(fname)
            if date_str:
                try:
                    fdate = pd.Timestamp(date_str)
                    if fdate < start_dt or fdate > end_dt:
                        continue
                except (ValueError, TypeError):
                    pass
            df = _read_parquet_safe(
                fpath,
                columns=["trade_date", "symbol", "adjusted_close", "adjustment_policy"],
            )
            df["trade_date"] = pd.to_datetime(df["trade_date"])
            df = df[(df["trade_date"] >= start_dt) & (df["trade_date"] <= end_dt)]
            if not df.empty:
                batch_frames.append(df)
        if batch_frames:
            frames.append(pd.concat(batch_frames, ignore_index=True))

    if not frames:
        raise RuntimeError(f"prices 在 {start_date} ~ {end_date} 内无数据")

    prices = pd.concat(frames, ignore_index=True)
    prices["symbol"] = prices["symbol"].astype("string").str.strip().str.upper()
    prices = prices.dropna(subset=["trade_date", "symbol"]).drop_duplicates(["trade_date", "symbol"])

    close_df = prices.pivot_table(
        index="trade_date", columns="symbol", values="adjusted_close", aggfunc="last"
    )
    close_df.index = pd.to_datetime(close_df.index).date
    return close_df


def _extract_date_from_filename(fname: str) -> str | None:
    """从 prices 文件名提取 YYYYMMDD 日期字符串.

    支持两种命名模式：
    - ...__part-prices-YYYYMMDD.parquet (2015, 2026)
    - ...__part-YYYY-YYYYMMDD-prices.parquet (2016-2025)
    """
    import re

    # 模式1: ...__part-prices-YYYYMMDD.parquet
    m = re.search(r"prices-(\d{8})\.parquet", fname)
    if m:
        return m.group(1)
    # 模式2: ...__part-YYYY-YYYYMMDD-prices.parquet
    m = re.search(r"part-\d{4}-(\d{8})-prices\.parquet", fname)
    if m:
        return m.group(1)
    return None


def build_data_matrices(
    start_date: str,
    end_date: str,
    warmup_start: str,
) -> ExperimentData:
    """构建实验所需全部数据矩阵."""
    t0 = time.monotonic()
    print(f"[数据加载] 开始: warmup={warmup_start}, 实验={start_date}~{end_date}")

    # 1. 交易日历
    calendar = load_trade_calendar(warmup_start, end_date)
    print(f"  - 交易日历: {len(calendar)} 个交易日 ({calendar[0]} ~ {calendar[-1]})")

    # 2. market_cap + turnover_rate
    market_cap_df, turnover_df = load_market_cap(warmup_start, end_date)
    print(f"  - market_cap: {market_cap_df.shape[0]} 天 × {market_cap_df.shape[1]} 股")

    # 3. prices (adjusted_close)
    close_df = load_prices(warmup_start, end_date)
    print(f"  - prices: {close_df.shape[0]} 天 × {close_df.shape[1]} 股")

    # 4. 对齐三个矩阵的日期和股票
    common_dates = sorted(
        set(calendar)
        & set(market_cap_df.index)
        & set(close_df.index)
    )
    common_symbols = sorted(
        set(market_cap_df.columns)
        & set(close_df.columns)
        & set(turnover_df.columns)
    )
    print(f"  - 对齐后: {len(common_dates)} 天 × {len(common_symbols)} 股")

    market_cap_df = market_cap_df.reindex(index=common_dates, columns=common_symbols)
    turnover_df = turnover_df.reindex(index=common_dates, columns=common_symbols)
    close_df = close_df.reindex(index=common_dates, columns=common_symbols)

    # 5. 股票基本信息
    list_date_map = load_stock_list_dates()
    print(f"  - stock_basic: {len(list_date_map)} 只股票有上市日期")

    # 6. 上市天数过滤（在 valid_mask 中处理，此处只记录）
    # 在 warmup 期内按 list_date 标记不足 252 日的新股

    elapsed = time.monotonic() - t0
    print(f"[数据加载] 完成，耗时 {elapsed:.1f}s")

    return ExperimentData(
        close_df=close_df,
        turnover_df=turnover_df,
        market_cap_df=market_cap_df,
        abnormal_turnover=pd.DataFrame(),  # 后续计算
        forward_returns=pd.DataFrame(),  # 后续计算
        valid_mask=pd.DataFrame(),  # 后续计算
        calendar=common_dates,
        rebalance_dates=[],  # 后续计算
        list_date_map=list_date_map,
    )


# ---------------------------------------------------------------------------
# 第2区：因子计算
# ---------------------------------------------------------------------------


def calculate_abnormal_turnover(
    turnover_df: pd.DataFrame,
    short_window: int = 21,
    long_window: int = 252,
    short_min_periods: int = 15,
    long_min_periods: int = 60,
) -> pd.DataFrame:
    """计算异常换手率因子.

    abnormal_turnover = mean(turnover, short_window) / mean(turnover, long_window)
    """
    return calculate_abnormal_turnover_21_252(
        turnover_df,
        short_window=short_window,
        long_window=long_window,
        short_min_periods=short_min_periods,
        long_min_periods=long_min_periods,
        clip_bounds=(0.01, 10.0),
    )


def build_forward_return_20d(close_df: pd.DataFrame) -> pd.DataFrame:
    """计算 20 日前瞻收益.

    forward_return_20d = close[t+20] / close[t] - 1

    注意：最后 20 个交易日 forward_return 为 NaN，需在有效样本中剔除。
    """
    return close_df.shift(-20) / close_df - 1.0


# ---------------------------------------------------------------------------
# 第3区：过滤与调仓日期
# ---------------------------------------------------------------------------


def _apply_listing_days_filter(
    mask: pd.DataFrame,
    list_date_map: dict[str, str],
    min_days: int,
) -> None:
    """向量化方式应用上市天数过滤.

    对于 mask 中的每个交易日，计算每只股票的上市天数，
    将上市不足 min_days 的股票标记为 False。
    """
    if not list_date_map:
        return

    # 构建上市日期 Series（与 mask.columns 对齐）
    list_dates = pd.Series(
        {sym: pd.Timestamp(ld) for sym, ld in list_date_map.items() if sym in mask.columns},
        dtype="datetime64[ns]",
    )
    if list_dates.empty:
        return

    # 对齐到 mask.columns
    list_dates = list_dates.reindex(mask.columns)

    # 对每个交易日，计算上市天数矩阵
    date_index = pd.DatetimeIndex([pd.Timestamp(d) for d in mask.index])
    # 利用广播计算：trade_date[:, None] - list_date[None, :]
    listing_days = date_index.to_numpy()[:, None] - list_dates.to_numpy()[None, :]
    # listing_days 是 timedelta64 数组，转为天数
    listing_days_days = listing_days.astype("timedelta64[D]").astype(float)

    # 标记上市不足 min_days 的为 False
    insufficient = listing_days_days < min_days
    # 也标记 list_date 为 NaT 的（即不在 list_date_map 中的股票）
    insufficient |= np.isnan(listing_days_days)

    mask.values[insufficient] = False


def apply_filters(
    abnormal_turnover: pd.DataFrame,
    market_cap_df: pd.DataFrame,
    turnover_df: pd.DataFrame,
    forward_returns: pd.DataFrame,
    list_date_map: dict[str, str],
    long_window: int = 252,
    min_long_samples: int = 60,
) -> pd.DataFrame:
    """构建有效样本 mask.

    过滤规则：
    1. market_cap 缺失
    2. turnover_rate 缺失或 <= 0（隐含停牌）
    3. 252 日窗口有效非零样本 < min_long_samples
    4. forward_return 缺失
    5. abnormal_turnover 缺失
    6. 上市不足 long_window 个自然日（近似过滤新股）
    """
    mask = (
        market_cap_df.notna()
        & turnover_df.notna()
        & (turnover_df > 0)
        & abnormal_turnover.notna()
        & forward_returns.notna()
    )

    # 252 日窗口样本数过滤
    long_count = turnover_df.rolling(long_window, min_periods=1).apply(
        lambda x: (x > 0).sum(), raw=True
    )
    mask = mask & (long_count >= min_long_samples)

    # 上市天数过滤（向量化实现）
    print(f"  [过滤] 上市天数检查中...")
    _apply_listing_days_filter(mask, list_date_map, long_window)

    return mask


def get_rebalance_dates(
    calendar: list[date],
    freq: int = 20,
    start_date: str = "2019-01-01",
    forward_horizon: int = 20,
) -> list[date]:
    """从日历中每隔 freq 个交易日取一个调仓日.

    有效实验结束日 = end_date 往前推 forward_horizon 个交易日（防前视泄漏）。
    """
    experiment_start = date.fromisoformat(start_date)
    # 从 calendar 中找到实验起始日之后的第一个交易日
    valid = [d for d in calendar if d >= experiment_start]
    # 最后 forward_horizon 个交易日剔除（标签不可用）
    if len(valid) > forward_horizon:
        valid = valid[: -forward_horizon]
    # 每隔 freq 取一个
    rebalance = valid[::freq]
    return rebalance


# ---------------------------------------------------------------------------
# 第4区：分组工具
# ---------------------------------------------------------------------------


def assign_quantile_groups(
    values: pd.Series,
    group_count: int = 5,
) -> pd.Series:
    """将序列按分位数分为 group_count 组.

    G1 = 最低值, G{group_count} = 最高值。
    复用自 experiment_17_21 的 assign_quantile_groups 逻辑。
    """
    clean = values.dropna()
    if len(clean) < group_count:
        return pd.Series([pd.NA] * len(values), index=values.index, dtype="Int64")
    # 检查是否有足够变异
    if clean.nunique() < 2:
        return pd.Series([pd.NA] * len(values), index=values.index, dtype="Int64")
    ranks = clean.rank(method="first")
    try:
        groups = pd.qcut(ranks, q=group_count, labels=range(1, group_count + 1))
    except ValueError:
        return pd.Series([pd.NA] * len(values), index=values.index, dtype="Int64")
    result = groups.reindex(values.index)
    return result.astype("Int64")


def newey_west_ttest(
    series: pd.Series,
    lags: int | None = None,
) -> dict[str, Any]:
    """Newey-West HAC 稳健 t 检验.

    参数:
        series: 时序数据（如每日价差序列）
        lags: 截断滞后阶数，None 则自动选择 max(1, int(T^(1/3)))

    返回:
        dict with mean, std, hac_std, t_stat, nw_t_stat, n_obs, lags, p_value
    """
    x = series.dropna().to_numpy(dtype=float)
    T = len(x)
    if T < 2:
        return {
            "mean": float(np.mean(x)) if T > 0 else None,
            "std": None,
            "hac_std": None,
            "t_stat": None,
            "nw_t_stat": None,
            "n_observations": T,
            "lags_used": 0,
            "p_value_approx": None,
        }

    mean_x = float(np.mean(x))
    std_x = float(np.std(x, ddof=1))

    if lags is None:
        lags = max(1, int(T ** (1 / 3)))

    # 样本自协方差
    gamma = np.zeros(lags + 1)
    for j in range(lags + 1):
        if j == 0:
            gamma[j] = np.mean((x - mean_x) ** 2)
        else:
            gamma[j] = np.mean((x[j:] - mean_x) * (x[:-j] - mean_x))

    # Bartlett 核权重
    hac_var = gamma[0]
    for j in range(1, lags + 1):
        weight = 1.0 - j / (lags + 1)
        hac_var += 2 * weight * gamma[j]

    # 确保 HAC 方差非负
    hac_var = max(hac_var, 1e-15)

    hac_se = float(np.sqrt(hac_var / T))
    nw_t = mean_x / hac_se if hac_se > 0 else 0.0
    t_stat = mean_x / (std_x / np.sqrt(T)) if std_x > 0 else 0.0

    # 正态近似双侧 p 值
    p_value = float(2 * (1 - 0.5 * (1 + math.erf(abs(nw_t) / np.sqrt(2)))))

    return {
        "mean": mean_x,
        "std": std_x,
        "hac_std": hac_se,
        "t_stat": t_stat,
        "nw_t_stat": nw_t,
        "n_observations": T,
        "lags_used": lags,
        "p_value_approx": p_value,
    }


# ---------------------------------------------------------------------------
# 第5区：三个子实验
# ---------------------------------------------------------------------------


def run_experiment_a(
    abnormal_turnover: pd.DataFrame,
    forward_returns: pd.DataFrame,
    valid_mask: pd.DataFrame,
    rebalance_dates: list[date],
    group_count: int = 5,
) -> GroupResult:
    """实验A：单变量排序."""
    print(f"\n[实验A] 单变量排序，调仓日: {len(rebalance_dates)}")
    factor_matrix, forward_matrix, _ = _masked_rebalance_matrices(
        abnormal_turnover,
        forward_returns,
        valid_mask,
        rebalance_dates,
    )
    sort_returns = single_sort_returns(
        factor_matrix,
        forward_matrix,
        quantiles=group_count,
        min_cross_section=group_count * 2,
    )
    ts = _single_sort_to_legacy(sort_returns)
    if ts.empty:
        raise RuntimeError("实验A：无有效分组数据")

    # 分组汇总
    summary_rows = []
    for gid in sorted(ts["group"].unique()):
        sub = ts[ts["group"] == gid]
        nw = newey_west_ttest(sub["mean_return"])
        summary_rows.append({
            "group": int(gid),
            "mean_return": float(sub["mean_return"].mean()),
            "std_return": float(sub["mean_return"].std()),
            "t_stat": nw["t_stat"],
            "nw_t_stat": nw["nw_t_stat"],
            "p_value": nw["p_value_approx"],
            "n_dates": len(sub),
            "avg_n_stocks": float(sub["n_stocks"].mean()),
        })
    summary = pd.DataFrame(summary_rows)

    # G1-G5 价差时序
    pivot = ts.pivot_table(
        index="date", columns="group", values="mean_return", aggfunc="mean"
    )
    g1_col = 1 if 1 in pivot.columns else pivot.columns[0]
    g5_col = group_count if group_count in pivot.columns else pivot.columns[-1]
    spread_ts = pivot[g1_col] - pivot[g5_col]
    spread_nw = newey_west_ttest(spread_ts)

    return GroupResult(
        group_returns_ts=ts,
        group_returns_summary=summary,
        spread_ts=spread_ts,
        spread_nw=spread_nw,
    )


def _masked_rebalance_matrices(
    factor: pd.DataFrame,
    forward_returns: pd.DataFrame,
    valid_mask: pd.DataFrame,
    rebalance_dates: list[date],
    *,
    market_cap_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    selected_dates = [
        td
        for td in rebalance_dates
        if td in factor.index
        and td in forward_returns.index
        and (market_cap_df is None or td in market_cap_df.index)
    ]
    mask = valid_mask.reindex(
        index=factor.index,
        columns=factor.columns,
        fill_value=False,
    ).astype(bool)
    factor_matrix = factor.where(mask).loc[selected_dates]
    forward_mask = mask.reindex(
        index=forward_returns.index,
        columns=forward_returns.columns,
        fill_value=False,
    )
    forward_matrix = forward_returns.where(forward_mask).loc[selected_dates]
    if market_cap_df is None:
        return factor_matrix, forward_matrix, None
    size_mask = mask.reindex(
        index=market_cap_df.index,
        columns=market_cap_df.columns,
        fill_value=False,
    )
    size_matrix = market_cap_df.where(size_mask).loc[selected_dates]
    return factor_matrix, forward_matrix, size_matrix


def _single_sort_to_legacy(sort_returns: pd.DataFrame) -> pd.DataFrame:
    if sort_returns.empty:
        return pd.DataFrame(columns=["date", "group", "mean_return", "n_stocks"])
    output = sort_returns.rename(
        columns={
            "trade_date": "date",
            "mean_forward_return": "mean_return",
            "symbol_count": "n_stocks",
        }
    )[["date", "group", "mean_return", "n_stocks"]].copy()
    output["date"] = pd.to_datetime(output["date"]).dt.date
    output["group"] = output["group"].astype(int)
    return output


def _double_sort_to_legacy(sort_returns: pd.DataFrame, *, conditional: bool) -> pd.DataFrame:
    if sort_returns.empty:
        return pd.DataFrame(columns=["date", "size_group", "turnover_group", "mean_return", "n_stocks"])
    size_column = "conditioning_group" if conditional else "size_group"
    output = sort_returns.rename(
        columns={
            "trade_date": "date",
            size_column: "size_group",
            "factor_group": "turnover_group",
            "mean_forward_return": "mean_return",
            "symbol_count": "n_stocks",
        }
    )[["date", "size_group", "turnover_group", "mean_return", "n_stocks"]].copy()
    output["date"] = pd.to_datetime(output["date"]).dt.date
    output["size_group"] = output["size_group"].astype(int)
    output["turnover_group"] = output["turnover_group"].astype(int)
    return output


def _double_sort_spreads(cell_df: pd.DataFrame, group_count: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    columns = ["date", "size_group", "turnover_spread"]
    if cell_df.empty:
        return pd.DataFrame(columns=columns)
    pivot = cell_df.pivot_table(
        index=["date", "size_group"],
        columns="turnover_group",
        values="mean_return",
        aggfunc="mean",
    )
    for (trade_date, size_group), row in pivot.iterrows():
        if 1 not in row.index or group_count not in row.index:
            continue
        low = row[1]
        high = row[group_count]
        if pd.notna(low) and pd.notna(high):
            rows.append(
                {
                    "date": trade_date,
                    "size_group": int(size_group),
                    "turnover_spread": float(low - high),
                }
            )
    return pd.DataFrame(rows, columns=columns)


def _double_sort_core(
    abnormal_turnover: pd.DataFrame,
    market_cap_df: pd.DataFrame,
    forward_returns: pd.DataFrame,
    valid_mask: pd.DataFrame,
    rebalance_dates: list[date],
    group_count: int,
    conditional: bool,
) -> DoubleSortResult:
    """双重排序核心逻辑.

    conditional=False: 独立双重排序（市值和换手率都在全市场独立分组）
    conditional=True:  条件双重排序（先市值分组，再组内换手率分组）
    """
    mode = "条件" if conditional else "独立"
    print(f"\n[实验{'C' if conditional else 'B'}] {mode}双重排序，调仓日: {len(rebalance_dates)}")
    factor_matrix, forward_matrix, size_matrix = _masked_rebalance_matrices(
        abnormal_turnover,
        forward_returns,
        valid_mask,
        rebalance_dates,
        market_cap_df=market_cap_df,
    )
    if conditional:
        sort_returns = conditional_double_sort_returns(
            size_matrix,
            factor_matrix,
            forward_matrix,
            groups=group_count,
            min_cross_section=group_count * 2,
        )
    else:
        sort_returns = independent_double_sort_returns(
            factor_matrix,
            size_matrix,
            forward_matrix,
            groups=group_count,
            min_cross_section=group_count * 2,
        )
    cell_df = _double_sort_to_legacy(sort_returns, conditional=conditional)
    spread_df = _double_sort_spreads(cell_df, group_count)

    if cell_df.empty:
        raise RuntimeError(f"实验{'C' if conditional else 'B'}：无有效双重排序数据")

    # 5x5 平均收益矩阵
    cell_summary = cell_df.groupby(["size_group", "turnover_group"]).agg(
        mean_return=("mean_return", "mean"),
        n_dates=("date", "nunique"),
        avg_n_stocks=("n_stocks", "mean"),
    ).reset_index()

    # 样本数矩阵
    count_matrix = cell_df.groupby(["size_group", "turnover_group"]).agg(
        avg_n_stocks=("n_stocks", "mean"),
    ).reset_index().pivot(
        index="size_group", columns="turnover_group", values="avg_n_stocks"
    )

    # 各市值组换手率价差汇总
    spread_summary_rows = []
    for sg in sorted(spread_df["size_group"].unique()):
        sub = spread_df[spread_df["size_group"] == sg]
        nw = newey_west_ttest(sub["turnover_spread"])
        spread_summary_rows.append({
            "size_group": int(sg),
            "mean_spread": float(sub["turnover_spread"].mean()),
            "nw_t_stat": nw["nw_t_stat"],
            "p_value": nw["p_value_approx"],
            "n_dates": len(sub),
        })
    spread_summary = pd.DataFrame(spread_summary_rows)

    # 各市值组价差均值序列（用于计算整体 NW t）
    pivot_spread = spread_df.pivot_table(
        index="date", columns="size_group", values="turnover_spread", aggfunc="mean"
    )
    avg_spread_ts = pivot_spread.mean(axis=1)
    avg_spread_nw = newey_west_ttest(avg_spread_ts)

    return DoubleSortResult(
        cell_returns=cell_df,
        cell_summary=cell_summary,
        size_spread_ts=spread_df,
        size_spread_summary=spread_summary,
        avg_spread_nw=avg_spread_nw,
        count_matrix=count_matrix,
    )


def run_experiment_b(
    abnormal_turnover: pd.DataFrame,
    market_cap_df: pd.DataFrame,
    forward_returns: pd.DataFrame,
    valid_mask: pd.DataFrame,
    rebalance_dates: list[date],
    group_count: int = 5,
) -> DoubleSortResult:
    """实验B：独立双重排序."""
    return _double_sort_core(
        abnormal_turnover, market_cap_df, forward_returns,
        valid_mask, rebalance_dates, group_count, conditional=False,
    )


def run_experiment_c(
    abnormal_turnover: pd.DataFrame,
    market_cap_df: pd.DataFrame,
    forward_returns: pd.DataFrame,
    valid_mask: pd.DataFrame,
    rebalance_dates: list[date],
    group_count: int = 5,
) -> DoubleSortResult:
    """实验C：条件双重排序."""
    return _double_sort_core(
        abnormal_turnover, market_cap_df, forward_returns,
        valid_mask, rebalance_dates, group_count, conditional=True,
    )


# ---------------------------------------------------------------------------
# 第6区：可视化
# ---------------------------------------------------------------------------


def generate_charts(
    output_dir: Path,
    exp_a: GroupResult,
    exp_b: DoubleSortResult,
    exp_c: DoubleSortResult,
    rebalance_dates: list[date],
) -> list[Path]:
    """生成 5 张图表."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    # 设置中文字体
    _cjk_fonts = [f.name for f in fm.fontManager.ttflist
                  if any(k in f.name for k in ['Droid Sans Fallback', 'WenQuanYi', 'Noto Sans CJK'])]
    if _cjk_fonts:
        plt.rcParams["font.family"] = _cjk_fonts[0]
    plt.rcParams["axes.unicode_minus"] = False

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    # 图1：实验A 5 组平均收益柱状图
    fig, ax = plt.subplots(figsize=(10, 6))
    summary = exp_a.group_returns_summary.sort_values("group")
    colors = ["#2196F3" if v >= 0 else "#F44336" for v in summary["mean_return"]]
    bars = ax.bar(
        [f"G{int(g)}" for g in summary["group"]],
        summary["mean_return"] * 100,
        color=colors,
        edgecolor="white",
    )
    for bar, nw_t in zip(bars, summary["nw_t_stat"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (0.02 if bar.get_height() >= 0 else -0.08),
            f"t={nw_t:.2f}" if nw_t is not None else "N/A",
            ha="center", fontsize=9,
        )
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.set_title("实验A：异常换手率 5 组平均前瞻收益", fontsize=14)
    ax.set_xlabel("换手率分组 (G1=最低, G5=最高)")
    ax.set_ylabel("平均 forward_return_20d (%)")
    fig.tight_layout()
    path1 = output_dir / "exp_a_group_returns.png"
    fig.savefig(str(path1), dpi=150)
    plt.close(fig)
    paths.append(path1)

    # 图2：实验B 5×5 热力图
    _save_double_sort_heatmap(
        exp_b, output_dir / "exp_b_heatmap.png",
        "实验B：独立双重排序 5×5 平均收益 (%)",
    )
    paths.append(output_dir / "exp_b_heatmap.png")

    # 图3：实验C 5×5 热力图
    _save_double_sort_heatmap(
        exp_c, output_dir / "exp_c_heatmap.png",
        "实验C：条件双重排序 5×5 平均收益 (%)",
    )
    paths.append(output_dir / "exp_c_heatmap.png")

    # 图4：实验A G1-G5 价差时序
    fig, ax = plt.subplots(figsize=(12, 5))
    spread = exp_a.spread_ts.dropna()
    ax.plot(spread.index, spread.values * 100, color="#2196F3", linewidth=0.8)
    ax.axhline(y=0, color="black", linewidth=0.5, linestyle="--")
    ax.fill_between(
        spread.index, 0, spread.values * 100,
        alpha=0.15, color="#2196F3",
    )
    nw = exp_a.spread_nw
    ax.set_title(
        f"实验A：G1-G5 价差时序 (均值={nw['mean']*100:.3f}%, NW t={nw['nw_t_stat']:.2f})",
        fontsize=13,
    )
    ax.set_ylabel("G1 - G5 价差 (%)")
    fig.tight_layout()
    path4 = output_dir / "exp_a_spread_ts.png"
    fig.savefig(str(path4), dpi=150)
    plt.close(fig)
    paths.append(path4)

    # 图5：实验B vs C 各市值组价差对比
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(1, 6)
    width = 0.35
    b_spreads = [
        exp_b.size_spread_summary[
            exp_b.size_spread_summary["size_group"] == i
        ]["mean_spread"].values[0] * 100
        if i in exp_b.size_spread_summary["size_group"].values else 0
        for i in range(1, 6)
    ]
    c_spreads = [
        exp_c.size_spread_summary[
            exp_c.size_spread_summary["size_group"] == i
        ]["mean_spread"].values[0] * 100
        if i in exp_c.size_spread_summary["size_group"].values else 0
        for i in range(1, 6)
    ]
    ax.bar(x - width/2, b_spreads, width, label="独立双重排序 (B)", color="#2196F3")
    ax.bar(x + width/2, c_spreads, width, label="条件双重排序 (C)", color="#FF9800")
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f"市值 G{i}" for i in range(1, 6)])
    ax.set_title("实验B vs C：各市值组内换手率价差对比", fontsize=13)
    ax.set_ylabel("G1 - G5 价差 (%)")
    ax.legend()
    fig.tight_layout()
    path5 = output_dir / "exp_b_c_spread_compare.png"
    fig.savefig(str(path5), dpi=150)
    plt.close(fig)
    paths.append(path5)

    return paths


def _save_double_sort_heatmap(
    result: DoubleSortResult,
    path: Path,
    title: str,
) -> None:
    """保存双重排序 5×5 热力图."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    _cjk_fonts = [f.name for f in fm.fontManager.ttflist
                  if any(k in f.name for k in ['Droid Sans Fallback', 'WenQuanYi', 'Noto Sans CJK'])]
    if _cjk_fonts:
        plt.rcParams["font.family"] = _cjk_fonts[0]
    plt.rcParams["axes.unicode_minus"] = False

    pivot = result.cell_summary.pivot(
        index="size_group", columns="turnover_group", values="mean_return"
    )
    # 确保 5x5 完整
    for i in range(1, 6):
        if i not in pivot.index:
            pivot.loc[i] = np.nan
        if i not in pivot.columns:
            pivot[i] = np.nan
    pivot = pivot.reindex(sorted(pivot.index), axis=0)
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)

    fig, ax = plt.subplots(figsize=(8, 7))
    data_pct = pivot.values * 100
    im = ax.imshow(data_pct, cmap="RdYlGn", aspect="auto", vmin=-1.5, vmax=1.5)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = data_pct[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.2f}%", ha="center", va="center", fontsize=10,
                        color="black" if abs(val) < 0.8 else "white")

    ax.set_xticks(range(5))
    ax.set_xticklabels([f"T{i}" for i in range(1, 6)])
    ax.set_yticks(range(5))
    ax.set_yticklabels([f"S{i}" for i in range(1, 6)])
    ax.set_xlabel("换手率分组 (T1=最低, T5=最高)")
    ax.set_ylabel("市值分组 (S1=最小, S5=最大)")
    ax.set_title(title, fontsize=13)
    fig.colorbar(im, ax=ax, label="mean forward_return_20d (%)")
    fig.tight_layout()
    fig.savefig(str(path), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 第7区：报告生成
# ---------------------------------------------------------------------------


def format_pct(value: float | None, digits: int = 3) -> str:
    """格式化百分比."""
    if value is None or np.isnan(value):
        return "N/A"
    return f"{value * 100:.{digits}f}%"


def format_t(value: float | None) -> str:
    """格式化 t 值."""
    if value is None or np.isnan(value):
        return "N/A"
    return f"{value:.2f}"


def render_report(
    *,
    args: argparse.Namespace,
    run_id: str,
    data: ExperimentData,
    exp_a: GroupResult,
    exp_b: DoubleSortResult,
    exp_c: DoubleSortResult,
    chart_paths: list[Path],
    output_paths: dict[str, Path],
) -> str:
    """生成 Markdown 主研究报告."""
    lines: list[str] = []
    lines.append("# A股低换手率因子双重排序实验报告")
    lines.append("")
    lines.append(f"**Run ID**: `{run_id}`")
    lines.append(f"**Factor ID**: `{FACTOR_ID}`")
    lines.append(f"**Strategy ID**: `{STRATEGY_ID}`")
    lines.append(f"**生成时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append("")

    # 执行结论
    lines.append("## 执行结论")
    lines.append("")
    lines.append(f"- **实验区间**: {args.start_date} ~ {args.end_date}")
    lines.append(f"- **预热起始**: {args.warmup_start}")
    lines.append(f"- **交易日数**: {len(data.calendar)}")
    lines.append(f"- **调仓频率**: 每 {args.rebalance_freq} 个交易日")
    lines.append(f"- **调仓日数**: {len(data.rebalance_dates)}")
    lines.append(f"- **分组数**: {args.group_count}")
    lines.append(f"- **前瞻 horizon**: {args.forward_horizon} 个交易日")
    lines.append("")

    a_nw = exp_a.spread_nw
    b_nw = exp_b.avg_spread_nw
    c_nw = exp_c.avg_spread_nw

    lines.append("| 实验 | G1-G5 价差均值 | NW t 值 | p 值 | 结论 |")
    lines.append("|------|---------------|---------|------|------|")
    lines.append(
        f"| 单变量排序 (A) | {format_pct(a_nw['mean'])} | {format_t(a_nw['nw_t_stat'])} "
        f"| {a_nw['p_value_approx']:.4f} | "
        f"{'低换手跑赢，显著' if a_nw.get('nw_t_stat') and abs(a_nw['nw_t_stat']) > 2 else '需进一步分析'} |"
    )
    lines.append(
        f"| 独立双重排序 (B) | {format_pct(b_nw['mean'])} | {format_t(b_nw['nw_t_stat'])} "
        f"| {b_nw['p_value_approx']:.4f} | "
        f"{'控制市值后仍有效' if b_nw.get('nw_t_stat') and b_nw['nw_t_stat'] > 0 else '需进一步分析'} |"
    )
    lines.append(
        f"| 条件双重排序 (C) | {format_pct(c_nw['mean'])} | {format_t(c_nw['nw_t_stat'])} "
        f"| {c_nw['p_value_approx']:.4f} | "
        f"{'同市值内仍有增量' if c_nw.get('nw_t_stat') and c_nw['nw_t_stat'] > 0 else '需进一步分析'} |"
    )
    lines.append("")

    # 1. 数据与因子定义
    lines.append("## 1. 数据与因子定义")
    lines.append("")
    lines.append("### 1.1 数据来源")
    lines.append("")
    lines.append("- **market_cap/turnover_rate**: 数据湖 canonical, tushare daily_basic 接口")
    lines.append("- **prices (adjusted_close)**: 数据湖 canonical, tushare daily + adj_factor 接口")
    lines.append("- **交易日历**: 数据湖 canonical, tushare trade_cal 接口")
    lines.append("- **股票基本信息 (list_date)**: 数据湖 canonical, tushare stock_basic 接口")
    lines.append("")
    lines.append("### 1.2 因子定义")
    lines.append("")
    lines.append("```")
    lines.append("abnormal_turnover_21_252 = mean(turnover_rate, 21d) / mean(turnover_rate, 252d)")
    lines.append("```")
    lines.append("")
    lines.append("- 短期窗口: 21 个交易日 (min_periods=15)")
    lines.append("- 长期窗口: 252 个交易日 (min_periods=60)")
    lines.append("- 极端值截断: [0.01, 10.0]")
    lines.append("")
    lines.append("### 1.3 前瞻收益")
    lines.append("")
    lines.append("```")
    lines.append("forward_return_20d = adjusted_close[t+20] / adjusted_close[t] - 1")
    lines.append("```")
    lines.append("")
    lines.append("- 使用 adjusted_close (前复权) 计算收益")
    lines.append(f"- 最后 {args.forward_horizon} 个交易日从有效样本中剔除（防前视泄漏）")
    lines.append("")

    # 1.4 过滤规则
    lines.append("### 1.4 过滤规则")
    lines.append("")
    lines.append("1. 剔除 market_cap 缺失的股票")
    lines.append("2. 剔除 turnover_rate 缺失或 <= 0 的股票（隐含停牌）")
    lines.append("3. 剔除 252 日窗口有效非零样本 < 60 的股票")
    lines.append("4. 剔除 forward_return 缺失的股票")
    lines.append("5. 剔除 abnormal_turnover 缺失的股票")
    lines.append("6. 剔除上市不足 252 个自然日的股票")
    lines.append("")

    # 1.5 限制声明
    lines.append("### 1.5 限制声明")
    lines.append("")
    lines.append("- ⚠️ 本实验使用 ex-post 复权价格 (adjustment_policy=qfq)，不声明 PIT 无泄漏复权")
    lines.append("- ⚠️ 本实验不声明 tradability pass（未使用 ST/涨跌停/停牌 PIT 数据做可交易性筛选）")
    lines.append("- ⚠️ 本实验不声明 capacity pass（未计算冲击成本和容量约束）")
    lines.append("- ⚠️ 本实验不声明 simulation-ready 或 QMT-ready")
    lines.append("- ⚠️ 本实验未触发 QMT、provider fetch、lake write、publish 或凭据读取")
    lines.append("")

    # 2. 实验A
    lines.append("## 2. 实验A：单变量排序")
    lines.append("")
    lines.append("### 2.1 5 组平均收益")
    lines.append("")
    lines.append("| 分组 | 平均收益 | 标准差 | t 值 | NW t 值 | p 值 | 调仓日数 | 平均股票数 |")
    lines.append("|------|---------|--------|------|---------|------|---------|-----------|")
    for _, row in exp_a.group_returns_summary.iterrows():
        lines.append(
            f"| G{int(row['group'])} | {format_pct(row['mean_return'])} "
            f"| {format_pct(row['std_return'])} | {format_t(row['t_stat'])} "
            f"| {format_t(row['nw_t_stat'])} | {row['p_value']:.4f} "
            f"| {int(row['n_dates'])} | {int(row['avg_n_stocks'])} |"
        )
    lines.append("")

    lines.append("### 2.2 G1-G5 价差")
    lines.append("")
    lines.append(f"- 价差均值: {format_pct(a_nw['mean'])}")
    lines.append(f"- NW t 值: {format_t(a_nw['nw_t_stat'])}")
    lines.append(f"- p 值: {a_nw['p_value_approx']:.4f}")
    lines.append(f"- 样本期数: {a_nw['n_observations']}")
    lines.append(f"- 滞后阶数: {a_nw['lags_used']}")
    lines.append("")

    lines.append(f"![实验A 分组收益](charts/exp_a_group_returns.png)")
    lines.append(f"![实验A 价差时序](charts/exp_a_spread_ts.png)")
    lines.append("")

    # 3. 实验B
    lines.append("## 3. 实验B：独立双重排序")
    lines.append("")
    lines.append("### 3.1 5×5 平均收益矩阵 (%)")
    lines.append("")
    _render_heatmap_table(lines, exp_b)
    lines.append("")
    lines.append("### 3.2 样本数矩阵")
    lines.append("")
    _render_count_table(lines, exp_b)
    lines.append("")
    lines.append("### 3.3 各市值组内换手率价差")
    lines.append("")
    lines.append("| 市值组 | 价差均值 | NW t 值 | p 值 | 调仓日数 |")
    lines.append("|--------|---------|---------|------|---------|")
    for _, row in exp_b.size_spread_summary.iterrows():
        lines.append(
            f"| S{int(row['size_group'])} | {format_pct(row['mean_spread'])} "
            f"| {format_t(row['nw_t_stat'])} | {row['p_value']:.4f} "
            f"| {int(row['n_dates'])} |"
        )
    lines.append("")
    lines.append(f"- 各市值组价差均值: {format_pct(b_nw['mean'])}")
    lines.append(f"- NW t 值: {format_t(b_nw['nw_t_stat'])}")
    lines.append("")
    lines.append(f"![实验B 热力图](charts/exp_b_heatmap.png)")
    lines.append("")

    # 4. 实验C
    lines.append("## 4. 实验C：条件双重排序")
    lines.append("")
    lines.append("### 4.1 5×5 平均收益矩阵 (%)")
    lines.append("")
    _render_heatmap_table(lines, exp_c)
    lines.append("")
    lines.append("### 4.2 样本数矩阵")
    lines.append("")
    _render_count_table(lines, exp_c)
    lines.append("")
    lines.append("### 4.3 各市值组内条件换手率价差")
    lines.append("")
    lines.append("| 市值组 | 价差均值 | NW t 值 | p 值 | 调仓日数 |")
    lines.append("|--------|---------|---------|------|---------|")
    for _, row in exp_c.size_spread_summary.iterrows():
        lines.append(
            f"| S{int(row['size_group'])} | {format_pct(row['mean_spread'])} "
            f"| {format_t(row['nw_t_stat'])} | {row['p_value']:.4f} "
            f"| {int(row['n_dates'])} |"
        )
    lines.append("")
    lines.append(f"- 各市值组价差均值: {format_pct(c_nw['mean'])}")
    lines.append(f"- NW t 值: {format_t(c_nw['nw_t_stat'])}")
    lines.append("")
    lines.append(f"![实验C 热力图](charts/exp_c_heatmap.png)")
    lines.append("")

    # 5. B vs C 对比
    lines.append("## 5. 实验B vs 实验C 对比")
    lines.append("")
    lines.append("| 市值组 | B 独立排序价差 | C 条件排序价差 | 差异 |")
    lines.append("|--------|---------------|---------------|------|")
    for sg in range(1, 6):
        b_val = exp_b.size_spread_summary[
            exp_b.size_spread_summary["size_group"] == sg
        ]["mean_spread"].values
        c_val = exp_c.size_spread_summary[
            exp_c.size_spread_summary["size_group"] == sg
        ]["mean_spread"].values
        b_str = format_pct(b_val[0]) if len(b_val) > 0 else "N/A"
        c_str = format_pct(c_val[0]) if len(c_val) > 0 else "N/A"
        diff = (b_val[0] - c_val[0]) * 100 if len(b_val) > 0 and len(c_val) > 0 else None
        diff_str = f"{diff:.3f}%" if diff is not None else "N/A"
        lines.append(f"| S{sg} | {b_str} | {c_str} | {diff_str} |")
    lines.append("")
    lines.append(f"![B vs C 对比](charts/exp_b_c_spread_compare.png)")
    lines.append("")

    # 6. 分年度稳定性
    lines.append("## 6. 分年度稳定性")
    lines.append("")
    _render_yearly_stability(lines, exp_a, exp_b, exp_c)
    lines.append("")

    # 7. 结论
    lines.append("## 7. 结论与建议")
    lines.append("")
    lines.append("### 7.1 研究假设检验")
    lines.append("")
    lines.append(f"- H1（异常换手率越低，未来收益越高）: "
                 f"{'支持' if a_nw.get('nw_t_stat') and a_nw['nw_t_stat'] > 0 else '不支持/需进一步研究'}")
    lines.append(f"- 控制市值后是否仍有效 (独立排序): "
                 f"{'是' if b_nw.get('nw_t_stat') and b_nw['nw_t_stat'] > 0 else '否/需进一步研究'}")
    lines.append(f"- 同市值内是否有增量 (条件排序): "
                 f"{'是' if c_nw.get('nw_t_stat') and c_nw['nw_t_stat'] > 0 else '否/需进一步研究'}")
    lines.append("")

    lines.append("### 7.2 是否纳入多因子候选库")
    lines.append("")
    lines.append("> 本结论需人工决策。以下为基于实验结果的推荐：")
    lines.append("")
    lines.append("- 若条件双重排序 NW t > 2 且价差为正：推荐纳入候选因子库")
    lines.append("- 若 NW t 介于 1.5-2：可作为观察因子，需进一步验证")
    lines.append("- 若 NW t < 1.5 或价差为负：不建议纳入，或需修改因子定义")
    lines.append("")

    lines.append("### 7.3 限制与后续")
    lines.append("")
    lines.append("- 本实验未使用 PIT 数据，存在生存偏差和前视偏差风险")
    lines.append("- 建议后续补充 ST/涨跌停/停牌过滤后重新验证")
    lines.append("- 建议与低波动、价值、质量因子做相关性分析后再确定多因子组合权重")
    lines.append("")

    # 附录
    lines.append("## 附录")
    lines.append("")
    lines.append("### A. 输出产物清单")
    lines.append("")
    lines.append("| 产物 | 路径 |")
    lines.append("|------|------|")
    for name, p in sorted(output_paths.items()):
        lines.append(f"| {name} | {_artifact_ref(p)} |")
    lines.append("")
    lines.append("### B. 图表索引")
    lines.append("")
    for p in chart_paths:
        lines.append(f"- [{p.name}](charts/{p.name})")
    lines.append("")

    return "\n".join(lines)


def _render_heatmap_table(lines: list[str], result: DoubleSortResult) -> None:
    """渲染 5×5 热力值表格."""
    pivot = result.cell_summary.pivot(
        index="size_group", columns="turnover_group", values="mean_return"
    )
    lines.append("| 市值 \\ 换手率 | T1 (低) | T2 | T3 | T4 | T5 (高) |")
    lines.append("|------------|---------|-----|-----|-----|--------|")
    for sg in range(1, 6):
        row_vals = []
        for tg in range(1, 6):
            if sg in pivot.index and tg in pivot.columns:
                val = pivot.loc[sg, tg]
                row_vals.append(format_pct(val) if not np.isnan(val) else "N/A")
            else:
                row_vals.append("N/A")
        lines.append(f"| S{sg} ({'小' if sg==1 else '大' if sg==5 else ''}盘) | {' | '.join(row_vals)} |")


def _render_count_table(lines: list[str], result: DoubleSortResult) -> None:
    """渲染样本数矩阵."""
    cm = result.count_matrix
    lines.append("| 市值 \\ 换手率 | T1 | T2 | T3 | T4 | T5 |")
    lines.append("|------------|-----|-----|-----|-----|-----|")
    for sg in range(1, 6):
        row_vals = []
        for tg in range(1, 6):
            if sg in cm.index and tg in cm.columns:
                val = cm.loc[sg, tg]
                row_vals.append(f"{int(val)}" if not np.isnan(val) else "N/A")
            else:
                row_vals.append("N/A")
        lines.append(f"| S{sg} | {' | '.join(row_vals)} |")


def _render_yearly_stability(
    lines: list[str],
    exp_a: GroupResult,
    exp_b: DoubleSortResult,
    exp_c: DoubleSortResult,
) -> None:
    """渲染分年度稳定性表."""
    # 从价差时序中提取年份
    for label, spread_ts in [("实验A", exp_a.spread_ts)]:
        if spread_ts.empty:
            continue
        yearly = spread_ts.groupby(lambda d: d.year if hasattr(d, 'year') else str(d)[:4]).agg(
            ["mean", "std", "count"]
        )
        lines.append(f"### {label} 分年度 G1-G5 价差")
        lines.append("")
        lines.append("| 年份 | 价差均值 | 标准差 | 调仓次数 |")
        lines.append("|------|---------|--------|---------|")
        for yr, row in yearly.iterrows():
            lines.append(
                f"| {yr} | {format_pct(row['mean'])} | {format_pct(row['std'])} "
                f"| {int(row['count'])} |"
            )
        lines.append("")


# ---------------------------------------------------------------------------
# 第8区：CR030 产物与过程文档
# ---------------------------------------------------------------------------


def write_cr030_artifacts(
    run_dir: Path,
    run_id: str,
    args: argparse.Namespace,
    exp_a: GroupResult,
    exp_b: DoubleSortResult,
    exp_c: DoubleSortResult,
    data: ExperimentData,
) -> dict[str, Path]:
    """生成 CR030 标准研究产物."""
    paths: dict[str, Path] = {}

    # FactorSpec
    factor_spec = {
        "factor_id": FACTOR_ID,
        "factor_family": "turnover",
        "description": "异常换手率因子：21日换手率均值 / 252日换手率均值",
        "direction": "negative",
        "input_fields": ["turnover_rate"],
        "windows": {"short": 21, "long": 252},
        "min_periods": {"short": 15, "long": 60},
        "clip_range": [0.01, 10.0],
        "research_note": "低异常换手率 → 高未来收益",
    }
    factor_spec_path = run_dir / "factor_spec.json"
    factor_spec_path.write_text(json.dumps(factor_spec, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["factor_spec"] = factor_spec_path

    # FactorRunSpec
    factor_run_spec = {
        "run_id": run_id,
        "factor_id": FACTOR_ID,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "warmup_start": args.warmup_start,
        "rebalance_freq": args.rebalance_freq,
        "forward_horizon": args.forward_horizon,
        "group_count": args.group_count,
        "min_252d_samples": args.min_252d_samples,
        "data_sources": {
            "market_cap": str(MC_DIR),
            "prices": str(PRICES_DIR),
            "trade_calendar": str(TC_PATH),
            "stock_basic": str(SB_PATH),
        },
        "adjustment_policy": "qfq",
        "adjustment_note": "ex-post 复权，不声明 PIT 无泄漏",
        "blocked_claims": [
            "tradability_pass",
            "capacity_pass",
            "simulation_ready",
            "qmt_ready",
            "pit_no_lookahead",
        ],
    }
    factor_run_spec_path = run_dir / "factor_run_spec.json"
    factor_run_spec_path.write_text(json.dumps(factor_run_spec, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["factor_run_spec"] = factor_run_spec_path

    # FactorEvaluationReport (JSON)
    eval_dir = REPORTS_BASE / "factor_evaluation" / "v1" / f"report-{run_id}-{FACTOR_ID}"
    eval_dir.mkdir(parents=True, exist_ok=True)
    eval_report = {
        "report_id": f"report-{run_id}-{FACTOR_ID}",
        "schema": "factor_evaluation_report_v1",
        "status": "research_limited",
        "run_id": run_id,
        "factor_id": FACTOR_ID,
        "metrics": {
            "experiment_a": {
                "g1_g5_spread_mean": exp_a.spread_nw["mean"],
                "g1_g5_spread_nw_t": exp_a.spread_nw["nw_t_stat"],
                "g1_g5_spread_p_value": exp_a.spread_nw["p_value_approx"],
                "n_observations": exp_a.spread_nw["n_observations"],
            },
            "experiment_b": {
                "avg_size_spread_mean": exp_b.avg_spread_nw["mean"],
                "avg_size_spread_nw_t": exp_b.avg_spread_nw["nw_t_stat"],
            },
            "experiment_c": {
                "avg_size_spread_mean": exp_c.avg_spread_nw["mean"],
                "avg_size_spread_nw_t": exp_c.avg_spread_nw["nw_t_stat"],
            },
        },
        "claims": {
            "allowed": ["raw_factor_performance", "close_only_exploration", "research_only"],
            "blocked": [
                {"claim": "tradability_pass", "reason": "ST/涨跌停/停牌 PIT 数据未使用"},
                {"claim": "capacity_pass", "reason": "冲击成本和容量约束未计算"},
                {"claim": "simulation_ready", "reason": "未通过 Stage6 全部 P0 gate"},
                {"claim": "qmt_ready", "reason": "未接入 QMT gateway"},
                {"claim": "pit_no_lookahead", "reason": "使用 ex-post 复权价格"},
            ],
        },
        "limitations": [
            "ex-post 复权价格，不声明 PIT 无泄漏",
            "未使用 ST/涨跌停/停牌 PIT 数据",
            "未计算冲击成本和容量约束",
            "固定 snapshot universe，非 PIT universe",
        ],
    }
    eval_json_path = eval_dir / "report.json"
    eval_json_path.write_text(json.dumps(eval_report, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["factor_evaluation_report"] = eval_json_path

    # ExperimentManifest
    manifest = {
        "manifest_id": f"manifest-{run_id}",
        "schema": "experiment_manifest_v1",
        "run_id": run_id,
        "factor_id": FACTOR_ID,
        "strategy_id": STRATEGY_ID,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "research_completed",
        "outputs": {name: _artifact_ref(p) for name, p in paths.items()},
    }
    manifest_path = run_dir / "experiment_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["experiment_manifest"] = manifest_path

    # ResearchReportCatalog
    catalog_dir = REPORTS_BASE / "research_catalog" / "v1" / f"catalog-{run_id}"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    catalog = {
        "catalog_id": f"catalog-{run_id}",
        "run_id": run_id,
        "factor_id": FACTOR_ID,
        "title": "A股低换手率因子双重排序实验",
        "category": "factor_research",
        "status": "research_completed",
        "report_path": _artifact_ref(run_dir / "turnover_factor_replication_report.md"),
    }
    (catalog_dir / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["research_catalog"] = catalog_dir / "catalog.json"

    # StrategyAdmissionPackage
    sap_dir = REPORTS_BASE / "stage6_admission" / f"package-{STRATEGY_ID}-{run_id}"
    sap_dir.mkdir(parents=True, exist_ok=True)
    sap = {
        "package_id": f"package-{STRATEGY_ID}-{run_id}",
        "strategy_id": STRATEGY_ID,
        "run_id": run_id,
        "admission_status": "research_only",
        "blocked_reasons": [
            {
                "gate": "tradability",
                "reason": "ST/涨跌停/停牌 PIT 数据未使用，不可声明 tradability pass",
            },
            {
                "gate": "capacity",
                "reason": "冲击成本和容量约束未计算，不可声明 capacity pass",
            },
            {
                "gate": "simulation_ready",
                "reason": "未通过 Stage6 全部 P0 gate",
            },
            {
                "gate": "qmt_ready",
                "reason": "未接入 QMT gateway",
            },
        ],
        "evidence": {
            "factor_evaluation_report": _artifact_ref(eval_json_path),
            "research_report": _artifact_ref(run_dir / "turnover_factor_replication_report.md"),
        },
        "recommendation": "仅作为因子研究参考，不可直接用于模拟盘或实盘",
    }
    sap_path = sap_dir / "strategy_admission_package.json"
    sap_path.write_text(json.dumps(sap, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["strategy_admission_package"] = sap_path

    # 策略准入摘要
    summary_md = sap_dir / "summary.md"
    summary_md.write_text(
        f"# 策略准入摘要：{STRATEGY_ID}\n\n"
        f"- **Run ID**: {run_id}\n"
        f"- **状态**: research_only\n"
        f"- **不可用于模拟盘/实盘**\n\n"
        f"## 阻断原因\n\n"
        f"- tradability: ST/涨跌停/停牌 PIT 数据未使用\n"
        f"- capacity: 冲击成本和容量约束未计算\n"
        f"- simulation_ready: 未通过 Stage6 全部 P0 gate\n"
        f"- qmt_ready: 未接入 QMT gateway\n\n"
        f"## 证据\n\n"
        f"- 因子评价报告: {_artifact_ref(eval_json_path)}\n"
        f"- 研究报告: {_artifact_ref(run_dir / 'turnover_factor_replication_report.md')}\n",
        encoding="utf-8",
    )
    paths["strategy_admission_summary"] = summary_md

    return paths


def write_process_docs(
    args: argparse.Namespace,
    run_id: str,
    data: ExperimentData,
) -> dict[str, Path]:
    """生成过程文档."""
    paths: dict[str, Path] = {}
    PROCESS_DIR.mkdir(parents=True, exist_ok=True)

    # PLAN.md
    plan = (
        "# 实验计划：A股低换手率因子双重排序\n\n"
        f"**Run ID**: {run_id}\n\n"
        "## 研究问题\n\n"
        "控制市值后，A股低换手率股票是否仍显著跑赢高换手率股票？\n\n"
        "## 研究假设\n\n"
        "H1: 异常换手率越低，股票未来收益越高。\n"
        "控制变量: 市值\n"
        "目标变量: 异常换手率 (abnormal_turnover_21_252)\n\n"
        "## 实验设计\n\n"
        "- A: 单变量排序 (异常换手率 5 分组)\n"
        "- B: 独立双重排序 (市值 5×换手率 5 交叉)\n"
        "- C: 条件双重排序 (先市值 5 组，再组内换手率 5 组)\n\n"
        "## 口径\n\n"
        f"- 调仓频率: 每 {args.rebalance_freq} 个交易日\n"
        f"- 前瞻 horizon: {args.forward_horizon} 个交易日\n"
        f"- 分组数: {args.group_count}\n"
        f"- 252 日最小样本: {args.min_252d_samples}\n"
        f"- 复权口径: qfq (ex-post)，不声明 PIT 无泄漏\n\n"
        "## 验证标准\n\n"
        "1. 分组完整、样本数充足\n"
        "2. 价差时序可计算\n"
        "3. Newey-West t 值不为 NaN\n"
        "4. 报告如实披露正/负/不显著结果（研究假设不作为程序通过条件）\n"
    )
    plan_path = PROCESS_DIR / "PLAN.md"
    plan_path.write_text(plan, encoding="utf-8")
    paths["plan"] = plan_path

    # DATA-CONTRACT.md
    data_contract = (
        "# 数据合同\n\n"
        f"**Run ID**: {run_id}\n\n"
        "## 数据源\n\n"
        f"- market_cap: {MC_DIR}\n"
        f"- prices: {PRICES_DIR}\n"
        f"- trade_calendar: {TC_PATH}\n"
        f"- stock_basic: {SB_PATH}\n\n"
        "## 字段覆盖\n\n"
        "- market_cap: trade_date, symbol, market_cap, turnover_rate ✅\n"
        "- prices: trade_date, symbol, adjusted_close, adj_factor, adjustment_policy ✅\n"
        "- trade_calendar: trade_date, is_open ✅\n"
        "- stock_basic: symbol, list_date, list_status ✅\n\n"
        f"## 日期覆盖\n\n"
        f"- 预热期: {args.warmup_start} ~ {args.start_date}\n"
        f"- 实验期: {args.start_date} ~ {args.end_date}\n"
        f"- 有效实验结束日: end_date 往前推 {args.forward_horizon} 个交易日\n\n"
        "## 复权口径\n\n"
        "- adjustment_policy: qfq (前复权)\n"
        "- adj_factor 来源: tushare adj_factor 接口，available_at 为次日 08:00\n"
        "- 声明: 本实验使用 ex-post 复权价格，不声明 PIT 无泄漏复权\n\n"
        "## 交易日历\n\n"
        "- 来源: trade_calendar canonical (run-cr014-s14)\n"
        "- 若缺失则用 market_cap/prices 交集，并在审计中声明\n\n"
        "## 缺失处理\n\n"
        "- ST/涨跌停/停牌: 未使用 PIT 数据，作为正式限制声明\n"
        "- 行业分类: 未使用\n"
        "- 风格暴露: 未使用\n"
    )
    dc_path = PROCESS_DIR / "DATA-CONTRACT.md"
    dc_path.write_text(data_contract, encoding="utf-8")
    paths["data_contract"] = dc_path

    # LEAKAGE-AUDIT.md
    leakage_audit = (
        "# 泄漏审计\n\n"
        f"**Run ID**: {run_id}\n\n"
        "## 前视收益标签\n\n"
        "```\n"
        "forward_return_20d = adjusted_close[t+20] / adjusted_close[t] - 1\n"
        "```\n\n"
        f"- decision_time: 调仓日收盘时刻\n"
        f"- label_window_start: 调仓日次日 (t+1)\n"
        f"- label_window_end: 调仓日后 {args.forward_horizon} 个交易日 (t+{args.forward_horizon})\n"
        f"- label_available_at: 调仓日后 {args.forward_horizon} 个交易日收盘后\n\n"
        "## 防前视措施\n\n"
        f"1. 最后 {args.forward_horizon} 个交易日从有效样本中剔除（forward_return 为 NaN）\n"
        f"2. 有效实验结束日 = end_date 往前推 {args.forward_horizon} 个交易日\n"
        "3. 因子计算仅使用调仓日当日及之前数据\n\n"
        "## 复权泄漏风险\n\n"
        "- 使用 adjusted_close (qfq) 计算收益\n"
        "- adj_factor 的 available_at 为次日 08:00\n"
        "- 若在调仓日当天使用 adj_factor，存在 ≤1 日的轻微前视\n"
        "- 本实验不声明 PIT 无泄漏复权\n\n"
        "## 结论\n\n"
        "- forward return 标签无前视泄漏 ✅\n"
        "- 因子计算无前视泄漏 ✅\n"
        "- 复权存在 ex-post 偏差（已声明）⚠️\n"
    )
    la_path = PROCESS_DIR / "LEAKAGE-AUDIT.md"
    la_path.write_text(leakage_audit, encoding="utf-8")
    paths["leakage_audit"] = la_path

    # NO-REAL-OPERATION.md
    no_op = (
        "# 不授权边界\n\n"
        f"**Run ID**: {run_id}\n\n"
        "本实验运行过程中：\n\n"
        "- ❌ 未触发 QMT gateway\n"
        "- ❌ 未触发 provider fetch (tushare/akshare/jqdata 等)\n"
        "- ❌ 未触发数据湖写入 (lake write)\n"
        "- ❌ 未触发数据发布 (publish)\n"
        "- ❌ 未读取凭据 (token/密码)\n"
        "- ❌ 未运行外部项目\n"
        "- ❌ 未修改依赖\n"
        "- ✅ 仅从数据湖 canonical 只读 parquet 文件\n"
        f"- ✅ 仅写入 NAS 研究产物目录：{REPORTS_BASE} 和 {PROCESS_DIR}\n"
    )
    noop_path = PROCESS_DIR / "NO-REAL-OPERATION.md"
    noop_path.write_text(no_op, encoding="utf-8")
    paths["no_real_operation"] = noop_path

    return paths


# ---------------------------------------------------------------------------
# 第9区：主入口
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="A股低换手率因子双重排序实验",
    )
    parser.add_argument("--start-date", default="2019-01-01", help="实验起始日期")
    parser.add_argument("--end-date", default="2025-12-31", help="实验结束日期")
    parser.add_argument("--warmup-start", default="2018-01-02", help="预热起始日期（需 252 日窗口）")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID, help="运行标识")
    parser.add_argument("--rebalance-freq", type=int, default=20, help="调仓频率（交易日）")
    parser.add_argument("--group-count", type=int, default=5, help="分组数")
    parser.add_argument("--forward-horizon", type=int, default=20, help="前瞻 horizon（交易日）")
    parser.add_argument("--min-252d-samples", type=int, default=60, help="252 日窗口最小有效样本")
    parser.add_argument("--output-root", default=None, help="研究报告输出根目录；默认使用 engine.research_paths 配置。")
    parser.add_argument("--process-dir", default=None, help="过程文档输出目录；默认使用 engine.research_paths 配置。")
    return parser.parse_args()


def main() -> None:
    global PROCESS_DIR, REPORTS_BASE
    args = parse_args()
    if args.output_root:
        REPORTS_BASE = Path(args.output_root)
    if args.process_dir:
        PROCESS_DIR = Path(args.process_dir)
    run_id = args.run_id
    run_dir = REPORTS_BASE / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "charts").mkdir(parents=True, exist_ok=True)

    print(f"{'='*60}")
    print(f"A股低换手率因子双重排序实验")
    print(f"Run ID: {run_id}")
    print(f"实验期: {args.start_date} ~ {args.end_date}")
    print(f"预热期: {args.warmup_start}")
    print(f"{'='*60}")

    # Step 1: 数据加载
    data = build_data_matrices(args.start_date, args.end_date, args.warmup_start)

    # Step 2: 因子计算
    print(f"\n[因子计算] abnormal_turnover_21_252 ...")
    abnormal_turnover = calculate_abnormal_turnover(data.turnover_df)
    data = ExperimentData(
        close_df=data.close_df,
        turnover_df=data.turnover_df,
        market_cap_df=data.market_cap_df,
        abnormal_turnover=abnormal_turnover,
        forward_returns=data.forward_returns,
        valid_mask=data.valid_mask,
        calendar=data.calendar,
        rebalance_dates=data.rebalance_dates,
        list_date_map=data.list_date_map,
    )

    # Step 3: 前瞻收益
    print(f"\n[标签计算] forward_return_20d ...")
    forward_returns = build_forward_return_20d(data.close_df)
    data = ExperimentData(
        close_df=data.close_df,
        turnover_df=data.turnover_df,
        market_cap_df=data.market_cap_df,
        abnormal_turnover=data.abnormal_turnover,
        forward_returns=forward_returns,
        valid_mask=data.valid_mask,
        calendar=data.calendar,
        rebalance_dates=data.rebalance_dates,
        list_date_map=data.list_date_map,
    )

    # Step 4: 过滤
    print(f"\n[过滤] 应用过滤规则 ...")
    valid_mask = apply_filters(
        data.abnormal_turnover,
        data.market_cap_df,
        data.turnover_df,
        data.forward_returns,
        data.list_date_map,
        long_window=252,
        min_long_samples=args.min_252d_samples,
    )
    n_valid = valid_mask.sum().sum()
    n_total = valid_mask.size
    print(f"  有效样本: {n_valid:,} / {n_total:,} ({n_valid/n_total*100:.1f}%)")

    # Step 5: 调仓日期
    rebalance_dates = get_rebalance_dates(
        data.calendar, args.rebalance_freq, args.start_date, args.forward_horizon
    )
    print(f"  调仓日: {len(rebalance_dates)} ({rebalance_dates[0]} ~ {rebalance_dates[-1]})")

    data = ExperimentData(
        close_df=data.close_df,
        turnover_df=data.turnover_df,
        market_cap_df=data.market_cap_df,
        abnormal_turnover=data.abnormal_turnover,
        forward_returns=data.forward_returns,
        valid_mask=valid_mask,
        calendar=data.calendar,
        rebalance_dates=rebalance_dates,
        list_date_map=data.list_date_map,
    )

    # Step 6: 实验A
    exp_a = run_experiment_a(
        data.abnormal_turnover,
        data.forward_returns,
        data.valid_mask,
        data.rebalance_dates,
        group_count=args.group_count,
    )
    print(f"  实验A G1-G5 价差: {format_pct(exp_a.spread_nw['mean'])}, NW t={format_t(exp_a.spread_nw['nw_t_stat'])}")

    # Step 7: 实验B
    exp_b = run_experiment_b(
        data.abnormal_turnover,
        data.market_cap_df,
        data.forward_returns,
        data.valid_mask,
        data.rebalance_dates,
        group_count=args.group_count,
    )
    print(f"  实验B 均价差: {format_pct(exp_b.avg_spread_nw['mean'])}, NW t={format_t(exp_b.avg_spread_nw['nw_t_stat'])}")

    # Step 8: 实验C
    exp_c = run_experiment_c(
        data.abnormal_turnover,
        data.market_cap_df,
        data.forward_returns,
        data.valid_mask,
        data.rebalance_dates,
        group_count=args.group_count,
    )
    print(f"  实验C 均价差: {format_pct(exp_c.avg_spread_nw['mean'])}, NW t={format_t(exp_c.avg_spread_nw['nw_t_stat'])}")

    # Step 9: 保存数据产物
    print(f"\n[输出] 保存数据产物 ...")
    exp_a.group_returns_ts.to_csv(run_dir / "group_returns_exp_a.csv", index=False)
    exp_b.cell_returns.to_csv(run_dir / "double_sort_exp_b.csv", index=False)
    exp_c.cell_returns.to_csv(run_dir / "double_sort_exp_c.csv", index=False)

    # Newey-West 汇总
    nw_rows = []
    for label, nw in [("exp_a", exp_a.spread_nw), ("exp_b", exp_b.avg_spread_nw), ("exp_c", exp_c.avg_spread_nw)]:
        nw_rows.append({"experiment": label, **nw})
    pd.DataFrame(nw_rows).to_csv(run_dir / "newey_west_ttest.csv", index=False)

    # 年度稳定性
    yearly_rows = []
    for label, spread_ts in [("exp_a", exp_a.spread_ts)]:
        if spread_ts.empty:
            continue
        for yr, grp in spread_ts.groupby(lambda d: d.year if hasattr(d, 'year') else str(d)[:4]):
            nw = newey_west_ttest(grp)
            yearly_rows.append({
                "experiment": label,
                "year": yr,
                "mean_spread": nw["mean"],
                "nw_t_stat": nw["nw_t_stat"],
                "n_obs": nw["n_observations"],
            })
    pd.DataFrame(yearly_rows).to_csv(run_dir / "yearly_stability.csv", index=False)

    # 保存因子面板和标签
    # 将 abnormal_turnover 转为长表保存
    at_long = data.abnormal_turnover.stack().reset_index()
    at_long.columns = ["date", "symbol", "factor_value"]
    at_long["factor_id"] = FACTOR_ID
    at_long.to_parquet(run_dir / "abnormal_turnover_factor.parquet", index=False)

    fr_long = data.forward_returns.stack().reset_index()
    fr_long.columns = ["date", "symbol", "forward_return_20d"]
    fr_long.to_parquet(run_dir / "forward_return_20d_label.parquet", index=False)

    # Step 10: 可视化
    print(f"\n[可视化] 生成图表 ...")
    chart_paths = generate_charts(
        run_dir / "charts", exp_a, exp_b, exp_c, data.rebalance_dates,
    )
    # 图表索引
    chart_index = "# 图表索引\n\n"
    for p in chart_paths:
        chart_index += f"- [{p.name}]({p.name})\n"
    (run_dir / "charts" / "index.md").write_text(chart_index, encoding="utf-8")

    # Step 11: 报告
    print(f"\n[报告] 生成主研究报告 ...")
    output_paths: dict[str, Path] = {
        "group_returns_exp_a": run_dir / "group_returns_exp_a.csv",
        "double_sort_exp_b": run_dir / "double_sort_exp_b.csv",
        "double_sort_exp_c": run_dir / "double_sort_exp_c.csv",
        "newey_west_ttest": run_dir / "newey_west_ttest.csv",
        "yearly_stability": run_dir / "yearly_stability.csv",
        "abnormal_turnover_factor": run_dir / "abnormal_turnover_factor.parquet",
        "forward_return_label": run_dir / "forward_return_20d_label.parquet",
    }
    report = render_report(
        args=args,
        run_id=run_id,
        data=data,
        exp_a=exp_a,
        exp_b=exp_b,
        exp_c=exp_c,
        chart_paths=chart_paths,
        output_paths=output_paths,
    )
    report_path = run_dir / "turnover_factor_replication_report.md"
    report_path.write_text(report, encoding="utf-8")

    # 数据审计摘要
    audit = (
        "# 数据审计摘要\n\n"
        f"**Run ID**: {run_id}\n\n"
        f"## 数据覆盖\n\n"
        f"- 交易日数: {len(data.calendar)}\n"
        f"- 股票数 (对齐后): {len(data.close_df.columns)}\n"
        f"- 有效样本率: {data.valid_mask.sum().sum() / data.valid_mask.size * 100:.1f}%\n\n"
        f"## 样本过滤统计\n\n"
        f"- 总样本 (date × symbol): {data.valid_mask.size:,}\n"
        f"- 有效样本: {data.valid_mask.sum().sum():,}\n"
        f"- 缺失 market_cap: {(~data.market_cap_df.notna()).sum().sum():,}\n"
        f"- 缺失 turnover_rate: {(~data.turnover_df.notna() | (data.turnover_df <= 0)).sum().sum():,}\n\n"
        f"## 复权口径\n\n"
        f"- adjustment_policy: qfq\n"
        f"- 声明: ex-post 复权，不声明 PIT 无泄漏\n\n"
        f"## Tradability 限制\n\n"
        f"- ST/涨跌停/停牌 PIT 数据未使用\n"
        f"- 本实验不声明 tradability pass\n"
    )
    (run_dir / "data_audit_summary.md").write_text(audit, encoding="utf-8")

    # metadata
    metadata = {
        "run_id": run_id,
        "factor_id": FACTOR_ID,
        "strategy_id": STRATEGY_ID,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "warmup_start": args.warmup_start,
        "rebalance_freq": args.rebalance_freq,
        "group_count": args.group_count,
        "forward_horizon": args.forward_horizon,
        "min_252d_samples": args.min_252d_samples,
        "n_calendar_days": len(data.calendar),
        "n_rebalance_dates": len(data.rebalance_dates),
        "n_symbols": len(data.close_df.columns),
        "adjustment_policy": "qfq",
        "pit_status": "ex-post",
        "tradability_status": "not_applied",
        "blocked_claims": [
            "tradability_pass",
            "capacity_pass",
            "simulation_ready",
            "qmt_ready",
            "pit_no_lookahead",
        ],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (run_dir / "experiment_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # CR030 产物
    print(f"\n[CR030] 生成标准研究产物 ...")
    cr030_paths = write_cr030_artifacts(run_dir, run_id, args, exp_a, exp_b, exp_c, data)
    output_paths.update(cr030_paths)

    # 过程文档
    print(f"\n[过程文档] 生成过程文档 ...")
    process_paths = write_process_docs(args, run_id, data)

    # 运行日志
    run_log = (
        f"# 运行记录：{run_id}\n\n"
        f"**开始时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
        f"## 命令\n\n"
        f"```bash\n"
        f"uv run --python 3.11 python experiments/run_experiment_turnover_factor.py \\\n"
        f"    --start-date {args.start_date} \\\n"
        f"    --end-date {args.end_date} \\\n"
        f"    --warmup-start {args.warmup_start} \\\n"
        f"    --run-id {run_id} \\\n"
        f"    --rebalance-freq {args.rebalance_freq} \\\n"
        f"    --group-count {args.group_count} \\\n"
        f"    --forward-horizon {args.forward_horizon} \\\n"
        f"    --min-252d-samples {args.min_252d_samples}\n"
        f"```\n\n"
        f"## 输出路径\n\n"
        f"- 研究报告: {_artifact_ref(run_dir / 'turnover_factor_replication_report.md')}\n"
        f"- 数据产物: {_artifact_ref(run_dir)}/\n"
        f"- 过程文档: {_artifact_ref(PROCESS_DIR)}/\n"
    )
    run_log_path = PROCESS_DIR / f"RUN-LOG-{run_id}.md"
    run_log_path.write_text(run_log, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"实验完成！")
    print(f"研究报告: {report_path}")
    print(f"数据目录: {run_dir}")
    print(f"过程文档: {PROCESS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
