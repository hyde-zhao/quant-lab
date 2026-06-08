"""《因子投资：方法与实践》第三章 A 股因子复刻工具。

本模块只处理调用方传入的离线 DataFrame，不读取凭据、不触发 provider、
不写 lake、不 publish，也不连接 QMT / simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


CHAPTER3_FACTOR_SCHEMA = "chapter3_factor_replication_v1"
CHAPTER3_AUDIT_SCHEMA = "chapter3_data_issue_audit_v1"

STATUS_COVERED = "covered"
STATUS_PARTIAL = "partial"
STATUS_MISSING = "missing"

DEFAULT_FACTOR_IDS = (
    "market_beta_252",
    "size_total_market_cap",
    "value_bm",
    "momentum_12_1",
    "profitability_roe_ttm",
    "investment_asset_growth",
    "abnormal_turnover_21_252",
)


@dataclass(frozen=True, slots=True)
class Chapter3DataAuditItem:
    issue_id: str
    requirement: str
    status: str
    evidence_fields: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Chapter3FactorDefinition:
    factor_id: str
    book_name: str
    raw_variable: str
    direction: str
    required_inputs: tuple[str, ...]
    formula: str
    chapter_section: str
    implementation_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Chapter3FactorReplicationResult:
    factor_definitions: tuple[Chapter3FactorDefinition, ...]
    raw_matrices: dict[str, pd.DataFrame]
    directional_matrices: dict[str, pd.DataFrame]
    winsorized_matrices: dict[str, pd.DataFrame]
    zscore_matrices: dict[str, pd.DataFrame]
    market_factor_return: pd.Series
    preprocessing_summary: pd.DataFrame
    limitations: tuple[str, ...]
    schema_version: str = CHAPTER3_FACTOR_SCHEMA


def chapter3_factor_definitions() -> tuple[Chapter3FactorDefinition, ...]:
    return (
        Chapter3FactorDefinition(
            factor_id="market_beta_252",
            book_name="市场因子",
            raw_variable="滚动 252 日市场 beta",
            direction="neutral",
            required_inputs=("prices.adjusted_close|close", "market_cap.market_cap 可选"),
            formula="cov(stock_return, market_return) / var(market_return)",
            chapter_section="3.2",
            implementation_note="市场组合收益单独输出为 market_factor_return；beta 仅用于复刻第三章 CAPM 截面检验。",
        ),
        Chapter3FactorDefinition(
            factor_id="size_total_market_cap",
            book_name="规模因子",
            raw_variable="总市值",
            direction="negative",
            required_inputs=("market_cap.market_cap",),
            formula="-log(total_market_cap)",
            chapter_section="3.3",
            implementation_note="书中做多小市值、做空大市值；打分方向统一为值越大越看多。",
        ),
        Chapter3FactorDefinition(
            factor_id="value_bm",
            book_name="价值因子",
            raw_variable="BM",
            direction="positive",
            required_inputs=("financials.book_equity 或 prices/book_to_market", "market_cap.market_cap"),
            formula="book_equity / total_market_cap",
            chapter_section="3.4",
        ),
        Chapter3FactorDefinition(
            factor_id="momentum_12_1",
            book_name="动量因子",
            raw_variable="过去 12 到 1 个月累计收益",
            direction="positive",
            required_inputs=("prices.adjusted_close|close",),
            formula="close[t-21] / close[t-252] - 1",
            chapter_section="3.5",
            implementation_note="用日频近似月频，排除最近 21 个交易日。",
        ),
        Chapter3FactorDefinition(
            factor_id="profitability_roe_ttm",
            book_name="盈利因子",
            raw_variable="ROE(TTM)",
            direction="positive",
            required_inputs=("financials.roe_ttm 或 operating_profit_ttm/book_equity",),
            formula="operating_profit_ttm / book_equity",
            chapter_section="3.6",
        ),
        Chapter3FactorDefinition(
            factor_id="investment_asset_growth",
            book_name="投资因子",
            raw_variable="总资产增长率",
            direction="negative",
            required_inputs=("financials.total_assets",),
            formula="-(total_assets / lag_annual_total_assets - 1)",
            chapter_section="3.7",
            implementation_note="书中低投资减高投资；打分方向统一为低投资更高分。",
        ),
        Chapter3FactorDefinition(
            factor_id="abnormal_turnover_21_252",
            book_name="换手率因子",
            raw_variable="异常换手率",
            direction="negative",
            required_inputs=("market_cap.turnover_rate 或 prices.turnover_rate",),
            formula="-(mean(turnover_rate, 21) / mean(turnover_rate, 252))",
            chapter_section="3.8",
            implementation_note="书中做多低异常换手率、做空高异常换手率。",
        ),
    )


def audit_chapter3_data_issues(frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    prices = _frame(frames, "prices")
    market_cap = _frame(frames, "market_cap")
    financials = _first_frame(frames, ("financials", "finance", "fundamentals", "income", "balance"))
    trade_status = _first_frame(frames, ("trade_status", "tradability", "suspend"))
    prices_limit = _first_frame(frames, ("prices_limit", "limit", "limits"))
    stock_basic = _first_frame(frames, ("stock_basic", "events", "lifecycle", "index_members"))

    items = [
        _audit_item(
            "C3-DATA-01",
            "量价数据应使用复权价格计算收益，并保留复权政策和可用时间。",
            _columns(prices),
            any_of=("adjusted_close", "hfq_close", "qfq_close", "close"),
            recommended=("adj_factor", "adjustment_policy", "available_at"),
        ),
        _audit_item(
            "C3-DATA-02",
            "长期停牌复牌等异常日收益应可识别或可压缩。",
            _columns(prices),
            any_of=("return", "pct_chg", "pct_change"),
            recommended=("limit_up", "limit_down", "is_suspended", "trade_status"),
            auxiliary_columns=_columns(trade_status) | _columns(prices_limit),
        ),
        _audit_item(
            "C3-DATA-03",
            "停牌日应能按指标场景选择填充或置缺失，波动率/beta 不应被停牌 0 收益污染。",
            _columns(prices) | _columns(trade_status),
            any_of=("is_suspended", "suspend_type", "trade_status"),
            recommended=("volume", "amount"),
        ),
        _audit_item(
            "C3-DATA-04",
            "滚动窗口指标应执行最少有效交易日规则，建议不少于窗口的三分之二。",
            _columns(prices),
            required=("trade_date", "symbol"),
            recommended=("is_suspended", "trade_status"),
            note="本模块的滚动因子按 2/3 min_periods 计算；项目级 runner 仍需把该策略写入 run metadata。",
        ),
        _audit_item(
            "C3-FIN-01",
            "财务数据应区分报告期、公告/可用时间，避免未来函数。",
            _columns(financials),
            any_of=("available_at", "ann_date", "publish_date"),
            recommended=("report_period", "end_date", "statement_type", "update_flag"),
        ),
        _audit_item(
            "C3-FIN-02",
            "财务调整/更正应遵循 point-in-time 原则，而不是直接使用最终修订值。",
            _columns(financials),
            any_of=("available_at", "ann_date", "publish_date"),
            recommended=("statement_type", "update_flag", "report_type", "is_adjusted", "is_restated"),
        ),
        _audit_item(
            "C3-FIN-03",
            "盈利因子应支持 TTM 或可由单季度/累计值构造 TTM。",
            _columns(financials),
            any_of=("roe_ttm", "operating_profit_ttm", "net_profit_ttm"),
            recommended=("quarter", "report_period", "total_assets", "book_equity"),
        ),
        _audit_item(
            "C3-UNIV-01",
            "股票池应能处理退市/ST/净资产为负/上市不足一年次新股黑名单。",
            _columns(stock_basic) | _columns(financials),
            any_of=("list_date", "list_status", "is_st", "st_status", "delist_date", "book_equity"),
            recommended=("net_assets", "total_equity", "is_new_stock"),
        ),
        _audit_item(
            "C3-TRADE-01",
            "月末调仓应能剔除停牌、一字涨停、一字跌停等不可交易股票。",
            _columns(prices) | _columns(trade_status) | _columns(prices_limit),
            any_of=("is_suspended", "limit_up", "limit_down", "up_limit", "down_limit"),
            recommended=("open", "high", "low", "close", "trade_status"),
        ),
        _audit_item(
            "C3-PREP-01",
            "因子截面应支持 1%/99% 缩尾、标准化和中性化审计。",
            set(),
            required=(),
            recommended=(),
            note="CR030 合同已有 winsorized/zscore 层；本模块实现 winsorize/zscore，但行业/市值中性化由组合或后续 runner 处理。",
        ),
        _audit_item(
            "C3-TEST-01",
            "因子检验应支持十分组、5x5 市值双重排序、月末调仓和 t 值。",
            set(),
            required=(),
            recommended=(),
            note="本模块提供十分组和 5x5 独立双重排序；Newey-West/Fama-MacBeth 可接后续统计模块扩展。",
        ),
    ]
    return pd.DataFrame([item.to_dict() for item in items])


def replicate_chapter3_factors(
    prices: pd.DataFrame,
    *,
    market_cap: pd.DataFrame | None = None,
    financials: pd.DataFrame | None = None,
    trade_calendar: pd.DataFrame | Sequence[Any] | None = None,
    factor_ids: Sequence[str] = DEFAULT_FACTOR_IDS,
    winsor_limits: tuple[float, float] = (0.01, 0.99),
    min_period_ratio: float = 2.0 / 3.0,
    min_cross_section: int = 5,
) -> Chapter3FactorReplicationResult:
    if not 0 <= winsor_limits[0] < winsor_limits[1] <= 1:
        raise ValueError("winsor_limits 必须满足 0 <= lower < upper <= 1")
    if not 0 < min_period_ratio <= 1:
        raise ValueError("min_period_ratio 必须在 (0, 1] 内")
    if min_cross_section < 2:
        raise ValueError("min_cross_section 必须至少为 2")

    price_frame = _normalise_long_frame(prices, required=("trade_date", "symbol"))
    close_column = _first_existing(price_frame, ("adjusted_close", "hfq_close", "qfq_close", "close"))
    if close_column is None:
        raise ValueError("prices 缺少 adjusted_close/hfq_close/qfq_close/close 字段")
    close = _pivot_numeric(price_frame, close_column, trade_calendar=trade_calendar)
    symbols = tuple(str(item) for item in close.columns)
    calendar = list(close.index)

    market_cap_matrix = _optional_matrix(market_cap, ("market_cap", "total_market_cap", "circ_mv"), calendar, symbols)
    turnover_matrix = _turnover_matrix(price_frame, market_cap, calendar, symbols)
    financial_daily = _build_financial_daily(financials, calendar, symbols)

    returns = close.pct_change(fill_method=None)
    market_factor_return = _market_return(returns, market_cap_matrix)

    raw: dict[str, pd.DataFrame] = {}
    limitations: list[str] = []
    requested = set(factor_ids)

    if "market_beta_252" in requested:
        raw["market_beta_252"] = _rolling_beta(returns, market_factor_return, window=252, min_period_ratio=min_period_ratio)
    if "size_total_market_cap" in requested:
        if market_cap_matrix is None:
            limitations.append("size_total_market_cap 缺 market_cap，无法复刻。")
        else:
            raw["size_total_market_cap"] = np.log(market_cap_matrix.where(market_cap_matrix > 0))
    if "value_bm" in requested:
        bm = _bm_matrix(price_frame, market_cap_matrix, financial_daily, calendar, symbols)
        if bm is None:
            limitations.append("value_bm 缺 book_equity/book_to_market 或 market_cap，无法复刻。")
        else:
            raw["value_bm"] = bm
    if "momentum_12_1" in requested:
        raw["momentum_12_1"] = close.shift(21) / close.shift(252) - 1.0
    if "profitability_roe_ttm" in requested:
        roe = _roe_ttm_matrix(financial_daily)
        if roe is None:
            limitations.append("profitability_roe_ttm 缺 roe_ttm 或 operating_profit_ttm/book_equity，无法复刻。")
        else:
            raw["profitability_roe_ttm"] = roe
    if "investment_asset_growth" in requested:
        inv = _asset_growth_matrix(financial_daily)
        if inv is None:
            limitations.append("investment_asset_growth 缺 total_assets/asset_growth，无法复刻。")
        else:
            raw["investment_asset_growth"] = inv
    if "abnormal_turnover_21_252" in requested:
        if turnover_matrix is None:
            limitations.append("abnormal_turnover_21_252 缺 turnover_rate，无法复刻。")
        else:
            short_window = _window_min_periods(21, min_period_ratio)
            long_window = _window_min_periods(252, min_period_ratio)
            raw["abnormal_turnover_21_252"] = (
                turnover_matrix.rolling(21, min_periods=short_window).mean()
                / turnover_matrix.rolling(252, min_periods=long_window).mean()
            )

    definitions = tuple(item for item in chapter3_factor_definitions() if item.factor_id in requested)
    direction_by_factor = {item.factor_id: item.direction for item in definitions}
    directional = {
        factor_id: _apply_direction(matrix, direction_by_factor.get(factor_id, "positive"))
        for factor_id, matrix in raw.items()
    }
    winsorized, zscores, summary = _preprocess(directional, winsor_limits=winsor_limits, min_cross_section=min_cross_section)

    return Chapter3FactorReplicationResult(
        factor_definitions=definitions,
        raw_matrices=raw,
        directional_matrices=directional,
        winsorized_matrices=winsorized,
        zscore_matrices=zscores,
        market_factor_return=market_factor_return,
        preprocessing_summary=summary,
        limitations=tuple(limitations),
    )


def factor_matrices_to_panel(
    result: Chapter3FactorReplicationResult,
    *,
    source_dataset: str = "research_input_v1",
    factor_version: str = "chapter3-v1",
    quality_status: str = "pass",
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for factor_id, raw in result.raw_matrices.items():
        directional = result.directional_matrices[factor_id]
        winsorized = result.winsorized_matrices[factor_id]
        zscore = result.zscore_matrices[factor_id]
        for value_name, matrix in (
            ("raw_value", raw),
            ("directional_value", directional),
            ("winsorized_value", winsorized),
            ("zscore_value", zscore),
        ):
            long = _stack_matrix(matrix, value_name)
            long.columns = ["trade_date", "symbol", value_name]
            if value_name == "raw_value":
                merged = long
            else:
                merged = merged.merge(long, on=["trade_date", "symbol"], how="left")
        merged["factor_id"] = factor_id
        merged["factor_version"] = factor_version
        merged["source_dataset"] = source_dataset
        merged["quality_status"] = quality_status
        rows.append(merged)
    if not rows:
        return pd.DataFrame(
            columns=[
                "trade_date",
                "symbol",
                "raw_value",
                "directional_value",
                "winsorized_value",
                "zscore_value",
                "factor_id",
                "factor_version",
                "source_dataset",
                "quality_status",
            ]
        )
    return pd.concat(rows, ignore_index=True)


def build_forward_return_matrix(close: pd.DataFrame, *, horizon: int) -> pd.DataFrame:
    if horizon <= 0:
        raise ValueError("horizon 必须为正数")
    return close.shift(-horizon) / close - 1.0


def single_sort_returns(
    factor: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    quantiles: int = 10,
    min_cross_section: int = 10,
) -> pd.DataFrame:
    if quantiles < 2:
        raise ValueError("quantiles 必须至少为 2")
    rows: list[dict[str, Any]] = []
    for trade_date in factor.index.intersection(forward_returns.index):
        valid = pd.DataFrame({"factor": factor.loc[trade_date], "forward_return": forward_returns.loc[trade_date]}).dropna()
        if len(valid) < max(quantiles, min_cross_section):
            continue
        valid["group"] = _quantile_groups(valid["factor"], quantiles)
        for group_id, group in valid.dropna(subset=["group"]).groupby("group", sort=True):
            rows.append(
                {
                    "trade_date": _iso_date(trade_date),
                    "group": int(group_id),
                    "mean_forward_return": float(group["forward_return"].mean()),
                    "symbol_count": int(len(group)),
                }
            )
    return pd.DataFrame(rows)


def independent_double_sort_returns(
    factor: pd.DataFrame,
    size: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    groups: int = 5,
    min_cross_section: int = 25,
) -> pd.DataFrame:
    if groups < 2:
        raise ValueError("groups 必须至少为 2")
    rows: list[dict[str, Any]] = []
    common_dates = factor.index.intersection(size.index).intersection(forward_returns.index)
    for trade_date in common_dates:
        valid = pd.DataFrame(
            {
                "factor": factor.loc[trade_date],
                "size": size.loc[trade_date],
                "forward_return": forward_returns.loc[trade_date],
            }
        ).dropna()
        if len(valid) < min_cross_section:
            continue
        valid["size_group"] = _quantile_groups(valid["size"], groups)
        valid["factor_group"] = _quantile_groups(valid["factor"], groups)
        valid = valid.dropna(subset=["size_group", "factor_group"])
        for (size_group, factor_group), group in valid.groupby(["size_group", "factor_group"], sort=True):
            rows.append(
                {
                    "trade_date": _iso_date(trade_date),
                    "size_group": int(size_group),
                    "factor_group": int(factor_group),
                    "mean_forward_return": float(group["forward_return"].mean()),
                    "symbol_count": int(len(group)),
                }
            )
    return pd.DataFrame(rows)


def long_short_summary(group_returns: pd.DataFrame, *, high_minus_low: bool = True) -> dict[str, Any]:
    if group_returns.empty:
        return {"status": "missing", "mean": None, "t_stat": None, "observation_count": 0}
    pivot = group_returns.pivot_table(index="trade_date", columns="group", values="mean_forward_return", aggfunc="mean")
    if pivot.empty:
        return {"status": "missing", "mean": None, "t_stat": None, "observation_count": 0}
    low = int(min(pivot.columns))
    high = int(max(pivot.columns))
    spread = pivot[high] - pivot[low] if high_minus_low else pivot[low] - pivot[high]
    spread = spread.dropna()
    return {
        "status": "pass" if not spread.empty else "missing",
        "mean": _safe_float(spread.mean()) if not spread.empty else None,
        "t_stat": _t_stat(spread),
        "observation_count": int(len(spread)),
    }


def _audit_item(
    issue_id: str,
    requirement: str,
    columns: set[str],
    *,
    required: Sequence[str] = (),
    any_of: Sequence[str] = (),
    recommended: Sequence[str] = (),
    auxiliary_columns: set[str] | None = None,
    note: str = "",
) -> Chapter3DataAuditItem:
    all_columns = set(columns) | set(auxiliary_columns or set())
    required_missing = tuple(field for field in required if field not in all_columns)
    any_present = not any_of or any(field in all_columns for field in any_of)
    recommended_missing = tuple(field for field in recommended if field not in all_columns)
    evidence = tuple(sorted(field for field in set(required) | set(any_of) | set(recommended) if field in all_columns))
    if required_missing or not any_present:
        status = STATUS_MISSING
    elif recommended_missing:
        status = STATUS_PARTIAL
    else:
        status = STATUS_COVERED
    missing = required_missing + (() if any_present else tuple(any_of)) + recommended_missing
    if not required and not any_of and not recommended:
        status = STATUS_COVERED if "本模块" in note or "CR030" in note else STATUS_PARTIAL
    return Chapter3DataAuditItem(issue_id, requirement, status, evidence, tuple(dict.fromkeys(missing)), note)


def _frame(frames: Mapping[str, pd.DataFrame], name: str) -> pd.DataFrame | None:
    frame = frames.get(name)
    return frame if isinstance(frame, pd.DataFrame) else None


def _first_frame(frames: Mapping[str, pd.DataFrame], names: Sequence[str]) -> pd.DataFrame | None:
    for name in names:
        frame = _frame(frames, name)
        if frame is not None:
            return frame
    return None


def _columns(frame: pd.DataFrame | None) -> set[str]:
    return set() if frame is None else {str(item) for item in frame.columns}


def _normalise_long_frame(frame: pd.DataFrame, *, required: Sequence[str]) -> pd.DataFrame:
    missing = [field for field in required if field not in frame.columns]
    if missing:
        raise ValueError("缺少必需字段: " + ", ".join(missing))
    work = frame.copy()
    work["trade_date"] = pd.to_datetime(work["trade_date"]).dt.date
    work["symbol"] = work["symbol"].astype("string").str.strip()
    work = work.dropna(subset=["trade_date", "symbol"])
    return work


def _first_existing(frame: pd.DataFrame, columns: Sequence[str]) -> str | None:
    for column in columns:
        if column in frame.columns:
            return column
    return None


def _pivot_numeric(
    frame: pd.DataFrame,
    value_column: str,
    *,
    trade_calendar: pd.DataFrame | Sequence[Any] | None = None,
    symbols: Sequence[str] | None = None,
) -> pd.DataFrame:
    work = frame.copy()
    work[value_column] = pd.to_numeric(work[value_column], errors="coerce")
    matrix = work.pivot_table(index="trade_date", columns="symbol", values=value_column, aggfunc="last")
    calendar = _calendar_index(trade_calendar)
    if calendar:
        matrix = matrix.reindex(index=calendar)
    if symbols is not None:
        matrix = matrix.reindex(columns=list(symbols))
    matrix = matrix.sort_index()
    matrix.columns = [str(column) for column in matrix.columns]
    return matrix


def _calendar_index(trade_calendar: pd.DataFrame | Sequence[Any] | None) -> list[date]:
    if trade_calendar is None:
        return []
    if isinstance(trade_calendar, pd.DataFrame):
        if "trade_date" not in trade_calendar.columns:
            return []
        work = trade_calendar.copy()
        if "is_open" in work.columns:
            work = work[work["is_open"].astype(bool)]
        values = work["trade_date"].tolist()
    else:
        values = list(trade_calendar)
    return sorted({pd.Timestamp(item).date() for item in values if pd.notna(item)})


def _optional_matrix(
    frame: pd.DataFrame | None,
    columns: Sequence[str],
    calendar: Sequence[Any],
    symbols: Sequence[str],
) -> pd.DataFrame | None:
    if frame is None:
        return None
    work = _normalise_long_frame(frame, required=("trade_date", "symbol"))
    column = _first_existing(work, columns)
    if column is None:
        return None
    return _pivot_numeric(work, column, trade_calendar=list(calendar), symbols=symbols)


def _turnover_matrix(
    price_frame: pd.DataFrame,
    market_cap: pd.DataFrame | None,
    calendar: Sequence[Any],
    symbols: Sequence[str],
) -> pd.DataFrame | None:
    column = _first_existing(price_frame, ("turnover_rate", "turnover", "turnover_rate_f"))
    if column is not None:
        return _pivot_numeric(price_frame, column, trade_calendar=list(calendar), symbols=symbols)
    return _optional_matrix(market_cap, ("turnover_rate", "turnover", "turnover_rate_f"), calendar, symbols)


def _build_financial_daily(
    financials: pd.DataFrame | None,
    calendar: Sequence[Any],
    symbols: Sequence[str],
) -> dict[str, pd.DataFrame]:
    if financials is None or financials.empty:
        return {}
    work = financials.copy()
    if "symbol" not in work.columns:
        return {}
    available_column = _first_existing(work, ("available_at", "ann_date", "publish_date", "trade_date"))
    if available_column is None:
        return {}
    work["available_date"] = pd.to_datetime(work[available_column]).dt.date
    work["symbol"] = work["symbol"].astype("string").str.strip()
    work = work.dropna(subset=["available_date", "symbol"]).sort_values(["symbol", "available_date"])
    result: dict[str, pd.DataFrame] = {}
    value_columns = [
        column
        for column in work.columns
        if column not in {"trade_date", "available_at", "ann_date", "publish_date", "available_date", "symbol"}
    ]
    for column in value_columns:
        work[column] = pd.to_numeric(work[column], errors="coerce")
        matrix = work.pivot_table(index="available_date", columns="symbol", values=column, aggfunc="last")
        matrix = matrix.reindex(index=list(calendar), columns=list(symbols)).sort_index().ffill()
        result[column] = matrix
    return result


def _market_return(returns: pd.DataFrame, market_cap: pd.DataFrame | None) -> pd.Series:
    if market_cap is None:
        return returns.mean(axis=1, skipna=True).rename("market_return")
    weights = market_cap.shift(1).reindex_like(returns)
    weights = weights.where(weights > 0)
    weighted = returns * weights
    return (weighted.sum(axis=1, skipna=True) / weights.where(returns.notna()).sum(axis=1, skipna=True)).rename("market_return")


def _rolling_beta(
    returns: pd.DataFrame,
    market_return: pd.Series,
    *,
    window: int,
    min_period_ratio: float,
) -> pd.DataFrame:
    min_periods = _window_min_periods(window, min_period_ratio)
    market = market_return.reindex(returns.index)
    variance = market.rolling(window, min_periods=min_periods).var(ddof=0)
    beta = pd.DataFrame(index=returns.index, columns=returns.columns, dtype="float64")
    for symbol in returns.columns:
        covariance = returns[symbol].rolling(window, min_periods=min_periods).cov(market, ddof=0)
        beta[symbol] = covariance / variance
    return beta


def _bm_matrix(
    price_frame: pd.DataFrame,
    market_cap: pd.DataFrame | None,
    financial_daily: Mapping[str, pd.DataFrame],
    calendar: Sequence[Any],
    symbols: Sequence[str],
) -> pd.DataFrame | None:
    direct_column = _first_existing(price_frame, ("book_to_market", "bm", "book_equity_to_market"))
    if direct_column is not None:
        return _pivot_numeric(price_frame, direct_column, trade_calendar=list(calendar), symbols=symbols)
    book = _first_existing_matrix(financial_daily, ("book_equity", "total_equity", "net_assets", "total_hldr_eqy_exc_min_int"))
    if book is None or market_cap is None:
        return None
    return book / market_cap.replace(0, np.nan)


def _roe_ttm_matrix(financial_daily: Mapping[str, pd.DataFrame]) -> pd.DataFrame | None:
    direct = _first_existing_matrix(financial_daily, ("roe_ttm", "roe"))
    if direct is not None:
        return direct
    profit = _first_existing_matrix(financial_daily, ("operating_profit_ttm", "operate_profit_ttm", "net_profit_ttm"))
    book = _first_existing_matrix(financial_daily, ("book_equity", "total_equity", "net_assets", "total_hldr_eqy_exc_min_int"))
    if profit is None or book is None:
        return None
    return profit / book.replace(0, np.nan)


def _asset_growth_matrix(financial_daily: Mapping[str, pd.DataFrame]) -> pd.DataFrame | None:
    direct = _first_existing_matrix(financial_daily, ("asset_growth", "total_assets_growth", "total_asset_growth"))
    if direct is not None:
        return direct
    assets = _first_existing_matrix(financial_daily, ("total_assets", "total_asset"))
    if assets is None:
        return None
    return assets / assets.shift(252) - 1.0


def _first_existing_matrix(financial_daily: Mapping[str, pd.DataFrame], names: Sequence[str]) -> pd.DataFrame | None:
    for name in names:
        matrix = financial_daily.get(name)
        if matrix is not None:
            return matrix
    return None


def _apply_direction(matrix: pd.DataFrame, direction: str) -> pd.DataFrame:
    if direction == "negative":
        return -matrix
    return matrix.copy()


def _preprocess(
    directional: Mapping[str, pd.DataFrame],
    *,
    winsor_limits: tuple[float, float],
    min_cross_section: int,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame]:
    winsorized: dict[str, pd.DataFrame] = {}
    zscores: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    lower_q, upper_q = winsor_limits
    for factor_id, matrix in directional.items():
        valid_counts = matrix.notna().sum(axis=1)
        valid_rows = valid_counts >= min_cross_section
        lower = matrix.quantile(lower_q, axis=1)
        upper = matrix.quantile(upper_q, axis=1)
        clipped = matrix.clip(lower=lower, upper=upper, axis=0)
        clipped.loc[~valid_rows, :] = np.nan
        means = clipped.mean(axis=1, skipna=True)
        stds = clipped.std(axis=1, ddof=0, skipna=True).replace(0, np.nan)
        zscore = clipped.sub(means, axis=0).div(stds, axis=0)
        zscore.loc[~valid_rows, :] = np.nan
        winsorized[factor_id] = clipped
        zscores[factor_id] = zscore
        rows.append(
            {
                "factor_id": factor_id,
                "date_count": int(matrix.shape[0]),
                "symbol_count": int(matrix.shape[1]),
                "valid_date_count": int(valid_rows.sum()),
                "raw_observation_count": int(matrix.notna().sum().sum()),
                "zscore_observation_count": int(zscore.notna().sum().sum()),
                "winsor_lower": lower_q,
                "winsor_upper": upper_q,
                "min_cross_section": min_cross_section,
            }
        )
    return winsorized, zscores, pd.DataFrame(rows)


def _quantile_groups(values: pd.Series, groups: int) -> pd.Series:
    ranks = values.rank(method="first")
    if ranks.notna().sum() < groups:
        return pd.Series(index=values.index, dtype="float64")
    try:
        labels = pd.qcut(ranks, groups, labels=False, duplicates="drop")
    except ValueError:
        return pd.Series(index=values.index, dtype="float64")
    return pd.Series(labels, index=values.index, dtype="float64") + 1


def _stack_matrix(matrix: pd.DataFrame, value_name: str) -> pd.DataFrame:
    try:
        return matrix.stack(future_stack=True).rename(value_name).reset_index()
    except TypeError:
        return matrix.stack(dropna=False).rename(value_name).reset_index()


def _window_min_periods(window: int, min_period_ratio: float) -> int:
    return max(1, int(np.ceil(window * min_period_ratio)))


def _t_stat(values: pd.Series) -> float | None:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if len(clean) < 2:
        return None
    std = clean.std(ddof=1)
    if not np.isfinite(std) or std == 0:
        return None
    return float(clean.mean() / (std / np.sqrt(len(clean))))


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _iso_date(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value)
