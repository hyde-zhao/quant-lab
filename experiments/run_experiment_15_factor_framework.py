"""实验十五：因子工程基础框架。"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.metrics import calculate_metrics
from engine.portfolio import PortfolioConfig, RebalanceSignal, run_portfolio
from engine.research_dataset import (
    AllowedClaimsResult,
    ResearchInputMetadata,
    build_auxiliary_availability,
    build_research_input_metadata,
    evaluate_allowed_claims,
    metadata_to_dict,
)
from engine.research_paths import research_report_path
from engine.experiment_lake_input_contract import add_experiment_lake_args, load_experiment_lake_frames
from engine.research_reporting import attach_research_input_metadata
from market_data.benchmarks import build_benchmark_field_payload


REQUIRED_PARQUETS = {
    "prices": "prices.parquet",
    "index_members": "index_members.parquet",
    "trade_calendar": "trade_calendar.parquet",
}

FACTOR_PANEL_FIELDS = [
    "date",
    "symbol",
    "factor_name",
    "factor_value",
    "factor_zscore",
    "forward_return_1d",
    "forward_return_5d",
    "forward_return_10d",
    "forward_return_20d",
]

FORWARD_HORIZONS = (1, 5, 10, 20)
DEFAULT_FACTORS = ("momentum_20d", "volume_ratio_20d", "volatility_20d")
FACTOR_PATTERN = re.compile(r"^(?P<name>momentum|volume_ratio|volatility)_(?P<window>\d+)d$")
EXPERIMENT_15_BASE_ALLOWED_CLAIMS = (
    "factor_framework_smoke",
    "fixed_snapshot_exploration",
    "framework_validation",
    "raw_factor_performance",
    "close_only_exploration",
    "volume_only_exploration",
)
EXPERIMENT_15_REQUESTED_CLAIMS = (
    *EXPERIMENT_15_BASE_ALLOWED_CLAIMS,
    "real_tradable_execution",
    "tradability_screened",
    "true_fillability",
    "vwap_execution",
    "open_execution",
    "intraday_range_factor",
    "full_ohlcv_factor",
    "industry_neutral",
    "industry_attribution",
    "industry_zscore",
    "industry_group_ic",
    "size_neutral",
    "market_cap_neutral",
    "market_cap_weighted_ic",
    "capacity_analysis",
    "corporate_action_audited",
    "auditable_adjustment_chain",
    "liquidity_controlled",
    "tradable_capacity",
    "pure_alpha",
    "style_neutral",
    "risk_model_adjusted_alpha",
    "pit_factor_research",
    "survivorship_bias_controlled",
    "complete_forward_return_label",
)


class FactorFrameworkError(ValueError):
    """因子框架输入或配置错误。"""


@dataclass(frozen=True, slots=True)
class FactorSpec:
    name: str
    family: str
    window: int
    description: str


@dataclass(frozen=True, slots=True)
class FactorCoverage:
    factor_name: str
    row_count: int
    date_count: int
    symbol_count: int
    start_date: str
    end_date: str
    zscore_null_count: int


@dataclass(frozen=True, slots=True)
class Experiment15Result:
    report_path: Path
    factor_panel_path: Path
    factor_schema_path: Path
    factor_preview_path: Path
    backtest_summary_path: Path
    trades_path: Path
    equity_curve_path: Path


def main() -> None:
    args = parse_args()
    result = run_factor_framework(args)
    print(f"报告已生成: {result.report_path}")
    print(f"因子面板已生成: {result.factor_panel_path}")
    print(f"因子 schema 已生成: {result.factor_schema_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验十五因子工程基础框架。")
    add_experiment_lake_args(parser)
    parser.add_argument("--output-dir", default=str(research_report_path("experiment_15")))
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--factors", nargs="+", default=list(DEFAULT_FACTORS), help="因子名，如 momentum_20d volume_ratio_20d。")
    parser.add_argument("--strategy-factor", default="momentum_20d", help="用于最小策略回测的因子。")
    parser.add_argument("--rebalance-freq", type=int, default=5)
    parser.add_argument("--top-fraction", type=float, default=0.1)
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--preview-rows", type=int, default=2000, help="CSV 预览最多输出行数；完整面板写 parquet。")
    if len(sys.argv) <= 1:
        parser.error("legacy --data-dir is no longer a CLI input; pass --lake-root and --as-of.")
    return parser.parse_args()


def run_factor_framework(args: argparse.Namespace) -> Experiment15Result:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    specs = parse_factor_specs(args.factors)
    if args.strategy_factor not in {spec.name for spec in specs}:
        raise FactorFrameworkError(f"strategy_factor 必须包含在 factors 中: {args.strategy_factor}")
    if args.rebalance_freq <= 0:
        raise FactorFrameworkError("rebalance_freq 必须为正数")
    if not 0 < args.top_fraction <= 1:
        raise FactorFrameworkError("top_fraction 必须在 (0, 1] 内")

    frames = _frames_from_explicit_inputs(args)
    close_df, volume_df, universe, calendar = build_matrices(frames, args.start_date, args.end_date)
    factor_panel = build_factor_panel(close_df, volume_df, specs)
    coverages = summarize_factor_coverage(factor_panel)

    panel_path = output_dir / "factor_panel.parquet"
    factor_panel.to_parquet(panel_path, index=False)
    preview_path = output_dir / "factor_panel_preview.csv"
    factor_panel.head(max(int(args.preview_rows), 0)).to_csv(preview_path, index=False)
    schema = build_factor_schema(specs, args, close_df, universe, calendar)
    schema_path = output_dir / "factor_schema.json"
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    backtest = run_factor_backtest(
        close_df,
        factor_panel,
        strategy_factor=args.strategy_factor,
        rebalance_freq=int(args.rebalance_freq),
        top_fraction=float(args.top_fraction),
        initial_cash=float(args.initial_cash),
    )
    backtest["summary"].update(auxiliary_summary_fields(schema["research_input_metadata"]))
    summary_path = output_dir / "factor_backtest_summary.csv"
    pd.DataFrame([backtest["summary"]]).to_csv(summary_path, index=False)
    trades_path = output_dir / "factor_strategy_trades.csv"
    pd.DataFrame(backtest["trades"]).to_csv(trades_path, index=False)
    equity_path = output_dir / "factor_strategy_equity_curve.csv"
    pd.DataFrame(backtest["equity_curve"]).to_csv(equity_path, index=False)

    report_path = output_dir / "factor_framework_report.md"
    report_path.write_text(
        render_report(
            args=args,
            schema=schema,
            coverages=coverages,
            backtest_summary=backtest["summary"],
            paths={
                "panel": panel_path,
                "preview": preview_path,
                "schema": schema_path,
                "summary": summary_path,
                "trades": trades_path,
                "equity": equity_path,
            },
        ),
        encoding="utf-8",
    )
    return Experiment15Result(report_path, panel_path, schema_path, preview_path, summary_path, trades_path, equity_path)


def require_explicit_data_dir(args: argparse.Namespace) -> Path:
    data_dir = getattr(args, "data_dir", None)
    if data_dir is None or str(data_dir).strip() == "":
        raise FactorFrameworkError("必须显式传入 --data-dir，禁止默认读取仓库旧数据目录。")
    return Path(data_dir)


def _frames_from_explicit_inputs(args: argparse.Namespace) -> dict[str, pd.DataFrame]:
    if getattr(args, "lake_root", None) and getattr(args, "as_of", None):
        return dict(load_experiment_lake_frames(args).frames)
    fixture_frames = load_local_frames(require_explicit_data_dir(args))
    fixture_args = argparse.Namespace(
        lake_root=getattr(args, "lake_root", "explicit-fixture-frames"),
        as_of=getattr(args, "as_of", "1970-01-01T00:00:00+00:00"),
        start_date=getattr(args, "start_date", None),
        end_date=getattr(args, "end_date", None),
        symbols=getattr(args, "symbols", None),
        quality_policy=getattr(args, "quality_policy", "require_pass"),
        fixture_frames=fixture_frames,
    )
    return dict(load_experiment_lake_frames(fixture_args).frames)


def parse_factor_specs(factor_names: list[str] | tuple[str, ...]) -> list[FactorSpec]:
    specs: list[FactorSpec] = []
    seen: set[str] = set()
    for factor_name in factor_names:
        if factor_name in seen:
            continue
        seen.add(factor_name)
        match = FACTOR_PATTERN.match(str(factor_name))
        if not match:
            raise FactorFrameworkError(f"不支持的因子名: {factor_name}")
        family = match.group("name")
        window = int(match.group("window"))
        if window <= 0:
            raise FactorFrameworkError(f"因子窗口必须为正数: {factor_name}")
        description = {
            "momentum": f"{window} 日收盘价动量：close[t] / close[t-{window}] - 1",
            "volume_ratio": f"{window} 日成交量相对强度：volume[t] / 最近 {window} 个交易日均量 - 1",
            "volatility": f"{window} 日日收益波动率：std(pct_change(close), window={window})",
        }[family]
        specs.append(FactorSpec(str(factor_name), family, window, description))
    return specs


def load_local_frames(data_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    missing: list[str] = []
    for dataset, filename in REQUIRED_PARQUETS.items():
        path = data_dir / filename
        if not path.exists():
            missing.append(str(path))
            continue
        try:
            frames[dataset] = pd.read_parquet(path)
        except Exception as exc:
            raise FactorFrameworkError(f"parquet 读取失败: {path}: {type(exc).__name__}: {exc}") from exc
    if missing:
        raise FactorFrameworkError("缺少标准 parquet: " + ", ".join(missing))
    return frames


def build_matrices(
    frames: dict[str, pd.DataFrame],
    start_date: str | None,
    end_date: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[date]]:
    prices = frames["prices"].copy()
    members = frames["index_members"].copy()
    calendar_frame = frames["trade_calendar"].copy()
    required_price_columns = {"trade_date", "symbol", "close", "volume"}
    missing_price_columns = sorted(required_price_columns - set(prices.columns))
    if missing_price_columns:
        raise FactorFrameworkError("prices 缺少必需字段: " + ", ".join(missing_price_columns))
    if "symbol" not in members.columns:
        raise FactorFrameworkError("index_members 缺少必需字段: symbol")
    if "trade_date" not in calendar_frame.columns:
        raise FactorFrameworkError("trade_calendar 缺少必需字段: trade_date")

    prices["trade_date"] = _date_series(prices["trade_date"])
    prices["symbol"] = prices["symbol"].astype("string").str.strip()
    prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
    prices["volume"] = pd.to_numeric(prices["volume"], errors="coerce")
    calendar_frame["trade_date"] = _date_series(calendar_frame["trade_date"])
    if "is_open" in calendar_frame.columns:
        calendar_frame = calendar_frame[_bool_series(calendar_frame["is_open"])]

    start = _optional_date(start_date) or prices["trade_date"].min()
    end = _optional_date(end_date) or prices["trade_date"].max()
    if start is None or end is None or pd.isna(start) or pd.isna(end):
        raise FactorFrameworkError("prices 覆盖区间为空")
    if start > end:
        raise FactorFrameworkError("start_date 不得晚于 end_date")

    universe = build_universe(members, prices)
    calendar = sorted(
        {
            item
            for item in calendar_frame["trade_date"].dropna().tolist()
            if start <= item <= end
        }
    )
    if not calendar:
        raise FactorFrameworkError("交易日历在请求区间内为空")
    prices = prices[(prices["trade_date"] >= start) & (prices["trade_date"] <= end)]
    prices = prices[prices["symbol"].isin(universe)]
    close_df = prices.pivot_table(index="trade_date", columns="symbol", values="close", aggfunc="last")
    volume_df = prices.pivot_table(index="trade_date", columns="symbol", values="volume", aggfunc="last")
    close_df = close_df.reindex(index=calendar, columns=universe)
    volume_df = volume_df.reindex(index=calendar, columns=universe)
    close_df.index.name = "date"
    volume_df.index.name = "date"
    if close_df.dropna(how="all").empty:
        raise FactorFrameworkError("close 矩阵为空")
    return close_df, volume_df, universe, calendar


def build_universe(members: pd.DataFrame, prices: pd.DataFrame) -> list[str]:
    work = members.copy()
    work["symbol"] = work["symbol"].astype("string").str.strip()
    if "is_member" in work.columns:
        work = work[_bool_series(work["is_member"])]
    member_symbols = {str(symbol) for symbol in work["symbol"].dropna().tolist() if str(symbol)}
    price_symbols = {str(symbol) for symbol in prices["symbol"].dropna().tolist() if str(symbol)}
    universe = sorted(member_symbols & price_symbols)
    if not universe:
        raise FactorFrameworkError("股票池为空或与 prices 无交集")
    return universe


def build_factor_panel(close_df: pd.DataFrame, volume_df: pd.DataFrame, specs: list[FactorSpec]) -> pd.DataFrame:
    label_frame = build_forward_return_frame(close_df)
    panels = []
    for spec in specs:
        values = calculate_factor_matrix(close_df, volume_df, spec)
        long_frame = matrix_to_long(values, "factor_value")
        long_frame["factor_name"] = spec.name
        long_frame = long_frame.merge(label_frame, on=["date", "symbol"], how="left")
        panels.append(long_frame)
    if not panels:
        return pd.DataFrame(columns=FACTOR_PANEL_FIELDS)
    panel = pd.concat(panels, ignore_index=True)
    panel = panel.dropna(subset=["factor_value"]).reset_index(drop=True)
    panel["factor_zscore"] = panel.groupby(["date", "factor_name"], sort=False)["factor_value"].transform(zscore)
    forward_fields = [f"forward_return_{horizon}d" for horizon in FORWARD_HORIZONS]
    panel = panel.dropna(subset=forward_fields).reset_index(drop=True)
    panel = panel[FACTOR_PANEL_FIELDS]
    return panel.sort_values(["date", "factor_name", "symbol"]).reset_index(drop=True)


def calculate_factor_matrix(close_df: pd.DataFrame, volume_df: pd.DataFrame, spec: FactorSpec) -> pd.DataFrame:
    if spec.family == "momentum":
        return close_df / close_df.shift(spec.window) - 1.0
    if spec.family == "volume_ratio":
        rolling_mean = volume_df.rolling(spec.window, min_periods=spec.window).mean()
        return volume_df / rolling_mean - 1.0
    if spec.family == "volatility":
        returns = close_df.pct_change(fill_method=None)
        return returns.rolling(spec.window, min_periods=spec.window).std(ddof=0)
    raise FactorFrameworkError(f"未实现的因子族: {spec.family}")


def build_forward_return_frame(close_df: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for horizon in FORWARD_HORIZONS:
        matrix = close_df.shift(-horizon) / close_df - 1.0
        frames.append(matrix_to_long(matrix, f"forward_return_{horizon}d"))
    result = frames[0]
    for frame in frames[1:]:
        result = result.merge(frame, on=["date", "symbol"], how="left")
    return result


def matrix_to_long(matrix: pd.DataFrame, value_name: str) -> pd.DataFrame:
    work = matrix.copy()
    work.index = [item.isoformat() if isinstance(item, date) else str(item) for item in work.index]
    work.index.name = "date"
    work.columns = [str(column) for column in work.columns]
    return work.stack(future_stack=True).rename(value_name).reset_index().rename(columns={"level_1": "symbol"})


def zscore(series: pd.Series) -> pd.Series:
    mean = float(series.mean())
    std = float(series.std(ddof=0))
    if not math.isfinite(std) or std == 0:
        return pd.Series([pd.NA] * len(series), index=series.index, dtype="Float64")
    return (series - mean) / std


def summarize_factor_coverage(panel: pd.DataFrame) -> list[FactorCoverage]:
    rows: list[FactorCoverage] = []
    for factor_name, group in panel.groupby("factor_name", sort=True):
        rows.append(
            FactorCoverage(
                factor_name=str(factor_name),
                row_count=int(len(group)),
                date_count=int(group["date"].nunique()),
                symbol_count=int(group["symbol"].nunique()),
                start_date=str(group["date"].min()) if not group.empty else "",
                end_date=str(group["date"].max()) if not group.empty else "",
                zscore_null_count=int(group["factor_zscore"].isna().sum()),
            )
        )
    return rows


def build_factor_schema(
    specs: list[FactorSpec],
    args: argparse.Namespace,
    close_df: pd.DataFrame,
    universe: list[str],
    calendar: list[date],
) -> dict[str, Any]:
    research_input_metadata = build_experiment_15_research_input_metadata(
        specs=specs,
        args=args,
        close_df=close_df,
        universe=universe,
        calendar=calendar,
    )
    research_metadata = metadata_to_dict(research_input_metadata)
    return {
        "schema_name": "experiment_15_factor_panel",
        "schema_version": "1.0",
        "primary_key": ["date", "symbol", "factor_name"],
        "fields": [
            {"name": "date", "type": "string", "description": "因子计算日期，YYYY-MM-DD"},
            {"name": "symbol", "type": "string", "description": "股票代码"},
            {"name": "factor_name", "type": "string", "description": "因子名称"},
            {"name": "factor_value", "type": "float64", "description": "原始因子值"},
            {"name": "factor_zscore", "type": "float64 nullable", "description": "同一日期、同一因子横截面 z-score"},
            {"name": "forward_return_1d", "type": "float64", "description": "未来 1 个交易日 close-to-close 收益"},
            {"name": "forward_return_5d", "type": "float64", "description": "未来 5 个交易日 close-to-close 收益"},
            {"name": "forward_return_10d", "type": "float64", "description": "未来 10 个交易日 close-to-close 收益"},
            {"name": "forward_return_20d", "type": "float64", "description": "未来 20 个交易日 close-to-close 收益"},
        ],
        "factors": [asdict(spec) for spec in specs],
        "label_policy": {
            "price_column": "close",
            "horizons": list(FORWARD_HORIZONS),
            "label_complete_only": True,
            "definition": "forward_return_Nd = close[t+N] / close[t] - 1",
        },
        "standardization_policy": {
            "method": "cross_sectional_zscore",
            "group_keys": ["date", "factor_name"],
            "zero_std_policy": "factor_zscore=null",
        },
        "source": {
            "input_mode": "read_panel_as_of",
            "lake_root": str(getattr(args, "lake_root", "")),
            "as_of": str(getattr(args, "as_of", "")),
            "start_date": close_df.index.min().isoformat() if len(close_df.index) else "",
            "end_date": close_df.index.max().isoformat() if len(close_df.index) else "",
            "calendar_days": len(calendar),
            "symbol_count": len(universe),
            "is_pit_universe": False,
        },
        "auxiliary_availability": research_metadata.get("auxiliary_availability", {}),
        "allowed_claims": research_metadata.get("allowed_claims", []),
        "blocked_claims": research_metadata.get("blocked_claims", []),
        "research_input_metadata": research_metadata,
    }


def build_experiment_15_research_input_metadata(
    *,
    specs: list[FactorSpec],
    args: argparse.Namespace,
    close_df: pd.DataFrame,
    universe: list[str],
    calendar: list[date],
) -> ResearchInputMetadata:
    max_horizon = max(FORWARD_HORIZONS)
    label_available_end = calendar[-max_horizon - 1].isoformat() if len(calendar) > max_horizon else ""
    coverage_start = close_df.index.min().isoformat() if len(close_df.index) else ""
    coverage_end = close_df.index.max().isoformat() if len(close_df.index) else ""
    auxiliary_claims = build_experiment15_auxiliary_claims(specs, label_available_end=label_available_end)
    known_limitations = [
        "fixed snapshot universe; not PIT; survivorship bias must be disclosed",
        "proxy benchmark is same-universe equal-weight buy-and-hold, not real hs300_index",
        "close price is used as execution proxy; no VWAP or tradability gate is available",
        *auxiliary_claims.known_limitations,
    ]
    return build_research_input_metadata(
        {
            "report_kind": "experiment_15_factor_framework",
            "source_run_id": "experiment_15_factor_framework_offline_run",
            "coverage_start": coverage_start,
            "coverage_end": coverage_end,
            "benchmark": {
                "benchmark_status": "proxy_only",
                "benchmark_kind": "proxy_baseline",
                "benchmark_missing_reason": "not_requested",
                "missing_reason": "not_requested",
                "denominator_mode": "same_universe_close_to_close",
            },
            "universe": {
                "universe_mode": "fixed_snapshot",
                "is_pit_universe": False,
                "pit_status": "unavailable",
                "survivorship_bias_note": "fixed snapshot index_members; not PIT",
                "symbol_count": len(universe),
            },
            "adjustment_policy": "source_prices_adjustment_policy_unverified",
            "label_window": {
                "forward_return_horizon": max_horizon,
                "label_available_end": label_available_end,
                "label_status": "complete_only" if label_available_end else "unavailable",
                "horizons": list(FORWARD_HORIZONS),
            },
            "quality": {
                "quality_status": "not_assessed_by_experiment_15",
                "readiness_status": "framework_validation_only",
            },
            "known_limitations": known_limitations,
            "allowed_claims": auxiliary_claims.allowed_claims,
            "blocked_claims": auxiliary_claims.blocked_claims,
            "auxiliary_availability": auxiliary_claims.auxiliary_availability,
            "factor_context": {
                "factor_count": len(specs),
                "factors": [spec.name for spec in specs],
                "strategy_factor": args.strategy_factor,
            },
        }
    )


def build_experiment15_auxiliary_requirements(
    specs: list[FactorSpec],
    report_claims: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    del specs, report_claims
    return {
        "capabilities": [
            "tradability",
            "ohlcv_vwap",
            "industry_classification",
            "market_cap",
            "adjustment_audit",
            "liquidity",
            "style_exposure",
            "pit_universe",
            "label_quality",
        ]
    }


def build_experiment15_auxiliary_claims(
    specs: list[FactorSpec],
    *,
    label_available_end: str,
) -> AllowedClaimsResult:
    requirements = build_experiment15_auxiliary_requirements(specs, EXPERIMENT_15_REQUESTED_CLAIMS)
    reader_results = {
        "ohlcv_vwap": {
            "status": "available",
            "source_dataset": "prices",
            "observed_columns": ["trade_date", "symbol", "close", "volume"],
            "lineage_status": "missing",
        },
        "adjustment_audit": {
            "status": "available",
            "source_dataset": "prices",
            "observed_columns": ["trade_date", "symbol", "close", "volume", "adjustment_policy"],
            "lineage_status": "missing",
        },
        "liquidity": {
            "status": "available",
            "source_dataset": "prices",
            "observed_columns": ["trade_date", "symbol", "volume"],
            "lineage_status": "missing",
        },
    }
    availability = build_auxiliary_availability(
        reader_results,
        requirements,
        gate_result={
            "label_window": {
                "label_status": "complete_only" if label_available_end else "unavailable",
                "label_available_end": label_available_end,
                "forward_return_horizon": max(FORWARD_HORIZONS),
            }
        },
        universe_metadata={
            "universe_mode": "fixed_snapshot",
            "is_pit_universe": False,
            "pit_status": "unavailable",
            "survivorship_bias_note": "fixed snapshot index_members; not PIT",
        },
    )
    return evaluate_allowed_claims(
        availability,
        EXPERIMENT_15_REQUESTED_CLAIMS,
        base_allowed_claims=EXPERIMENT_15_BASE_ALLOWED_CLAIMS,
    )


def auxiliary_summary_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    blocked_claims = list(metadata.get("blocked_claims") or [])
    allowed_claims = list(metadata.get("allowed_claims") or [])
    availability = metadata.get("auxiliary_availability") if isinstance(metadata.get("auxiliary_availability"), dict) else {}
    return {
        "auxiliary_allowed_claims": ",".join(str(item) for item in allowed_claims),
        "auxiliary_blocked_claim_count": len(blocked_claims),
        "auxiliary_blocked_claims": ",".join(str(item.get("claim", "")) for item in blocked_claims if isinstance(item, dict)),
        "auxiliary_available_capability_count": sum(1 for item in availability.values() if isinstance(item, dict) and item.get("status") == "available"),
    }


def run_factor_backtest(
    close_df: pd.DataFrame,
    factor_panel: pd.DataFrame,
    *,
    strategy_factor: str,
    rebalance_freq: int,
    top_fraction: float,
    initial_cash: float,
) -> dict[str, Any]:
    factor_rows = factor_panel[factor_panel["factor_name"] == strategy_factor].copy()
    factor_rows = factor_rows.dropna(subset=["factor_zscore"])
    if factor_rows.empty:
        return empty_backtest_result(strategy_factor, "factor_rows_empty")
    dates = [item.isoformat() if isinstance(item, date) else str(item) for item in close_df.index]
    next_date = {dates[index]: dates[index + 1] for index in range(len(dates) - 1)}
    signal_dates = sorted(date_value for date_value in factor_rows["date"].dropna().unique().tolist() if date_value in next_date)
    signal_dates = signal_dates[::rebalance_freq]
    if not signal_dates:
        return empty_backtest_result(strategy_factor, "signal_schedule_empty")

    signals: list[RebalanceSignal] = []
    selected_counts: list[int] = []
    for signal_date in signal_dates:
        day_scores = factor_rows[factor_rows["date"] == signal_date][["symbol", "factor_zscore"]]
        scores = {
            str(row.symbol): float(row.factor_zscore)
            for row in day_scores.itertuples(index=False)
            if pd.notna(row.factor_zscore)
        }
        target_symbols = select_top_symbols(scores, top_fraction)
        selected_counts.append(len(target_symbols))
        signals.append(
            RebalanceSignal(
                signal_date=pd.to_datetime(signal_date).date(),
                execution_date=pd.to_datetime(next_date[signal_date]).date(),
                target_symbols=target_symbols,
            )
        )
    portfolio_config = PortfolioConfig(initial_cash=initial_cash)
    strategy_result = run_portfolio(close_df, signals, portfolio_config)
    strategy_metrics = calculate_metrics(strategy_result)

    benchmark_signal = RebalanceSignal(
        signal_date=signals[0].signal_date,
        execution_date=signals[0].execution_date,
        target_symbols=list(close_df.columns),
    )
    benchmark_result = run_portfolio(close_df, [benchmark_signal], PortfolioConfig(initial_cash=initial_cash))
    benchmark_metrics = calculate_metrics(benchmark_result)
    benchmark_fields = build_benchmark_field_payload(
        result=None,
        proxy_metrics={
            "total_return": benchmark_metrics["total_return"],
            "annual_return": benchmark_metrics["annual_return"],
            "proxy_excess_return": _optional_subtract(strategy_metrics["total_return"], benchmark_metrics["total_return"]),
            "proxy_excess_annual_return": _optional_subtract(strategy_metrics["annual_return"], benchmark_metrics["annual_return"]),
            "max_drawdown": benchmark_metrics["max_drawdown"],
            "sharpe": benchmark_metrics["sharpe"],
            "turnover": benchmark_metrics["turnover"],
            "final_value": benchmark_metrics["final_value"],
        },
    )

    summary = {
        "status": "success",
        "strategy_factor": strategy_factor,
        "signal_count": len(signals),
        "first_signal_date": signals[0].signal_date.isoformat(),
        "last_signal_date": signals[-1].signal_date.isoformat(),
        "avg_selected_count": sum(selected_counts) / len(selected_counts) if selected_counts else 0.0,
        "top_fraction": top_fraction,
        "rebalance_freq": rebalance_freq,
        "initial_cash": initial_cash,
        "total_return": strategy_metrics["total_return"],
        "annual_return": strategy_metrics["annual_return"],
        "sharpe": strategy_metrics["sharpe"],
        "max_drawdown": strategy_metrics["max_drawdown"],
        "turnover": strategy_metrics["turnover"],
        "final_value": strategy_metrics["final_value"],
        **benchmark_fields,
        "filled_trade_count": sum(1 for trade in strategy_result.trades if trade.status == "filled"),
    }
    return {
        "summary": summary,
        "trades": [asdict(trade) for trade in strategy_result.trades],
        "equity_curve": [
            {
                "date": snapshot.trade_date.isoformat(),
                "cash": snapshot.cash,
                "position_value": snapshot.position_value,
                "total_value": snapshot.total_value,
                "turnover_amount": snapshot.turnover_amount,
                "holding_count": len(snapshot.holdings),
            }
            for snapshot in strategy_result.daily_snapshots
        ],
    }


def empty_backtest_result(strategy_factor: str, reason: str) -> dict[str, Any]:
    return {
        "summary": {
            "status": "skipped",
            "reason": reason,
            "strategy_factor": strategy_factor,
            "signal_count": 0,
        },
        "trades": [],
        "equity_curve": [],
    }


def select_top_symbols(scores: dict[str, float], top_fraction: float) -> list[str]:
    if not scores:
        return []
    count = max(1, math.ceil(len(scores) * top_fraction))
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [symbol for symbol, _ in ranked[:count]]


def render_report(
    *,
    args: argparse.Namespace,
    schema: dict[str, Any],
    coverages: list[FactorCoverage],
    backtest_summary: dict[str, Any],
    paths: dict[str, Path],
) -> str:
    lines = [
        "# 实验十五：因子工程基础框架报告",
        "",
        "## 执行结论",
        "",
        f"- 因子面板：`{paths['panel']}`",
        f"- 因子 schema：`{paths['schema']}`",
        f"- CSV 预览：`{paths['preview']}`",
        f"- 回测摘要：`{paths['summary']}`",
        f"- 回测状态：**{backtest_summary.get('status', '')}**",
        "",
        "## 数据与标签口径",
        "",
        f"- Lake 输入：`{getattr(args, 'lake_root', '')}`",
        f"- PIT as_of：`{getattr(args, 'as_of', '')}`",
        f"- 数据区间：{schema['source']['start_date']} 至 {schema['source']['end_date']}",
        f"- 股票数：{schema['source']['symbol_count']}；交易日数：{schema['source']['calendar_days']}",
        "- 标签定义：`forward_return_Nd = close[t+N] / close[t] - 1`，当前输出仅保留 1/5/10/20 日标签完整的样本。",
        "- 标准化定义：同一 `date + factor_name` 横截面做 z-score；横截面标准差为 0 时 `factor_zscore` 为空。",
        "- 股票池来自当前 `index_members.parquet` 固定快照；不是严格 PIT 成分池，存在幸存者偏差。",
        "",
        *attach_research_input_metadata([], schema["research_input_metadata"]),
        "",
        *render_experiment15_auxiliary_claims_section(schema["research_input_metadata"]),
        "",
        "## 因子面板 Schema",
        "",
        markdown_table(schema["fields"], ["name", "type", "description"]),
        "",
        "## 已计算因子",
        "",
        markdown_table(schema["factors"], ["name", "family", "window", "description"]),
        "",
        "## 面板覆盖",
        "",
        markdown_table([asdict(item) for item in coverages], ["factor_name", "row_count", "date_count", "symbol_count", "start_date", "end_date", "zscore_null_count"]),
        "",
        "## 因子策略回测",
        "",
        markdown_table(
            [backtest_summary],
            [
                "status",
                "strategy_factor",
                "signal_count",
                "first_signal_date",
                "last_signal_date",
                "avg_selected_count",
                "annual_return",
                "proxy_annual_return",
                "proxy_excess_annual_return",
                "sharpe",
                "max_drawdown",
                "turnover",
                "filled_trade_count",
            ],
        ),
        "",
        "## 产物清单",
        "",
        markdown_table(
            [
                {"artifact": "factor_panel", "path": str(paths["panel"]), "description": "完整因子长表 parquet"},
                {"artifact": "factor_panel_preview", "path": str(paths["preview"]), "description": "便于人工查看的 CSV 预览"},
                {"artifact": "factor_schema", "path": str(paths["schema"]), "description": "字段、因子、标签与标准化合同"},
                {"artifact": "factor_backtest_summary", "path": str(paths["summary"]), "description": "因子策略与 proxy_baseline 摘要"},
                {"artifact": "factor_strategy_trades", "path": str(paths["trades"]), "description": "因子策略成交明细"},
                {"artifact": "factor_strategy_equity_curve", "path": str(paths["equity"]), "description": "因子策略净值曲线"},
            ],
            ["artifact", "path", "description"],
        ),
        "",
        "## 限制与后续",
        "",
        "- 当前回测使用 close 作为执行价代理，并沿用默认交易成本；结果用于验证因子工程链路，不应直接当作可交易收益承诺。",
        "- 当前代理基准为同股票池等权买入持有，不是真实沪深300指数。",
        "- 当前严肃归因、执行、容量和风险模型结论均以 `blocked_claims` 为准；报告只保留框架验证和原始因子表现。",
        "- 下一步若要输出更强研究结论，需先通过新的数据生产与合同 Story 补齐对应辅助能力。",
        "",
    ]
    return "\n".join(lines)


def render_experiment15_auxiliary_claims_section(metadata: dict[str, Any]) -> list[str]:
    availability = metadata.get("auxiliary_availability") if isinstance(metadata.get("auxiliary_availability"), dict) else {}
    availability_rows = [
        {
            "capability": capability,
            "status": item.get("status", ""),
            "missing_reason": item.get("missing_reason", ""),
        }
        for capability, item in availability.items()
        if isinstance(item, dict)
    ]
    blocked = [item for item in metadata.get("blocked_claims") or [] if isinstance(item, dict)]
    allowed = [str(item) for item in metadata.get("allowed_claims") or []]
    conservative_auxiliary_statement = (
        "Conservative limitation: industry, market cap, liquidity and style exposure data are unavailable."
    )
    return [
        "## 辅助数据合同",
        "",
        conservative_auxiliary_statement,
        "",
        "### Availability",
        "",
        markdown_table(availability_rows, ["capability", "status", "missing_reason"]),
        "",
        "### Allowed Claims",
        "",
        ", ".join(allowed) if allowed else "无。",
        "",
        "### Blocked Claims",
        "",
        markdown_table(blocked, ["claim", "missing_capability", "reason", "severity"]),
    ]


def markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return "无数据。"
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join("---" for _ in fields) + " |"
    body = ["| " + " | ".join(format_value(row.get(field, "")) for field in fields) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def format_value(value: Any) -> str:
    if value is None or value is pd.NA:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.6f}"
    return str(value).replace("\n", " ")


def _optional_subtract(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def _optional_date(value: str | None) -> date | None:
    if value in (None, ""):
        return None
    return pd.to_datetime(value).date()


def _date_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def _bool_series(series: pd.Series) -> pd.Series:
    def coerce(value: Any) -> bool:
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "y", "是"}

    return series.map(coerce).astype(bool)


if __name__ == "__main__":
    main()
