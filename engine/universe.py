"""固定池与 PIT 股票池 Provider。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field as dataclass_field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from engine.diagnostics import start_diagnostic
from engine.source_registry import require_resolved_registry_key, SourceRegistryError
from market_data.contracts import (
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_STOCK_BASIC,
    PIT_STATUS_AVAILABLE,
    PIT_STATUS_FAILED,
    PIT_STATUS_INCOMPLETE,
    PIT_STATUS_NON_PIT_SNAPSHOT,
    READINESS_STATUS_AVAILABLE,
    READINESS_STATUS_QUALITY_FAILED,
    READINESS_STATUS_REQUIRED_MISSING,
    READINESS_STATUS_UNAVAILABLE,
)
from market_data.readers import ReaderResult


class UniverseError(Exception):
    """股票池 Provider 错误。"""


SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE = (
    "固定快照存在幸存者偏差，仅可用于探索或框架验证，不能声明 PIT 因子结论。"
)

_REQUEST_UNIVERSE_MODES = frozenset({"pit_required", "pit_optional", "fixed_snapshot"})
_REQUEST_ANALYSIS_MODES = frozenset({"research", "exploratory"})
_PIT_REQUIRED_FIELDS = frozenset({"index_code", "effective_date", "available_at"})


@dataclass(frozen=True, slots=True)
class UniverseRequest:
    """PIT / fixed universe resolver 请求。"""

    index_code: str = "399300.SZ"
    start_date: str | date | None = None
    end_date: str | date | None = None
    analysis_mode: str = "research"
    universe_mode: str = "fixed_snapshot"
    symbols: tuple[str, ...] | None = None
    decision_calendar: Sequence[str | date] | None = None
    universe: str = "csi300"


@dataclass(frozen=True, slots=True)
class UniverseIssue:
    """Universe resolver 结构化问题。"""

    code: str
    message: str
    severity: str = "ERROR"
    dataset: str | None = None
    field: str | None = None
    details: dict[str, Any] = dataclass_field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: _metadata_value(value) for key, value in payload.items() if value not in (None, {}, [])}


@dataclass(frozen=True, slots=True)
class UniverseMetadata:
    """research_input_v1 universe 子对象。"""

    universe: str
    index_code: str
    universe_mode: str
    is_pit_universe: bool
    pit_status: str
    readiness_status: str
    survivorship_bias_note: str
    symbol_count: int = 0
    symbols: list[str] = dataclass_field(default_factory=list)
    source_dataset: str | None = None
    issues: list[dict[str, Any]] = dataclass_field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _metadata_value(asdict(self))


@dataclass(frozen=True, slots=True)
class UniverseResolution:
    """Universe resolver 输出合同。"""

    status: str
    members: pd.DataFrame | None
    symbols: list[str]
    metadata: UniverseMetadata
    issues: list[UniverseIssue] = dataclass_field(default_factory=list)
    known_limitations: list[Any] = dataclass_field(default_factory=list)
    allowed_claims: list[str] = dataclass_field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _metadata_value(
            {
                "status": self.status,
                "symbols": self.symbols,
                "metadata": self.metadata.to_dict(),
                "issues": [issue.to_dict() for issue in self.issues],
                "known_limitations": self.known_limitations,
                "allowed_claims": self.allowed_claims,
            }
        )


@dataclass(slots=True)
class UniverseProvider:
    frame: pd.DataFrame
    mode: str = "fixed"

    def symbols_for_date(self, trade_date: str | date) -> list[str]:
        diag = start_diagnostic("universe", "STORY-009", {"mode": self.mode, "trade_date": trade_date})
        target = pd.to_datetime(trade_date).date()
        try:
            work = self.frame.copy()
            if self.mode == "fixed":
                symbols = sorted({str(symbol) for symbol in work["symbol"].dropna().tolist()})
                diag.warning("fixed_fallback", symbol_count=len(symbols))
                diag.end("success", symbol_count=len(symbols))
                return symbols
            _require_pit_registry()
            for column in ("symbol", "index_code", "effective_date", "available_at", "is_member", "is_pit_universe"):
                if column not in work.columns:
                    raise UniverseError(f"PIT 股票池缺少字段: {column}")
            work["effective_date"] = pd.to_datetime(work["effective_date"], errors="coerce").dt.date
            work["available_at"] = pd.to_datetime(work["available_at"], errors="coerce").dt.date
            work = work[(work["effective_date"] <= target) & (work["available_at"] <= target)]
            work = work[work["is_member"].fillna(True).astype(bool)]
            symbols = sorted({str(symbol) for symbol in work["symbol"].dropna().tolist()})
            diag.end("success", symbol_count=len(symbols))
            return symbols
        except Exception as exc:
            diag.error(exc)
            raise


def load_universe(path: str | Path, mode: str = "fixed") -> UniverseProvider:
    diag = start_diagnostic("universe", "STORY-009", {"path": Path(path), "mode": mode})
    try:
        if mode == "pit":
            _require_pit_registry()
        try:
            frame = pd.read_parquet(path, engine="pyarrow") if str(path).endswith(".parquet") else pd.read_csv(path)
        except FileNotFoundError as exc:
            raise UniverseError(f"股票池文件不存在: {Path(path)}") from exc
        if "symbol" not in frame.columns:
            raise UniverseError("股票池缺少 symbol 字段")
        diag.end("success", rows=len(frame))
        return UniverseProvider(frame=frame, mode=mode)
    except Exception as exc:
        diag.error(exc)
        raise


def resolve_universe(
    request: UniverseRequest | Mapping[str, Any],
    *,
    index_members_result: ReaderResult | None = None,
    stock_basic_result: ReaderResult | None = None,
    index_weights_result: ReaderResult | None = None,
) -> UniverseResolution:
    """解析 PIT / fixed 股票池，只消费调用方传入的 reader result。"""

    req = _coerce_universe_request(request)
    issues: list[UniverseIssue] = []
    start = _parse_date(req.start_date, "start_date", issues)
    end = _parse_date(req.end_date, "end_date", issues)
    if start is not None and end is not None and start > end:
        issues.append(UniverseIssue("invalid_date_range", "start_date 不得晚于 end_date。", field="start_date"))
    if req.universe_mode not in _REQUEST_UNIVERSE_MODES:
        issues.append(
            UniverseIssue(
                "invalid_universe_mode",
                f"universe_mode 必须属于 {sorted(_REQUEST_UNIVERSE_MODES)}。",
                field="universe_mode",
            )
        )
    if req.analysis_mode not in _REQUEST_ANALYSIS_MODES:
        issues.append(
            UniverseIssue(
                "invalid_analysis_mode",
                f"analysis_mode 必须属于 {sorted(_REQUEST_ANALYSIS_MODES)}。",
                field="analysis_mode",
            )
        )
    if issues:
        return _missing_resolution(req, "invalid_request", issues, "invalid_request")

    if req.symbols and req.universe_mode != "pit_required":
        return _fixed_resolution(
            req,
            _symbols_frame(req.symbols, req.index_code),
            issues=[
                UniverseIssue(
                    "fixed_snapshot_survivorship_bias",
                    SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE,
                    severity="INFO",
                    dataset=DATASET_INDEX_MEMBERS,
                )
            ],
            status="available_with_warnings",
            source_dataset="explicit_symbols",
        )
    if req.universe_mode == "fixed_snapshot":
        frame = _result_frame(index_members_result)
        if frame is None and req.symbols:
            frame = _symbols_frame(req.symbols, req.index_code)
        if frame is None:
            return _missing_resolution(
                req,
                "required_missing",
                [
                    *_reader_result_issues(index_members_result, DATASET_INDEX_MEMBERS),
                    UniverseIssue(
                        "index_members_required_missing",
                        "fixed_snapshot 请求缺少 index_members 或 explicit symbols。",
                        dataset=DATASET_INDEX_MEMBERS,
                    ),
                ],
                "missing",
            )
        return _fixed_resolution(
            req,
            frame,
            issues=[
                UniverseIssue(
                    "fixed_snapshot_survivorship_bias",
                    SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE,
                    severity="INFO",
                    dataset=DATASET_INDEX_MEMBERS,
                )
            ],
            status="available_with_warnings",
            source_dataset=DATASET_INDEX_MEMBERS,
        )

    pit = _pit_resolution(req, index_members_result, stock_basic_result, index_weights_result)
    if pit.status == "available" or req.universe_mode == "pit_required":
        return pit

    fallback_frame = _result_frame(index_members_result)
    if fallback_frame is None and req.symbols:
        fallback_frame = _symbols_frame(req.symbols, req.index_code)
    if fallback_frame is None:
        return pit
    return _fixed_resolution(
        req,
        fallback_frame,
        issues=[
            *pit.issues,
            UniverseIssue(
                "pit_optional_fell_back_to_fixed_snapshot",
                SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE,
                severity="WARNING",
                dataset=DATASET_INDEX_MEMBERS,
            ),
        ],
        status="available_with_warnings",
        source_dataset=DATASET_INDEX_MEMBERS,
    )


def _require_pit_registry() -> None:
    try:
        require_resolved_registry_key("index_members_pit")
    except SourceRegistryError as exc:
        raise UniverseError(str(exc)) from exc


def _pit_resolution(
    req: UniverseRequest,
    index_members_result: ReaderResult | None,
    stock_basic_result: ReaderResult | None,
    index_weights_result: ReaderResult | None,
) -> UniverseResolution:
    issues: list[UniverseIssue] = []
    issues.extend(_reader_result_issues(index_members_result, DATASET_INDEX_MEMBERS))
    frame = _result_frame(index_members_result)
    if frame is None:
        if _result_frame(index_weights_result) is not None:
            issues.append(
                UniverseIssue(
                    "index_weights_not_members",
                    "index_weights 不得替代完整 index_members。",
                    dataset=DATASET_INDEX_WEIGHTS,
                    details={"not_substituted_for": DATASET_INDEX_MEMBERS},
                )
            )
        if _result_frame(stock_basic_result) is not None:
            issues.append(
                UniverseIssue(
                    "stock_basic_not_pit_universe",
                    "stock_basic 当前快照不得证明 PIT universe。",
                    dataset=DATASET_STOCK_BASIC,
                )
            )
        issues.append(
            UniverseIssue(
                "pit_universe_required_missing",
                "严肃 PIT 股票池缺少可用 index_members。",
                dataset=DATASET_INDEX_MEMBERS,
            )
        )
        return _missing_resolution(req, "required_missing", issues, "missing")

    work = frame.copy()
    if "con_code" in work.columns and "symbol" not in work.columns:
        work["symbol"] = work["con_code"]
    missing_fields = sorted(_PIT_REQUIRED_FIELDS - set(work.columns))
    if "symbol" not in work.columns:
        missing_fields.append("symbol")
    if missing_fields:
        issues.append(
            UniverseIssue(
                "pit_required_columns_missing",
                "index_members 缺少 PIT 必需字段。",
                dataset=DATASET_INDEX_MEMBERS,
                field=",".join(missing_fields),
                details={"missing_fields": missing_fields},
            )
        )

    pit_values = _column_values(work, "pit_status")
    readiness_values = _column_values(work, "readiness_status")
    quality_status = _catalog_quality(index_members_result)
    is_pit_flag = "is_pit_universe" in work.columns and not work.empty and _bool_series(work["is_pit_universe"]).all()
    if pit_values != {PIT_STATUS_AVAILABLE} or not is_pit_flag or missing_fields:
        if quality_status == "pass":
            issues.append(
                UniverseIssue(
                    "quality_pass_not_pit_available",
                    "quality_status=pass 不等于 PIT available。",
                    dataset=DATASET_INDEX_MEMBERS,
                    details={"pit_status": sorted(pit_values), "is_pit_universe": bool(is_pit_flag)},
                )
            )
        if PIT_STATUS_FAILED in pit_values:
            issues.append(UniverseIssue("pit_failed", "index_members pit_status=pit_failed。", dataset=DATASET_INDEX_MEMBERS))
        elif PIT_STATUS_INCOMPLETE in pit_values or missing_fields:
            issues.append(UniverseIssue("pit_incomplete", "index_members PIT 字段或 as-of 证据不完整。", dataset=DATASET_INDEX_MEMBERS))
        elif PIT_STATUS_NON_PIT_SNAPSHOT in pit_values or not is_pit_flag:
            issues.append(UniverseIssue("non_pit_snapshot_for_research", "非 PIT snapshot 不可用于 PIT 研究股票池。", dataset=DATASET_INDEX_MEMBERS))

    if readiness_values and readiness_values != {READINESS_STATUS_AVAILABLE}:
        issues.append(
            UniverseIssue(
                "readiness_not_available",
                "index_members readiness_status 不全为 available。",
                dataset=DATASET_INDEX_MEMBERS,
                details={"readiness_status": sorted(readiness_values)},
            )
        )

    if issues:
        pit_status = _pit_status_from_issues(issues, pit_values)
        readiness = _readiness_from_issues(issues)
        issues.append(
            UniverseIssue(
                "pit_universe_required_missing",
                "PIT required 请求不可用，必须 fail，不得伪装 PIT。",
                dataset=DATASET_INDEX_MEMBERS,
            )
        )
        return _missing_resolution(req, "gate_failed", issues, pit_status, readiness_status=readiness)

    decisions = _decision_dates(req, work)
    if not decisions:
        issues.append(UniverseIssue("decision_calendar_missing", "缺少可验证的 decision calendar。", dataset=DATASET_INDEX_MEMBERS))
        issues.append(UniverseIssue("pit_universe_required_missing", "PIT required 请求不可用，必须 fail。", dataset=DATASET_INDEX_MEMBERS))
        return _missing_resolution(req, "gate_failed", issues, PIT_STATUS_INCOMPLETE)

    members = _asof_members(work, decisions, req.index_code)
    if members.empty:
        issues.append(UniverseIssue("pit_asof_empty", "PIT as-of 过滤后股票池为空。", dataset=DATASET_INDEX_MEMBERS))
        issues.append(UniverseIssue("pit_universe_required_missing", "PIT required 请求不可用，必须 fail。", dataset=DATASET_INDEX_MEMBERS))
        return _missing_resolution(req, "gate_failed", issues, PIT_STATUS_INCOMPLETE)

    symbols = sorted({str(symbol) for symbol in members["symbol"].dropna().tolist() if str(symbol)})
    metadata = UniverseMetadata(
        universe=req.universe,
        index_code=req.index_code,
        universe_mode="pit",
        is_pit_universe=True,
        pit_status=PIT_STATUS_AVAILABLE,
        readiness_status=READINESS_STATUS_AVAILABLE,
        survivorship_bias_note="",
        symbol_count=len(symbols),
        symbols=symbols,
        source_dataset=DATASET_INDEX_MEMBERS,
        issues=[],
    )
    return UniverseResolution(
        status="available",
        members=members,
        symbols=symbols,
        metadata=metadata,
        issues=[],
        known_limitations=[],
        allowed_claims=["framework_validation", "exploratory_analysis", "pit_universe_research"],
    )


def _fixed_resolution(
    req: UniverseRequest,
    frame: pd.DataFrame,
    *,
    issues: list[UniverseIssue],
    status: str,
    source_dataset: str,
) -> UniverseResolution:
    symbols = _symbols_from_frame(frame)
    members = _fixed_members_frame(symbols, req.index_code)
    metadata = UniverseMetadata(
        universe=req.universe,
        index_code=req.index_code,
        universe_mode="fixed_snapshot",
        is_pit_universe=False,
        pit_status=PIT_STATUS_NON_PIT_SNAPSHOT,
        readiness_status="warn",
        survivorship_bias_note=SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE,
        symbol_count=len(symbols),
        symbols=symbols,
        source_dataset=source_dataset,
        issues=[issue.to_dict() for issue in issues],
    )
    return UniverseResolution(
        status=status,
        members=members,
        symbols=symbols,
        metadata=metadata,
        issues=issues,
        known_limitations=[
            {
                "code": "fixed_snapshot_survivorship_bias",
                "survivorship_bias_note": SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE,
            }
        ],
        allowed_claims=["framework_validation", "fixed_snapshot_exploration"],
    )


def _missing_resolution(
    req: UniverseRequest,
    status: str,
    issues: list[UniverseIssue],
    pit_status: str,
    *,
    readiness_status: str | None = None,
) -> UniverseResolution:
    metadata = UniverseMetadata(
        universe=req.universe,
        index_code=req.index_code,
        universe_mode="missing",
        is_pit_universe=False,
        pit_status=pit_status,
        readiness_status=readiness_status or READINESS_STATUS_REQUIRED_MISSING,
        survivorship_bias_note=SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE,
        symbol_count=0,
        symbols=[],
        source_dataset=DATASET_INDEX_MEMBERS,
        issues=[issue.to_dict() for issue in issues],
    )
    return UniverseResolution(
        status=status,
        members=None,
        symbols=[],
        metadata=metadata,
        issues=issues,
        known_limitations=[
            {
                "code": "pit_universe_unavailable",
                "survivorship_bias_note": SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE,
            }
        ],
        allowed_claims=[],
    )


def _coerce_universe_request(request: UniverseRequest | Mapping[str, Any]) -> UniverseRequest:
    if isinstance(request, UniverseRequest):
        return request
    values = dict(request)
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(symbol).strip() for symbol in values["symbols"] if str(symbol).strip())
    return UniverseRequest(**values)


def _parse_date(value: str | date | datetime | None, field_name: str, issues: list[UniverseIssue]) -> date | None:
    if value is None:
        issues.append(UniverseIssue("required_field_missing", f"{field_name} 必须显式传入。", field=field_name))
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(pd.Series([value]), errors="coerce")
    if parsed.isna().iloc[0]:
        issues.append(UniverseIssue("invalid_date", f"{field_name} 必须是可解析日期。", field=field_name))
        return None
    return parsed.dt.date.iloc[0]


def _result_frame(result: ReaderResult | None) -> pd.DataFrame | None:
    if result is None or result.status != "available" or result.frame is None:
        return None
    return result.frame.copy()


def _reader_result_issues(result: ReaderResult | None, dataset: str) -> list[UniverseIssue]:
    if result is None:
        return []
    issues = [
        UniverseIssue(
            str(issue.get("code", f"{dataset}_issue")),
            str(issue.get("message", f"{dataset} reader issue: {issue.get('code', 'unknown')}")),
            severity=str(issue.get("severity", "ERROR")),
            dataset=str(issue.get("dataset", dataset)),
            details={key: value for key, value in issue.items() if key not in {"code", "message", "severity", "dataset"}},
        )
        for issue in result.issues
    ]
    if result.status == "quality_failed":
        issues.append(UniverseIssue("index_members_quality_failed", "index_members quality_failed。", dataset=dataset))
    elif result.status not in {"available", ""}:
        issues.append(
            UniverseIssue(
                "index_members_required_missing",
                f"index_members 不可用: status={result.status}。",
                dataset=dataset,
                details={"reader_status": result.status},
            )
        )
    return issues


def _catalog_quality(result: ReaderResult | None) -> str:
    entry = None if result is None else result.catalog_entry
    return str(getattr(entry, "quality_status", "") or "")


def _column_values(frame: pd.DataFrame, column: str) -> set[str]:
    if column not in frame.columns:
        return set()
    return {str(value).strip() for value in frame[column].dropna().tolist() if str(value).strip()}


def _bool_series(series: pd.Series) -> pd.Series:
    def coerce(value: Any) -> bool:
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "y", "是"}

    return series.map(coerce).astype(bool)


def _decision_dates(req: UniverseRequest, frame: pd.DataFrame) -> list[date]:
    raw_values: Sequence[Any]
    if req.decision_calendar:
        raw_values = list(req.decision_calendar)
    elif "trade_date" in frame.columns:
        raw_values = frame["trade_date"].dropna().tolist()
    else:
        raw_values = [req.start_date, req.end_date]
    dates = pd.to_datetime(pd.Series(list(raw_values)), errors="coerce").dt.date.dropna().tolist()
    start = pd.to_datetime(pd.Series([req.start_date]), errors="coerce").dt.date.iloc[0]
    end = pd.to_datetime(pd.Series([req.end_date]), errors="coerce").dt.date.iloc[0]
    return sorted({item for item in dates if start <= item <= end})


def _asof_members(frame: pd.DataFrame, decisions: Sequence[date], index_code: str) -> pd.DataFrame:
    work = frame.copy()
    work["symbol"] = work["symbol"].astype("string").str.strip()
    work["index_code"] = work["index_code"].astype("string").str.strip()
    work["effective_date"] = pd.to_datetime(work["effective_date"], errors="coerce").dt.date
    work["available_at"] = pd.to_datetime(work["available_at"], errors="coerce").dt.date
    if "out_date" in work.columns:
        work["out_date"] = pd.to_datetime(work["out_date"], errors="coerce").dt.date
    if "is_member" in work.columns:
        member_mask = _bool_series(work["is_member"])
    else:
        member_mask = pd.Series(True, index=work.index)
    work = work[(work["index_code"] == str(index_code)) & member_mask]
    rows: list[pd.DataFrame] = []
    for decision in decisions:
        visible = work[(work["effective_date"] <= decision) & (work["available_at"] <= decision)].copy()
        if "out_date" in visible.columns:
            visible = visible[visible["out_date"].isna() | (visible["out_date"] > decision)]
        if visible.empty:
            continue
        visible["trade_date"] = decision
        rows.append(visible)
    if not rows:
        return pd.DataFrame(columns=["trade_date", "index_code", "symbol"])
    output = pd.concat(rows, ignore_index=True)
    return output.drop_duplicates(subset=["trade_date", "index_code", "symbol"]).reset_index(drop=True)


def _symbols_from_frame(frame: pd.DataFrame) -> list[str]:
    symbol_column = "symbol" if "symbol" in frame.columns else "con_code" if "con_code" in frame.columns else ""
    if not symbol_column:
        return []
    work = frame.copy()
    if "is_member" in work.columns:
        work = work[_bool_series(work["is_member"])]
    return sorted({str(symbol).strip() for symbol in work[symbol_column].dropna().tolist() if str(symbol).strip()})


def _symbols_frame(symbols: Sequence[str], index_code: str) -> pd.DataFrame:
    return pd.DataFrame({"index_code": index_code, "symbol": [str(symbol).strip() for symbol in symbols if str(symbol).strip()]})


def _fixed_members_frame(symbols: Sequence[str], index_code: str) -> pd.DataFrame:
    return pd.DataFrame({"index_code": index_code, "symbol": list(symbols), "is_member": True})


def _pit_status_from_issues(issues: Sequence[UniverseIssue], pit_values: set[str]) -> str:
    codes = {issue.code for issue in issues}
    if "pit_failed" in codes or PIT_STATUS_FAILED in pit_values:
        return PIT_STATUS_FAILED
    if "non_pit_snapshot_for_research" in codes or PIT_STATUS_NON_PIT_SNAPSHOT in pit_values:
        return PIT_STATUS_NON_PIT_SNAPSHOT
    if "pit_incomplete" in codes or PIT_STATUS_INCOMPLETE in pit_values:
        return PIT_STATUS_INCOMPLETE
    return "missing"


def _readiness_from_issues(issues: Sequence[UniverseIssue]) -> str:
    codes = {issue.code for issue in issues}
    if "index_members_quality_failed" in codes:
        return READINESS_STATUS_QUALITY_FAILED
    if "readiness_not_available" in codes:
        return READINESS_STATUS_UNAVAILABLE
    return READINESS_STATUS_REQUIRED_MISSING


def _metadata_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _metadata_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_metadata_value(item) for item in value]
    if isinstance(value, tuple):
        return [_metadata_value(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


__all__ = (
    "SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE",
    "UniverseError",
    "UniverseIssue",
    "UniverseMetadata",
    "UniverseProvider",
    "UniverseRequest",
    "UniverseResolution",
    "load_universe",
    "resolve_universe",
)
