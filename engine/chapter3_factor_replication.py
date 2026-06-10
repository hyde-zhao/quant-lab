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

from engine.factor_calculators import (
    compute_equity_factor_matrices,
    factor_matrices_to_panel as _generic_factor_matrices_to_panel,
)
from engine.factor_library import (
    DEFAULT_EQUITY_CORE_FACTOR_IDS,
    EquityFactorDefinition as Chapter3FactorDefinition,
    equity_core_factor_definitions,
)
from engine.factor_statistics import (
    build_forward_return_matrix,
    conditional_double_sort_returns,
    fama_macbeth_regression,
    independent_double_sort_returns,
    long_short_summary,
    long_short_summary_from_double_sort,
    newey_west_t_stat,
    single_sort_returns,
)


CHAPTER3_FACTOR_SCHEMA = "chapter3_factor_replication_v1"
CHAPTER3_AUDIT_SCHEMA = "chapter3_data_issue_audit_v1"
CHAPTER3_RESEARCH_POLICY_SCHEMA = "chapter3_research_policy_v1"

STATUS_COVERED = "covered"
STATUS_PARTIAL = "partial"
STATUS_MISSING = "missing"

DEFAULT_FACTOR_IDS = DEFAULT_EQUITY_CORE_FACTOR_IDS

DEFAULT_CHAPTER3_PRICE_COLUMNS = (
    "back_adjusted_close",
    "hfq_close",
    "adjusted_close",
    "qfq_close",
    "close",
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


@dataclass(frozen=True, slots=True)
class Chapter3ResearchPolicy:
    """第三章实证默认口径，全部只作用于调用方传入的离线数据。"""

    adjustment_policy: str = "back_adjusted_or_hfq"
    price_columns: tuple[str, ...] = DEFAULT_CHAPTER3_PRICE_COLUMNS
    include_financial_industry: bool = True
    exclude_star_market: bool = True
    new_stock_min_days: int = 365
    compress_returns_after: str = "1996-12-16"
    return_clip: tuple[float, float] = (-0.10, 0.10)
    one_price_tolerance: float = 1e-8
    schema_version: str = CHAPTER3_RESEARCH_POLICY_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Chapter3PreparedData:
    close: pd.DataFrame
    returns: pd.DataFrame
    universe_mask: pd.DataFrame
    tradable_mask: pd.DataFrame
    rebalance_dates: tuple[date, ...]
    selected_price_column: str
    limitations: tuple[str, ...]
    policy: Chapter3ResearchPolicy


def chapter3_factor_definitions() -> tuple[Chapter3FactorDefinition, ...]:
    """返回第三章复刻使用的通用因子定义。

    因子定义的 canonical 来源是 `engine.factor_library`；第三章只作为
    `source_refs` 中的来源元数据存在。
    """

    return equity_core_factor_definitions()


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
    stock_basic: pd.DataFrame | None = None,
    trade_status: pd.DataFrame | None = None,
    prices_limit: pd.DataFrame | None = None,
    trade_calendar: pd.DataFrame | Sequence[Any] | None = None,
    factor_ids: Sequence[str] = DEFAULT_FACTOR_IDS,
    winsor_limits: tuple[float, float] = (0.01, 0.99),
    min_period_ratio: float = 2.0 / 3.0,
    min_cross_section: int = 5,
    research_policy: Chapter3ResearchPolicy | None = None,
    universe_mask: pd.DataFrame | None = None,
    tradable_mask: pd.DataFrame | None = None,
) -> Chapter3FactorReplicationResult:
    if not 0 <= winsor_limits[0] < winsor_limits[1] <= 1:
        raise ValueError("winsor_limits 必须满足 0 <= lower < upper <= 1")
    if not 0 < min_period_ratio <= 1:
        raise ValueError("min_period_ratio 必须在 (0, 1] 内")
    if min_cross_section < 2:
        raise ValueError("min_cross_section 必须至少为 2")

    policy = research_policy or Chapter3ResearchPolicy()
    price_frame = _normalise_long_frame(prices, required=("trade_date", "symbol"))
    close_column = _first_existing(price_frame, policy.price_columns)
    if close_column is None:
        raise ValueError("prices 缺少 back_adjusted_close/hfq_close/adjusted_close/qfq_close/close 字段")
    close = _pivot_numeric(price_frame, close_column, trade_calendar=trade_calendar)
    symbols = tuple(str(item) for item in close.columns)
    calendar = list(close.index)

    market_cap_matrix = _optional_matrix(market_cap, ("market_cap", "total_market_cap", "circ_mv"), calendar, symbols)
    turnover_matrix = _turnover_matrix(price_frame, market_cap, calendar, symbols)
    financial_daily = _build_financial_daily(financials, calendar, symbols)

    suspended = _suspended_matrix(price_frame, trade_status, calendar, symbols)
    returns = build_chapter3_return_matrix(close, suspended=suspended, policy=policy)
    derived_universe_mask = (
        _align_bool_mask(universe_mask, calendar, symbols, default=True)
        if universe_mask is not None
        else build_chapter3_universe_mask(
            calendar,
            symbols,
            stock_basic=stock_basic,
            financial_daily=financial_daily,
            policy=policy,
        )
    )
    derived_tradable_mask = (
        _align_bool_mask(tradable_mask, calendar, symbols, default=True)
        if tradable_mask is not None
        else build_chapter3_tradable_mask(
            price_frame,
            trade_status=trade_status,
            prices_limit=prices_limit,
            calendar=calendar,
            symbols=symbols,
            policy=policy,
        )
    )
    factor_eligibility = derived_universe_mask & derived_tradable_mask
    returns_for_market = returns.where(derived_universe_mask)

    requested = set(factor_ids)
    computed = compute_equity_factor_matrices(
        close=close,
        returns=returns_for_market,
        price_frame=price_frame,
        market_cap_matrix=market_cap_matrix,
        turnover_matrix=turnover_matrix,
        financial_daily=financial_daily,
        factor_ids=factor_ids,
        eligibility_mask=factor_eligibility,
        winsor_limits=winsor_limits,
        min_period_ratio=min_period_ratio,
        min_cross_section=min_cross_section,
    )
    definitions = tuple(item for item in chapter3_factor_definitions() if item.factor_id in requested)

    return Chapter3FactorReplicationResult(
        factor_definitions=definitions,
        raw_matrices=computed.raw_matrices,
        directional_matrices=computed.directional_matrices,
        winsorized_matrices=computed.winsorized_matrices,
        zscore_matrices=computed.zscore_matrices,
        market_factor_return=computed.market_factor_return,
        preprocessing_summary=computed.preprocessing_summary,
        limitations=computed.limitations,
    )


def factor_matrices_to_panel(
    result: Chapter3FactorReplicationResult,
    *,
    source_dataset: str = "research_input_v1",
    factor_version: str = "chapter3-v1",
    quality_status: str = "pass",
) -> pd.DataFrame:
    return _generic_factor_matrices_to_panel(
        result,
        source_dataset=source_dataset,
        factor_version=factor_version,
        quality_status=quality_status,
    )


def prepare_chapter3_research_data(
    prices: pd.DataFrame,
    *,
    stock_basic: pd.DataFrame | None = None,
    financials: pd.DataFrame | None = None,
    trade_status: pd.DataFrame | None = None,
    prices_limit: pd.DataFrame | None = None,
    trade_calendar: pd.DataFrame | Sequence[Any] | None = None,
    research_policy: Chapter3ResearchPolicy | None = None,
) -> Chapter3PreparedData:
    policy = research_policy or Chapter3ResearchPolicy()
    price_frame = _normalise_long_frame(prices, required=("trade_date", "symbol"))
    close_column = _first_existing(price_frame, policy.price_columns)
    if close_column is None:
        raise ValueError("prices 缺少 back_adjusted_close/hfq_close/adjusted_close/qfq_close/close 字段")
    close = _pivot_numeric(price_frame, close_column, trade_calendar=trade_calendar)
    symbols = tuple(str(item) for item in close.columns)
    calendar = list(close.index)
    financial_daily = _build_financial_daily(financials, calendar, symbols)
    suspended = _suspended_matrix(price_frame, trade_status, calendar, symbols)
    returns = build_chapter3_return_matrix(close, suspended=suspended, policy=policy)
    universe = build_chapter3_universe_mask(calendar, symbols, stock_basic=stock_basic, financial_daily=financial_daily, policy=policy)
    tradable = build_chapter3_tradable_mask(
        price_frame,
        trade_status=trade_status,
        prices_limit=prices_limit,
        calendar=calendar,
        symbols=symbols,
        policy=policy,
    )
    limitations: list[str] = []
    if close_column not in {"back_adjusted_close", "hfq_close"}:
        limitations.append(f"价格列使用 {close_column}，不是第三章首选的后复权口径。")
    if stock_basic is None:
        limitations.append("缺 stock_basic，黑名单只能依赖财务矩阵中的负净资产字段。")
    if trade_status is None and "is_suspended" not in price_frame.columns:
        limitations.append("缺 trade_status/is_suspended，停牌日收益置缺和调仓剔除无法完全验证。")
    if prices_limit is None and not _has_any_column(price_frame, ("limit_up", "limit_down", "up_limit", "down_limit")):
        limitations.append("缺 prices_limit/涨跌停字段，一字涨跌停剔除无法完全验证。")
    return Chapter3PreparedData(
        close=close,
        returns=returns,
        universe_mask=universe,
        tradable_mask=tradable,
        rebalance_dates=chapter3_month_end_rebalance_dates(calendar),
        selected_price_column=close_column,
        limitations=tuple(limitations),
        policy=policy,
    )


def build_chapter3_return_matrix(
    close: pd.DataFrame,
    *,
    suspended: pd.DataFrame | None = None,
    policy: Chapter3ResearchPolicy | None = None,
) -> pd.DataFrame:
    policy = policy or Chapter3ResearchPolicy()
    returns = close.pct_change(fill_method=None)
    if suspended is not None:
        suspended = _align_bool_mask(suspended, close.index, close.columns, default=False)
        returns = returns.mask(suspended)
    clip_start = pd.Timestamp(policy.compress_returns_after).date()
    after_clip_start = pd.Series(close.index, index=close.index).map(lambda value: value >= clip_start)
    returns.loc[after_clip_start, :] = returns.loc[after_clip_start, :].clip(
        lower=policy.return_clip[0],
        upper=policy.return_clip[1],
    )
    return returns


def build_chapter3_universe_mask(
    calendar: Sequence[Any],
    symbols: Sequence[str],
    *,
    stock_basic: pd.DataFrame | None = None,
    financial_daily: Mapping[str, pd.DataFrame] | None = None,
    policy: Chapter3ResearchPolicy | None = None,
) -> pd.DataFrame:
    policy = policy or Chapter3ResearchPolicy()
    index = [pd.Timestamp(item).date() for item in calendar]
    columns = [str(item) for item in symbols]
    mask = pd.DataFrame(True, index=index, columns=columns)
    if policy.exclude_star_market:
        star_symbols = {symbol for symbol in columns if symbol.startswith("688")}
        if stock_basic is not None and not stock_basic.empty:
            basic = stock_basic.copy()
            if "symbol" in basic.columns:
                basic["symbol"] = basic["symbol"].astype("string").str.strip()
                for column in ("board", "market", "exchange", "list_board"):
                    if column in basic.columns:
                        star = basic[column].astype("string").str.contains("科创|STAR|SSE_STAR", case=False, regex=True, na=False)
                        star_symbols |= set(basic.loc[star, "symbol"].astype(str))
        for symbol in star_symbols & set(columns):
            mask.loc[:, symbol] = False
    if stock_basic is not None and not stock_basic.empty and "symbol" in stock_basic.columns:
        basic = stock_basic.copy()
        basic["symbol"] = basic["symbol"].astype("string").str.strip()
        for _, row in basic.iterrows():
            symbol = str(row["symbol"])
            if symbol not in mask.columns:
                continue
            if _truthy(row.get("is_st")) or _truthy(row.get("st_status")):
                mask.loc[:, symbol] = False
            list_status = str(row.get("list_status", "")).upper()
            if list_status and list_status not in {"L", "LISTED", "上市", "NAN", "<NA>"}:
                mask.loc[:, symbol] = False
            list_date = _optional_date(row.get("list_date"))
            if list_date is not None and policy.new_stock_min_days > 0:
                eligible_after = pd.Timestamp(list_date) + pd.Timedelta(days=policy.new_stock_min_days)
                mask.loc[[item < eligible_after.date() for item in mask.index], symbol] = False
            delist_date = _optional_date(row.get("delist_date"))
            if delist_date is not None:
                mask.loc[[item >= delist_date for item in mask.index], symbol] = False
            net_asset = _first_row_value(row, ("book_equity", "net_assets", "total_equity", "total_hldr_eqy_exc_min_int"))
            if net_asset is not None and np.isfinite(net_asset) and net_asset <= 0:
                mask.loc[:, symbol] = False
    equity = _first_existing_matrix(financial_daily or {}, ("book_equity", "net_assets", "total_equity", "total_hldr_eqy_exc_min_int"))
    if equity is not None:
        equity = equity.reindex(index=mask.index, columns=mask.columns)
        mask = mask & (equity.isna() | (equity > 0))
    return mask


def build_chapter3_tradable_mask(
    price_frame: pd.DataFrame,
    *,
    trade_status: pd.DataFrame | None,
    prices_limit: pd.DataFrame | None,
    calendar: Sequence[Any],
    symbols: Sequence[str],
    policy: Chapter3ResearchPolicy | None = None,
) -> pd.DataFrame:
    policy = policy or Chapter3ResearchPolicy()
    index = [pd.Timestamp(item).date() for item in calendar]
    columns = [str(item) for item in symbols]
    tradable = pd.DataFrame(True, index=index, columns=columns)
    suspended = _suspended_matrix(price_frame, trade_status, index, columns)
    if suspended is not None:
        tradable = tradable & ~suspended
    limit_up = _limit_mask(price_frame, prices_limit, index, columns, kind="up", policy=policy)
    limit_down = _limit_mask(price_frame, prices_limit, index, columns, kind="down", policy=policy)
    return tradable & ~limit_up & ~limit_down


def chapter3_month_end_rebalance_dates(calendar: Sequence[Any]) -> tuple[date, ...]:
    index = pd.Index([pd.Timestamp(item).date() for item in calendar])
    if index.empty:
        return ()
    months = pd.Series(index, index=index).groupby([item.strftime("%Y-%m") for item in index]).max()
    return tuple(pd.Timestamp(item).date() for item in months.tolist())


def canonicalize_chapter3_financials(financials: pd.DataFrame) -> pd.DataFrame:
    """按第三章 PIT 原则为同日多条财务记录建立稳定优先级。

    调用方仍需提供已经离线落地的财报记录；本函数不抓取、不修正源数据，只
    避免同一 symbol/report_period/available_at 存在多条记录时随机取最后一条。
    """

    if financials.empty:
        return financials.copy()
    work = financials.copy()
    if "symbol" in work.columns:
        work["symbol"] = work["symbol"].astype("string").str.strip()
    available_column = _first_existing(work, ("available_at", "ann_date", "publish_date", "trade_date"))
    if available_column is not None:
        work["available_at"] = pd.to_datetime(work[available_column]).dt.date
    report_column = _first_existing(work, ("report_period", "end_date", "f_ann_date"))
    if report_column is not None:
        work["report_period"] = pd.to_datetime(work[report_column], errors="coerce").dt.strftime("%Y%m%d")
    work["chapter3_record_priority"] = work.apply(_financial_record_priority, axis=1)
    sort_columns = [column for column in ("symbol", "report_period", "available_at", "chapter3_record_priority") if column in work.columns]
    if sort_columns:
        work = work.sort_values(sort_columns)
    dedupe_columns = [column for column in ("symbol", "report_period", "available_at") if column in work.columns]
    if len(dedupe_columns) >= 2:
        work = work.drop_duplicates(subset=dedupe_columns, keep="last")
    return work


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


def _suspended_matrix(
    price_frame: pd.DataFrame,
    trade_status: pd.DataFrame | None,
    calendar: Sequence[Any],
    symbols: Sequence[str],
) -> pd.DataFrame | None:
    source = trade_status
    if source is None and _has_any_column(price_frame, ("is_suspended", "suspend_type", "trade_status")):
        source = price_frame
    if source is None or source.empty:
        return None
    work = _normalise_long_frame(source, required=("trade_date", "symbol"))
    if "is_suspended" in work.columns:
        values = work["is_suspended"].map(_truthy)
    elif "trade_status" in work.columns:
        status = work["trade_status"].astype("string").str.lower()
        values = status.str.contains("suspend|停牌|paused|halt", regex=True, na=False)
    elif "suspend_type" in work.columns:
        values = work["suspend_type"].notna() & (work["suspend_type"].astype("string").str.strip() != "")
    else:
        return None
    work = work.assign(_suspended=values.astype(bool))
    return work.pivot_table(index="trade_date", columns="symbol", values="_suspended", aggfunc="last").reindex(
        index=list(calendar),
        columns=list(symbols),
        fill_value=False,
    ).astype(bool)


def _limit_mask(
    price_frame: pd.DataFrame,
    prices_limit: pd.DataFrame | None,
    calendar: Sequence[Any],
    symbols: Sequence[str],
    *,
    kind: str,
    policy: Chapter3ResearchPolicy,
) -> pd.DataFrame:
    frame = price_frame.copy()
    limit_columns = ("limit_up", "up_limit", "is_limit_up") if kind == "up" else ("limit_down", "down_limit", "is_limit_down")
    flag_column = _first_existing(frame, limit_columns)
    flag = None
    if flag_column is not None:
        flag = _pivot_bool(frame, flag_column, calendar, symbols)
    if prices_limit is not None and not prices_limit.empty:
        limit_frame = _normalise_long_frame(prices_limit, required=("trade_date", "symbol"))
        limit_flag_column = _first_existing(limit_frame, limit_columns)
        if limit_flag_column is not None:
            limit_flag = _pivot_bool(limit_frame, limit_flag_column, calendar, symbols)
            flag = limit_flag if flag is None else (flag | limit_flag)
    one_price = _one_price_mask(frame, calendar, symbols, policy=policy)
    if flag is not None:
        return flag & one_price
    price_column = "up_limit" if kind == "up" else "down_limit"
    if prices_limit is not None and price_column in prices_limit.columns and "close" in frame.columns:
        limit_frame = _normalise_long_frame(prices_limit, required=("trade_date", "symbol"))
        limit_price = _pivot_numeric(limit_frame, price_column, trade_calendar=list(calendar), symbols=symbols)
        close = _pivot_numeric(frame, "close", trade_calendar=list(calendar), symbols=symbols)
        return _isclose_frame(close, limit_price, tolerance=policy.one_price_tolerance) & one_price
    return pd.DataFrame(False, index=list(calendar), columns=list(symbols))


def _one_price_mask(
    price_frame: pd.DataFrame,
    calendar: Sequence[Any],
    symbols: Sequence[str],
    *,
    policy: Chapter3ResearchPolicy,
) -> pd.DataFrame:
    if not {"open", "high", "low", "close"} <= set(price_frame.columns):
        return pd.DataFrame(True, index=list(calendar), columns=list(symbols))
    open_ = _pivot_numeric(price_frame, "open", trade_calendar=list(calendar), symbols=symbols)
    high = _pivot_numeric(price_frame, "high", trade_calendar=list(calendar), symbols=symbols)
    low = _pivot_numeric(price_frame, "low", trade_calendar=list(calendar), symbols=symbols)
    close = _pivot_numeric(price_frame, "close", trade_calendar=list(calendar), symbols=symbols)
    tol = policy.one_price_tolerance
    return _isclose_frame(open_, high, tolerance=tol) & _isclose_frame(high, low, tolerance=tol) & _isclose_frame(low, close, tolerance=tol)


def _pivot_bool(
    frame: pd.DataFrame,
    value_column: str,
    calendar: Sequence[Any],
    symbols: Sequence[str],
) -> pd.DataFrame:
    work = frame.copy()
    work[value_column] = work[value_column].map(_truthy)
    return work.pivot_table(index="trade_date", columns="symbol", values=value_column, aggfunc="last").reindex(
        index=list(calendar),
        columns=list(symbols),
        fill_value=False,
    ).astype(bool)


def _build_financial_daily(
    financials: pd.DataFrame | None,
    calendar: Sequence[Any],
    symbols: Sequence[str],
) -> dict[str, pd.DataFrame]:
    if financials is None or financials.empty:
        return {}
    work = canonicalize_chapter3_financials(financials)
    if "symbol" not in work.columns:
        return {}
    available_column = _first_existing(work, ("available_at", "ann_date", "publish_date", "trade_date", "available_date"))
    if available_column is None:
        return {}
    work["available_date"] = pd.to_datetime(work[available_column]).dt.date
    work["symbol"] = work["symbol"].astype("string").str.strip()
    work = work.dropna(subset=["available_date", "symbol"]).sort_values(["symbol", "available_date"])
    work = _add_chapter3_financial_derived_columns(work)
    result: dict[str, pd.DataFrame] = {}
    value_columns = [
        column
        for column in work.columns
        if column
        not in {
            "trade_date",
            "available_at",
            "ann_date",
            "publish_date",
            "available_date",
            "symbol",
            "report_period",
            "end_date",
            "statement_type",
            "report_type",
            "update_flag",
            "chapter3_record_priority",
        }
    ]
    for column in value_columns:
        work[column] = pd.to_numeric(work[column], errors="coerce")
        matrix = work.pivot_table(index="available_date", columns="symbol", values=column, aggfunc="last")
        matrix = matrix.reindex(index=list(calendar), columns=list(symbols)).sort_index().ffill()
        result[column] = matrix
    return result


def _add_chapter3_financial_derived_columns(financials: pd.DataFrame) -> pd.DataFrame:
    """补充第三章盈利和投资因子的 PIT 衍生变量。"""

    work = financials.copy()
    report_column = _first_existing(work, ("report_period", "end_date", "f_ann_date"))
    if report_column is None or "available_date" not in work.columns or "symbol" not in work.columns:
        return work
    work["chapter3_report_period"] = pd.to_datetime(work[report_column], errors="coerce").dt.strftime("%Y%m%d")
    work = work.sort_values(["symbol", "available_date", "chapter3_report_period"])
    equity_column = _first_existing(work, ("book_equity", "total_equity", "net_assets", "total_hldr_eqy_exc_min_int"))
    profit_column = _first_existing(work, ("operating_profit_ttm", "operate_profit_ttm", "net_profit_ttm"))
    assets_column = _first_existing(work, ("total_assets", "total_asset"))

    if equity_column is not None:
        work["chapter3_book_equity_avg4q"] = _derive_pit_rolling_report_mean(
            work,
            value_column=equity_column,
            periods=4,
        )
    if profit_column is not None and "chapter3_book_equity_avg4q" in work.columns:
        denominator = pd.to_numeric(work["chapter3_book_equity_avg4q"], errors="coerce").replace(0, np.nan)
        work["chapter3_roe_ttm"] = pd.to_numeric(work[profit_column], errors="coerce") / denominator
    if assets_column is not None:
        work["chapter3_annual_asset_growth"] = _derive_pit_annual_asset_growth(work, value_column=assets_column)
        work["chapter3_annual_asset_growth"] = work.groupby("symbol", sort=False)["chapter3_annual_asset_growth"].ffill()
    return work


def _derive_pit_rolling_report_mean(
    financials: pd.DataFrame,
    *,
    value_column: str,
    periods: int,
) -> pd.Series:
    values = pd.Series(np.nan, index=financials.index, dtype="float64")
    for _, group in financials.groupby("symbol", sort=False):
        report_values: dict[str, float] = {}
        for index, row in group.iterrows():
            report_period = str(row.get("chapter3_report_period", ""))
            value = _safe_float(row.get(value_column))
            if report_period and np.isfinite(value):
                report_values[report_period] = value
            eligible_periods = sorted(period for period in report_values if period <= report_period)[-periods:]
            eligible_values = [report_values[period] for period in eligible_periods if np.isfinite(report_values[period])]
            if eligible_values:
                values.loc[index] = float(np.mean(eligible_values))
    return values


def _derive_pit_annual_asset_growth(financials: pd.DataFrame, *, value_column: str) -> pd.Series:
    values = pd.Series(np.nan, index=financials.index, dtype="float64")
    for _, group in financials.groupby("symbol", sort=False):
        annual_assets: dict[str, float] = {}
        for index, row in group.iterrows():
            report_period = str(row.get("chapter3_report_period", ""))
            value = _safe_float(row.get(value_column))
            if report_period.endswith("1231") and np.isfinite(value):
                if len(report_period) != 8 or not report_period[:4].isdigit():
                    continue
                previous_period = f"{int(report_period[:4]) - 1}1231"
                previous = annual_assets.get(previous_period)
                if previous is not None and previous != 0 and np.isfinite(previous):
                    values.loc[index] = value / previous - 1.0
                annual_assets[report_period] = value
    return values


def _first_existing_matrix(financial_daily: Mapping[str, pd.DataFrame], names: Sequence[str]) -> pd.DataFrame | None:
    for name in names:
        matrix = financial_daily.get(name)
        if matrix is not None:
            return matrix
    return None


def _has_any_column(frame: pd.DataFrame, columns: Sequence[str]) -> bool:
    return any(column in frame.columns for column in columns)


def _align_bool_mask(
    mask: pd.DataFrame,
    calendar: Sequence[Any],
    symbols: Sequence[Any],
    *,
    default: bool,
) -> pd.DataFrame:
    aligned = mask.copy()
    aligned.index = [pd.Timestamp(item).date() for item in aligned.index]
    aligned.columns = [str(item) for item in aligned.columns]
    return aligned.reindex(
        index=[pd.Timestamp(item).date() for item in calendar],
        columns=[str(item) for item in symbols],
        fill_value=default,
    ).astype(bool)


def _truthy(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y", "st", "*st", "suspend", "停牌", "risk", "风险警示"}


def _optional_date(value: Any) -> date | None:
    if value is None or pd.isna(value):
        return None
    try:
        timestamp = pd.Timestamp(value)
        if pd.isna(timestamp):
            return None
        return timestamp.date()
    except (TypeError, ValueError):
        return None


def _first_row_value(row: pd.Series, columns: Sequence[str]) -> float | None:
    for column in columns:
        if column in row.index and pd.notna(row[column]):
            try:
                return float(row[column])
            except (TypeError, ValueError):
                return None
    return None


def _safe_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result if np.isfinite(result) else float("nan")


def _financial_record_priority(row: pd.Series) -> int:
    fields = " ".join(
        str(row.get(column, "")).lower()
        for column in ("statement_type", "report_type", "update_flag", "record_type", "data_type")
    )
    if "latest_pit" in fields:
        return 50
    if "type2" in fields or "baseline" in fields or "基准" in fields:
        return 40
    if "type1" in fields or "initial" in fields or "初始" in fields:
        return 30
    if "type4" in fields:
        return 20
    if "type3" in fields or "original" in fields or "原始" in fields:
        return 10
    return 0


def _isclose_frame(left: pd.DataFrame, right: pd.DataFrame, *, tolerance: float) -> pd.DataFrame:
    right = right.reindex(index=left.index, columns=left.columns)
    values = np.isclose(left.to_numpy(dtype="float64"), right.to_numpy(dtype="float64"), atol=tolerance, equal_nan=False)
    return pd.DataFrame(values, index=left.index, columns=left.columns)
