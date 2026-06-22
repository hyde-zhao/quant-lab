"""离线 parquet 数据加载与回测输入合同校验。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
import csv
from typing import Any

import pandas as pd

from engine.contracts import (
    DATASET_STATUS_FAIL_VALUES,
    DATASET_STATUS_PASS_VALUES,
    DATASET_STATUS_WARN_VALUES,
    DATASET_REQUIRED_COLUMNS,
    DEFAULT_ADJUSTMENT_POLICY,
    DEFAULT_AVAILABLE_AT_RULE,
    DEFAULT_QUALITY_POLICY,
    FETCH_STATUS_SUCCESS_VALUES,
    LOADER_METADATA_FIELDS,
    QUALITY_POLICY_VALUES,
    QUALITY_REPORT_REQUIRED_FIELDS,
    STANDARD_PARQUET_FILES,
    SURVIVORSHIP_BIAS_NOTE,
)
from engine.diagnostics import start_diagnostic
from engine.quality import QualityError, calculate_quality
from engine.research_dataset import ResearchDatasetRequest, build_research_dataset
from engine.research_paths import research_report_path
from engine.source_registry import require_resolved_registry_key, SourceRegistryError
from market_data.readers import LightweightInputRequest, read_lightweight_input


class DataLoaderError(Exception):
    """Data Loader 基础异常。"""


class DataContractError(DataLoaderError):
    """输入数据合同不满足。"""


class DataQualityGateError(DataContractError):
    """质量报告门禁失败。"""


@dataclass(slots=True)
class LoaderConfig:
    data_dir: str | Path = "data"
    manifest_path: str | Path = "data/manifests/data_prep_manifest.jsonl"
    quality_report_path: str | Path = research_report_path("data_quality_report.csv")
    input_mode: str = "legacy_flat"
    market_data_lake_root: str | Path | None = None
    dataset: str = "prices"
    start_date: str | date | None = None
    end_date: str | date | None = None
    adjustment_policy: str = DEFAULT_ADJUSTMENT_POLICY
    quality_policy: str = DEFAULT_QUALITY_POLICY
    legacy_flat_enabled: bool = False
    decision_time_rule: str = DEFAULT_AVAILABLE_AT_RULE
    allow_exploratory_recompute: bool = False
    enable_pit_universe: bool = False
    enable_trade_status: bool = False
    enable_limit_constraints: bool = False
    enable_events: bool = False


@dataclass(slots=True)
class LoadedBacktestData:
    close_df: pd.DataFrame
    universe: list[str]
    calendar: list[date]
    metadata: dict[str, Any] = field(default_factory=dict)


def load_backtest_data(config: LoaderConfig | dict[str, Any]) -> LoadedBacktestData:
    """加载标准 parquet、质量报告和 manifest，返回下游回测对象。"""

    cfg = _coerce_config(config)
    input_mode = str(cfg.input_mode).replace("-", "_")
    if input_mode == "canonical_gold":
        return _load_canonical_gold_backtest_data(cfg)
    if input_mode != "legacy_flat":
        raise DataContractError(f"未知数据输入模式: {cfg.input_mode}")
    _validate_legacy_flat_path(cfg)
    diag = start_diagnostic(
        "data_loader",
        "STORY-004",
        {
            "data_dir": Path(cfg.data_dir),
            "start_date": cfg.start_date,
            "end_date": cfg.end_date,
            "quality_policy": cfg.quality_policy,
            "pit_enabled": cfg.enable_pit_universe,
        },
    )
    try:
        _validate_enhancement_gates(cfg)
        data_dir = Path(cfg.data_dir)
        paths = {name: data_dir / filename for name, filename in STANDARD_PARQUET_FILES.items()}
        for dataset, path in paths.items():
            if not path.exists():
                raise DataContractError(f"缺少标准 parquet: dataset={dataset}, path={path}")
        manifest_path = Path(cfg.manifest_path)
        if not manifest_path.exists():
            raise DataContractError(f"缺少 manifest: {manifest_path}")

        frames = {
            dataset: _read_parquet_with_required_columns(dataset, path)
            for dataset, path in paths.items()
        }
        quality = _load_quality_gate(cfg, paths, diag)
        calendar = _build_calendar(frames["trade_calendar"], cfg)
        universe = _build_universe(frames["index_members"], cfg)
        close_df = _build_close_matrix(frames["prices"], calendar, universe, cfg)
        metadata = _build_loader_metadata(
            cfg=cfg,
            paths=paths,
            quality=quality,
            index_members=frames["index_members"],
            calendar=calendar,
            close_df=close_df,
            universe=universe,
        )
        if metadata["warnings"]:
            diag.warning("quality_warn", warnings=metadata["warnings"])
        diag.end("success", calendar_count=len(calendar), universe_count=len(universe))
        return LoadedBacktestData(close_df=close_df, universe=universe, calendar=calendar, metadata=metadata)
    except Exception as exc:
        diag.error(exc)
        raise


def load_research_backtest_data(
    config: ResearchDatasetRequest | LoaderConfig | dict[str, Any],
    *,
    builder: Any = None,
) -> LoadedBacktestData:
    """显式 CR008 research dataset adapter，不改变 legacy/canonical 默认入口。"""

    request = _coerce_research_request(config)
    dataset_builder = builder or build_research_dataset
    dataset = dataset_builder(request)
    if dataset.status not in {"available", "available_with_warnings"} or dataset.close_df is None:
        message = _format_research_dataset_error(dataset)
        if dataset.status == "quality_failed":
            raise DataQualityGateError(message)
        raise DataContractError(message)
    return LoadedBacktestData(
        close_df=dataset.close_df,
        universe=list(dataset.universe_symbols),
        calendar=list(dataset.calendar),
        metadata={
            **dataset.metadata,
            "input_mode": "research_dataset_builder",
            "research_dataset_status": dataset.status,
            "gate_result": dataset.gate_result.to_dict(),
            "remediation_spec": dataset.remediation_spec,
        },
    )


def _coerce_research_request(
    config: ResearchDatasetRequest | LoaderConfig | dict[str, Any],
) -> ResearchDatasetRequest:
    if isinstance(config, ResearchDatasetRequest):
        return config
    if isinstance(config, LoaderConfig):
        return ResearchDatasetRequest(
            lake_root=config.market_data_lake_root,
            start_date=config.start_date,
            end_date=config.end_date,
            adjustment_policy=config.adjustment_policy,
            analysis_mode="research",
        )
    values = dict(config)
    if "lake_root" not in values and "market_data_lake_root" in values:
        values["lake_root"] = values.pop("market_data_lake_root")
    return ResearchDatasetRequest(**values)


def _format_research_dataset_error(dataset: Any) -> str:
    issues = getattr(dataset, "issues", [])
    code = issues[0].code if issues else getattr(dataset, "status", "unknown")
    return f"research dataset 输入不可用: status={dataset.status}, code={code}"


def _load_canonical_gold_backtest_data(cfg: LoaderConfig) -> LoadedBacktestData:
    result = read_lightweight_input(
        LightweightInputRequest(
            dataset=cfg.dataset,
            lake_root=cfg.market_data_lake_root,
            start_date=_optional_date_string(cfg.start_date),
            end_date=_optional_date_string(cfg.end_date),
            adjustment_policy=cfg.adjustment_policy,
            quality_policy=cfg.quality_policy,
            input_mode="canonical_gold",
            legacy_flat_enabled=cfg.legacy_flat_enabled,
        )
    )
    if not result.ok or result.close_df is None:
        message = _format_lightweight_input_error(result.status, result.issues)
        if result.status == "quality_failed":
            raise DataQualityGateError(message)
        raise DataContractError(message)
    return LoadedBacktestData(
        close_df=result.close_df,
        universe=list(result.universe),
        calendar=list(result.calendar),
        metadata={
            **result.metadata,
            "input_mode": "canonical_gold",
            "remediation_job_spec": result.remediation_job_spec,
        },
    )


def _format_lightweight_input_error(status: str, issues: list[dict[str, Any]]) -> str:
    code = issues[0].get("code") if issues else status
    return f"canonical/gold 输入不可用: status={status}, code={code}"


def _optional_date_string(value: str | date | None) -> str | None:
    if value is None:
        return None
    return _to_date(value).isoformat()


def _validate_legacy_flat_path(cfg: LoaderConfig) -> None:
    if _is_repo_data_default(cfg.data_dir):
        raise DataContractError("旧 repo data 为 reference-only，禁止作为默认 fallback；请使用 input_mode=canonical_gold 或显式 external legacy_flat。")


def _is_repo_data_default(value: str | Path) -> bool:
    path = Path(value)
    return not path.is_absolute() and (path.parts == ("data",) or path.parts[:1] == ("data",))


def _coerce_config(config: LoaderConfig | dict[str, Any]) -> LoaderConfig:
    if isinstance(config, LoaderConfig):
        return config
    return LoaderConfig(**dict(config))


def _read_parquet_with_required_columns(dataset: str, path: Path) -> pd.DataFrame:
    try:
        frame = pd.read_parquet(path, engine="pyarrow")
    except Exception as exc:
        raise DataContractError(f"parquet 读取失败: {path}: {exc}") from exc
    missing = [column for column in DATASET_REQUIRED_COLUMNS[dataset] if column not in frame.columns]
    if missing:
        raise DataContractError(f"{dataset} 缺少必需字段: {', '.join(missing)}")
    return frame


def _load_quality_gate(cfg: LoaderConfig, paths: dict[str, Path], diag: Any) -> dict[str, Any]:
    quality_path = Path(cfg.quality_report_path)
    if quality_path.suffix.lower() == ".md":
        raise DataQualityGateError("Markdown 质量报告仅供人工阅读，不能作为 Data Loader 机器入口")
    if not quality_path.exists():
        if not cfg.allow_exploratory_recompute:
            raise DataQualityGateError(f"缺少质量报告: {quality_path}")
        diag.warning("exploratory_recompute", quality_report_path=quality_path)
        try:
            summary = calculate_quality(paths, cfg.manifest_path, _requested_range(cfg), date.today())
        except QualityError as exc:
            raise DataQualityGateError(str(exc)) from exc
        status = summary.quality_status
        return {
            "quality_status": status,
            "fetch_status": "not_applicable",
            "dataset_status": status,
            "manifest_run_id": summary.manifest_run_id,
            "quality_policy": cfg.quality_policy,
            "allow_warn": _allows_quality_warn(cfg.quality_policy),
            "quality_source": "memory_calculate_quality",
            "quality_decision_reason": f"exploratory_recompute_status_{status}",
            "derived_quality_summary": True,
            "missing_rate": float(summary.missing_rate),
            "failed_batch_count": int(summary.failed_batch_count),
            "last_successful_update_at": summary.last_successful_update_at,
            "data_freshness_trade_days": int(summary.data_freshness_trade_days),
            "data_freshness_calendar_days": int(summary.data_freshness_calendar_days),
            "warnings": ["quality_report_missing_exploratory_recompute"],
        }

    with quality_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    overall = next((row for row in rows if row.get("dataset") == "overall"), rows[-1] if rows else {})
    missing_fields = [
        field
        for field in QUALITY_REPORT_REQUIRED_FIELDS
        if field not in overall or str(overall.get(field) or "").strip() == ""
    ]
    if missing_fields:
        raise DataQualityGateError("质量报告缺少 CR-004 必需字段: " + ", ".join(missing_fields))
    policy = _normalise_quality_policy(cfg.quality_policy)
    status = str(overall.get("quality_status") or "").strip().lower()
    fetch_status = str(overall.get("fetch_status") or "").strip().lower()
    dataset_status = str(overall.get("dataset_status") or "").strip().lower()
    if status not in {"pass", "warn", "fail"}:
        raise DataQualityGateError(f"质量报告状态非法: {status!r}")
    if dataset_status in DATASET_STATUS_FAIL_VALUES or status == "fail":
        raise DataQualityGateError(
            "质量报告未通过: "
            f"quality_status={status}, dataset_status={dataset_status}, allow_warn={_allows_quality_warn(policy)}"
        )
    warnings = []
    if status == "warn" or dataset_status in DATASET_STATUS_WARN_VALUES:
        warnings.append("warn_minor_missing_rate")
        if not _allows_quality_warn(policy):
            raise DataQualityGateError(
                "质量报告为 warn，默认策略拒绝启动: "
                f"quality_policy={policy}, allow_warn=false"
            )
    if dataset_status not in (*DATASET_STATUS_PASS_VALUES, *DATASET_STATUS_WARN_VALUES):
        raise DataQualityGateError(f"dataset_status 非法或不可放行: {dataset_status!r}")
    if fetch_status not in FETCH_STATUS_SUCCESS_VALUES:
        warnings.append("warn_source_fetch_failed_but_local_valid")
    return {
        "quality_status": status,
        "fetch_status": fetch_status,
        "dataset_status": dataset_status,
        "manifest_run_id": overall.get("manifest_run_id", ""),
        "quality_policy": policy,
        "allow_warn": _allows_quality_warn(policy),
        "quality_source": "csv_report",
        "quality_decision_reason": _quality_decision_reason(status, dataset_status, policy),
        "derived_quality_summary": False,
        "missing_rate": _float_value(overall.get("missing_rate")),
        "failed_batch_count": _int_value(overall.get("failed_batch_count")),
        "last_successful_update_at": str(overall.get("last_successful_update_at") or ""),
        "data_freshness_trade_days": _int_value(overall.get("data_freshness_trade_days")),
        "data_freshness_calendar_days": _int_value(overall.get("data_freshness_calendar_days")),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _normalise_quality_policy(value: str) -> str:
    policy = str(value or DEFAULT_QUALITY_POLICY).replace("-", "_")
    if policy not in QUALITY_POLICY_VALUES:
        raise DataQualityGateError(f"未知 quality_policy: {value!r}")
    return policy


def _allows_quality_warn(policy: str) -> bool:
    return _normalise_quality_policy(policy) in {"allow_warn", "pass_warn"}


def _quality_decision_reason(status: str, dataset_status: str, policy: str) -> str:
    if status == "pass" and dataset_status in DATASET_STATUS_PASS_VALUES:
        return "quality_pass_dataset_available"
    if _allows_quality_warn(policy):
        return "quality_warn_allowed_explicitly"
    return "quality_policy_passed"


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise DataQualityGateError(f"质量报告数值字段非法: {value!r}") from None


def _int_value(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        raise DataQualityGateError(f"质量报告整数字段非法: {value!r}") from None


def _build_loader_metadata(
    *,
    cfg: LoaderConfig,
    paths: dict[str, Path],
    quality: dict[str, Any],
    index_members: pd.DataFrame,
    calendar: list[date],
    close_df: pd.DataFrame,
    universe: list[str],
) -> dict[str, Any]:
    requested_start, requested_end = _requested_range(cfg)
    universe_meta = _universe_metadata(index_members)
    warnings = list(quality.get("warnings", []))
    if universe_meta["pit_status"] == "non_pit_warn":
        warnings.append("warn_non_pit_universe")
    loaded_start = close_df.index.min().isoformat() if len(close_df.index) else ""
    loaded_end = close_df.index.max().isoformat() if len(close_df.index) else ""
    metadata = {
        "loader_schema_version": "1.0",
        "requested_start": requested_start.isoformat(),
        "requested_end": requested_end.isoformat(),
        "loaded_start": loaded_start,
        "loaded_end": loaded_end,
        "price_row_count": int(close_df.count().sum()),
        "universe_size": len(universe),
        "calendar_size": len(calendar),
        "adjustment_policy": cfg.adjustment_policy,
        "available_at_rule": cfg.decision_time_rule,
        "source_parquet_paths": {dataset: str(path) for dataset, path in paths.items()},
        "source_manifest_path": str(Path(cfg.manifest_path)),
        "source_quality_report_path": str(Path(cfg.quality_report_path)),
        "filtered_symbol_count": 0,
        "dropped_non_open_days": 0,
        **quality,
        **universe_meta,
        "warnings": list(dict.fromkeys(warnings)),
    }
    for field in LOADER_METADATA_FIELDS:
        metadata.setdefault(field, "" if field not in {"warnings", "source_parquet_paths"} else [] if field == "warnings" else {})
    return metadata


def _universe_metadata(frame: pd.DataFrame) -> dict[str, Any]:
    is_pit = bool(_bool_series(frame.get("is_pit_universe")).any()) if "is_pit_universe" in frame else False
    if is_pit:
        return {
            "is_pit_universe": True,
            "universe_mode": "pit",
            "pit_status": "valid_pit",
            "survivorship_bias_note": "",
        }
    return {
        "is_pit_universe": False,
        "universe_mode": "non_pit_snapshot",
        "pit_status": "non_pit_warn",
        "survivorship_bias_note": SURVIVORSHIP_BIAS_NOTE,
    }


def _build_calendar(frame: pd.DataFrame, cfg: LoaderConfig) -> list[date]:
    work = frame.copy()
    work["trade_date"] = _date_series(work["trade_date"])
    if "is_open" in work:
        work = work[_bool_series(work["is_open"])]
    start, end = _requested_range(cfg)
    dates = sorted({item for item in work["trade_date"].dropna().tolist() if start <= item <= end})
    if not dates:
        raise DataContractError("交易日历在请求区间内为空")
    return dates


def _build_universe(frame: pd.DataFrame, cfg: LoaderConfig) -> list[str]:
    work = frame.copy()
    if cfg.enable_pit_universe:
        _require_registry("index_members_pit")
    is_pit = _bool_series(work.get("is_pit_universe")).any() if "is_pit_universe" in work else False
    if is_pit:
        required = ("symbol", "index_code", "effective_date", "available_at", "is_member", "is_pit_universe")
        missing = [field for field in required if field not in work.columns]
        if missing:
            raise DataContractError("PIT 股票池字段不完整: " + ", ".join(missing))
        if work[list(required)].isna().any().any():
            raise DataContractError("PIT 股票池存在空字段")
        work = work[_bool_series(work["is_member"])]
    symbols = sorted({str(symbol).strip() for symbol in work["symbol"].dropna().tolist() if str(symbol).strip()})
    if not symbols:
        raise DataContractError("股票池为空")
    return symbols


def _build_close_matrix(
    prices: pd.DataFrame,
    calendar: list[date],
    universe: list[str],
    cfg: LoaderConfig,
) -> pd.DataFrame:
    work = prices.copy()
    work["trade_date"] = _date_series(work["trade_date"])
    work["symbol"] = work["symbol"].astype("string").str.strip()
    work["close"] = pd.to_numeric(work["close"], errors="coerce")
    if "adjustment_policy" in work:
        policies = sorted({str(value) for value in work["adjustment_policy"].fillna(cfg.adjustment_policy).unique()})
        if policies != [cfg.adjustment_policy]:
            raise DataContractError(f"复权口径不匹配: expected={cfg.adjustment_policy}, actual={policies}")
    start, end = _requested_range(cfg)
    work = work[(work["trade_date"] >= start) & (work["trade_date"] <= end)]
    work = work[work["symbol"].isin(universe)]
    close_df = work.pivot_table(index="trade_date", columns="symbol", values="close", aggfunc="last")
    close_df = close_df.reindex(index=calendar, columns=universe)
    if close_df.empty:
        raise DataContractError("close_df 为空")
    close_df.index.name = "trade_date"
    return close_df


def _requested_range(cfg: LoaderConfig) -> tuple[date, date]:
    if cfg.start_date is None or cfg.end_date is None:
        raise DataContractError("LoaderConfig 必须包含 start_date/end_date")
    start = _to_date(cfg.start_date)
    end = _to_date(cfg.end_date)
    if start > end:
        raise DataContractError("start_date 不得晚于 end_date")
    return start, end


def _validate_enhancement_gates(cfg: LoaderConfig) -> None:
    if cfg.enable_pit_universe:
        _require_registry("index_members_pit")
    if cfg.enable_trade_status:
        _require_registry("trade_status")
    if cfg.enable_limit_constraints:
        _require_registry("prices_limit")
    if cfg.enable_events:
        _require_registry("events")


def _require_registry(key: str) -> None:
    try:
        require_resolved_registry_key(key)
    except SourceRegistryError as exc:
        raise DataContractError(str(exc)) from exc


def _to_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(pd.Series([value]), errors="coerce")
    if parsed.isna().iloc[0]:
        raise DataContractError(f"日期不可解析: {value!r}")
    return parsed.dt.date.iloc[0]


def _date_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def _bool_series(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype=bool)
    def coerce(value: Any) -> bool:
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "y", "是"}
    return series.map(coerce).astype(bool)
__all__ = (
    "DataContractError",
    "DataLoaderError",
    "DataQualityGateError",
    "LoadedBacktestData",
    "LoaderConfig",
    "load_backtest_data",
    "load_research_backtest_data",
)
