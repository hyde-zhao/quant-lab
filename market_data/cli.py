"""market_data offline CLI。"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from .contracts import (
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    DATASETS,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    INTERFACE_TRADE_CALENDAR_DAILY,
    SOURCE_FAKE,
    SOURCE_JQDATA,
    SOURCE_TUSHARE,
)
from .lake_layout import LakeLayout


class CliUsageError(ValueError):
    exit_code = 2
    error_type = "usage_error"


class RealSourceDisabledError(CliUsageError):
    error_type = "source_disabled"


class LakeRootMissingError(CliUsageError):
    error_type = "lake_root_missing"


class StructuredCliError(CliUsageError):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type


class CliExecutionError(RuntimeError):
    exit_code = 3
    error_type = "execution_error"


class QualityReportShapeError(CliExecutionError):
    error_type = "quality_report_shape_error"


QUALITY_REQUIRED_FIELDS: tuple[str, ...] = (
    "run_id",
    "generated_at",
    "dataset",
    "source_name",
    "source_interface",
    "target_dataset",
    "input_config_hash",
    "quality_status",
    "fetch_status",
    "dataset_status",
    "issue_count",
    "requested_start",
    "requested_end",
    "actual_start",
    "actual_end",
    "requested_symbols_count",
    "actual_symbols_count",
    "open_trade_dates_count",
    "expected_rows",
    "actual_rows",
    "missing_rows",
    "missing_rate",
    "denominator_mode",
    "thresholds_json",
    "missing_required_fields_json",
    "duplicate_keys_json",
    "negative_price_rows_json",
    "coverage_gaps_json",
    "manifest_inconsistencies_json",
    "warnings_json",
    "is_pit_universe",
    "universe_mode",
    "pit_status",
    "survivorship_bias_note",
)


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _require_prices(dataset: str) -> None:
    if dataset != DATASET_PRICES:
        raise CliUsageError(f"本批次仅支持 dataset={DATASET_PRICES}: {dataset}")


def _require_symbols(symbols: Sequence[str]) -> None:
    if not symbols:
        raise CliUsageError("--symbols 不能为空")


def _serializable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serializable(item) for item in value]
    return value


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(_serializable(payload), ensure_ascii=False, sort_keys=True))


def _error_payload(error: Exception) -> dict[str, Any]:
    return {
        "ok": False,
        "error_type": getattr(error, "error_type", error.__class__.__name__),
        "error_message": str(error),
    }


def _run_id(args: argparse.Namespace) -> str:
    return args.run_id or "run-cli"


def _batch_id(args: argparse.Namespace) -> str:
    return args.batch_id or "b1"


def _date_range(args: argparse.Namespace) -> tuple[str, str]:
    if not args.start_date or not args.end_date:
        raise CliUsageError("--start-date 与 --end-date 必须同时提供")
    if args.start_date > args.end_date:
        raise CliUsageError("--start-date 不能晚于 --end-date")
    return args.start_date, args.end_date


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise CliUsageError(f"布尔参数无法解析: {value}")


def _resolve_lake_root(explicit: str | None, *, required: bool = False) -> str:
    if explicit:
        return explicit
    env_value = os.environ.get("MARKET_DATA_LAKE_ROOT")
    if env_value:
        return env_value
    if required:
        raise LakeRootMissingError(
            "lake root 未配置；请传 --lake-root 或设置 MARKET_DATA_LAKE_ROOT"
        )
    return "data/market_data"


def _plan_payload(args: argparse.Namespace) -> dict[str, Any]:
    _require_prices(args.dataset)
    symbols = _split_csv(args.symbols)
    _require_symbols(symbols)
    start, end = _date_range(args)
    return {
        "ok": True,
        "command": "plan",
        "dataset": args.dataset,
        "source": args.source,
        "interface": args.interface,
        "symbols": symbols,
        "start_date": start,
        "end_date": end,
        "batch_count": 1,
        "offline": True,
        "requires_enable_real_source": args.source != SOURCE_FAKE,
    }


def cmd_plan(args: argparse.Namespace) -> dict[str, Any]:
    return _plan_payload(args)


def _p0_datasets(args: argparse.Namespace) -> tuple[str, ...]:
    from .runtime import CR014_P0_DATASETS

    return tuple(_split_csv(getattr(args, "datasets", None)) or CR014_P0_DATASETS)


def _p0_lifecycle_contract(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "as_of_trade_date": getattr(args, "as_of_trade_date", None),
        "coverage_denominator_ref": getattr(args, "coverage_denominator_ref", None),
        "lifecycle_denominator_ref": getattr(args, "coverage_denominator_ref", None),
    }


def _p0_plan_from_args(args: argparse.Namespace):
    from .runtime import P0DatasetPlanRequest, build_p0_plan

    request = P0DatasetPlanRequest(
        datasets=_p0_datasets(args),
        start_date=getattr(args, "start_date", None),
        end_date=getattr(args, "end_date", None),
        as_of_trade_date=getattr(args, "as_of_trade_date", None),
        coverage_denominator_ref=getattr(args, "coverage_denominator_ref", None),
    )
    return build_p0_plan(request, lifecycle_contract=_p0_lifecycle_contract(args))


def cmd_p0_plan(args: argparse.Namespace) -> dict[str, Any]:
    plan = _p0_plan_from_args(args)
    return {"ok": plan.status == "dry_run", "command": "p0-plan", **plan.to_dict()}


def cmd_p0_run(args: argparse.Namespace) -> dict[str, Any]:
    from .runtime import DevGate, RunAuthorization, run_p0_batches

    plan = _p0_plan_from_args(args)
    authorization = RunAuthorization(
        authorization_id=getattr(args, "authorization_id", None),
        allowed_sources=tuple(_split_csv(getattr(args, "allowed_sources", None))),
        allowed_interfaces=tuple(_split_csv(getattr(args, "allowed_interfaces", None))),
        approved_by=getattr(args, "approved_by", None),
        scope={
            "datasets": list(plan.datasets),
            "start_date": getattr(args, "start_date", None),
            "end_date": getattr(args, "end_date", None),
        },
    )
    dev_gate = DevGate(
        cp5_approved=bool(getattr(args, "cp5_approved", False)),
        lld_confirmed=bool(getattr(args, "lld_confirmed", False)),
        dependencies_satisfied=bool(getattr(args, "dependencies_satisfied", False)),
        file_conflict_free=bool(getattr(args, "file_conflict_free", False)),
    )
    result = run_p0_batches(plan, authorization=authorization, dev_gate=dev_gate)
    return {"ok": result.run_allowed, "command": "p0-run", **result.to_dict()}


def _s09_authorization_payload(args: argparse.Namespace) -> dict[str, Any]:
    from .windowed_run import S09_DEFAULT_PILOT_END, S09_DEFAULT_PILOT_START

    return {
        "authorization_id": getattr(args, "authorization_id", None),
        "datasets": _split_csv(getattr(args, "datasets", None))
        or [getattr(args, "dataset", DATASET_PRICES)],
        "date_range": {
            "start_date": getattr(args, "start_date", None) or S09_DEFAULT_PILOT_START,
            "end_date": getattr(args, "end_date", None) or S09_DEFAULT_PILOT_END,
        },
        "source_interface_allowlist": [
            {
                "source": getattr(args, "source", None) or SOURCE_TUSHARE,
                "interface": getattr(args, "interface", None) or INTERFACE_PRICES_DAILY,
            }
        ],
        "lake_root": getattr(args, "lake_root", None),
        "window_policy": {
            "policy_type": getattr(args, "window_policy", None) or "month",
            "trading_day_chunk_size": int(getattr(args, "trading_day_chunk_size", 20) or 20),
            "stop_on_error": bool(getattr(args, "stop_on_error", False)),
        },
        "resume_policy": {
            "skip_success": True,
            "retry_failed": True,
            "conflict_strategy": "fail_closed",
        },
        "rollback_policy": {
            "mode": "preview_only",
            "execute_authorized": False,
        },
        "credential_source_policy": {
            "policy_type": "env",
            "env_var_names": _split_csv(getattr(args, "credential_envs", None)),
            "redact_values": True,
        },
        "approved_by": getattr(args, "approved_by", None),
    }


def _s09_dev_gate_from_args(args: argparse.Namespace):
    from .runtime import DevGate

    return DevGate(
        cp5_approved=bool(getattr(args, "cp5_approved", False)),
        lld_confirmed=bool(getattr(args, "lld_confirmed", False)),
        dependencies_satisfied=bool(getattr(args, "dependencies_satisfied", False)),
        file_conflict_free=bool(getattr(args, "file_conflict_free", False)),
    )


def _s09_gate_payload(args: argparse.Namespace) -> dict[str, Any]:
    from .runtime import evaluate_s09_windowed_run_gate
    from .windowed_run import build_s09_authorization

    auth = build_s09_authorization(_s09_authorization_payload(args))
    gate = evaluate_s09_windowed_run_gate(
        authorization=auth,
        dev_gate=_s09_dev_gate_from_args(args),
        cp5_state={
            "implementation_allowed": bool(getattr(args, "implementation_allowed", False)),
            "real_run_authorized": False,
        },
        execution_mode="real",
        allow_fake_provider=False,
    )
    return {
        "authorization": auth.to_dict(),
        "run_gate": gate.to_dict(),
    }


def cmd_s09_plan(args: argparse.Namespace) -> dict[str, Any]:
    from .windowed_run import (
        S09_DEFAULT_PILOT_END,
        S09_DEFAULT_PILOT_START,
        build_s09_authorization,
        plan_windowed_run,
    )

    auth = build_s09_authorization(_s09_authorization_payload(args))
    gate_payload = _s09_gate_payload(args)
    plan = plan_windowed_run(auth)
    return {
        "ok": plan.status == "planned",
        "command": "s09-plan",
        "default_pilot_window": {
            "start_date": S09_DEFAULT_PILOT_START,
            "end_date": S09_DEFAULT_PILOT_END,
        },
        "real_run_authorized": False,
        "plan": plan.to_dict(),
        **gate_payload,
    }


def cmd_s09_run_gate(args: argparse.Namespace) -> dict[str, Any]:
    gate_payload = _s09_gate_payload(args)
    return {
        "ok": False,
        "command": "s09-run-gate",
        "real_run_authorized": False,
        "provider_fetch": 0,
        "lake_write": 0,
        "credential_read": 0,
        **gate_payload,
    }


def cmd_s09_rollback_preview(args: argparse.Namespace) -> dict[str, Any]:
    from .windowed_run import WindowedRunSummary, rollback_windowed_run

    summary = WindowedRunSummary(
        status="preview_input_empty",
        authorization_id=getattr(args, "authorization_id", None),
        windows_total=0,
        succeeded_count=0,
        failed_count=0,
        skipped_count=0,
        conflict_count=0,
        records=(),
        permission_counters={},
    )
    preview = rollback_windowed_run(summary, execute=False, execute_authorized=False)
    return {
        "ok": True,
        "command": "s09-rollback-preview",
        "real_run_authorized": False,
        **preview.to_dict(),
    }


def _p0_manifest_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "run_id": getattr(args, "run_id", None) or "run-cr014-s03",
        "batch_id": getattr(args, "batch_id", None) or "p0-01",
        "dataset": getattr(args, "dataset", None) or DATASET_PRICES,
        "source": getattr(args, "source", None) or "fixture",
        "source_interface": getattr(args, "source_interface", None) or "fixture.p0",
        "schema_hash": getattr(args, "schema_hash", None) or "schema-fixture",
        "row_count": int(getattr(args, "row_count", 0) or 0),
        "quality_status": getattr(args, "quality_status", None) or "pass",
        "readiness_status": getattr(args, "readiness_status", None) or "available",
        "lineage_checksum": getattr(args, "lineage_checksum", None) or "lineage-fixture",
        "lifecycle_denominator_ref": getattr(args, "coverage_denominator_ref", None)
        or "cr014-s01-denominator",
        "candidate_path": getattr(args, "candidate_path", None)
        or "candidate://cr014-s03/p0",
    }


def cmd_p0_normalize(args: argparse.Namespace) -> dict[str, Any]:
    from .normalization import normalize_p0_candidate

    candidate = normalize_p0_candidate(
        _p0_manifest_payload(args),
        raw_ref=getattr(args, "raw_ref", None),
    )
    return {
        "ok": not candidate.error_codes,
        "command": "p0-normalize",
        **candidate.to_dict(),
    }


def cmd_p0_replay(args: argparse.Namespace) -> dict[str, Any]:
    from .normalization import replay_p0_candidate

    manifest_store = [_p0_manifest_payload(args)] if getattr(args, "manifest_present", False) else None
    result = replay_p0_candidate(
        getattr(args, "run_id", None) or "run-cr014-s03",
        getattr(args, "batch_id", None) or "p0-01",
        manifest_store,
        dataset=getattr(args, "dataset", None) or DATASET_PRICES,
    )
    return {"ok": not result.error_codes, "command": "p0-replay", **result.to_dict()}


def cmd_p0_validate(args: argparse.Namespace) -> dict[str, Any]:
    from .validation import validate_p0_candidate

    candidate = {
        "dataset": getattr(args, "dataset", None) or DATASET_PRICES,
        "run_id": getattr(args, "run_id", None) or "run-cr014-s03",
        "candidate_path": getattr(args, "candidate_path", None)
        or "candidate://cr014-s03/p0",
        "status": "candidate_unpublished",
        "quality_status": getattr(args, "quality_status", None) or "pass",
        "readiness_status": getattr(args, "readiness_status", None) or "available",
    }
    result = validate_p0_candidate(candidate, lifecycle=_p0_lifecycle_contract(args))
    return {"ok": result.passed, "command": "p0-validate", **result.to_dict()}


def _p0_candidate_pointer(args: argparse.Namespace) -> dict[str, Any]:
    known_limitations = []
    return {
        "dataset": getattr(args, "dataset", None) or DATASET_PRICES,
        "schema_version": "1.0",
        "coverage_start": getattr(args, "start_date", None),
        "coverage_end": getattr(args, "end_date", None),
        "coverage_denominator": int(getattr(args, "coverage_denominator", 0) or 0),
        "latest_manifest_run_id": getattr(args, "run_id", None) or "run-cr014-s03",
        "lineage_checksum": getattr(args, "lineage_checksum", None) or "lineage-fixture",
        "published_at": getattr(args, "published_at", None) or "dry-run-only",
        "known_limitations": known_limitations,
        "universe_scope": getattr(args, "universe_scope", None) or "all_a_share",
        "as_of_trade_date": getattr(args, "as_of_trade_date", None),
        "quality_status": getattr(args, "quality_status", None) or "pass",
        "readiness_status": getattr(args, "readiness_status", None) or "available",
    }


def cmd_p0_publish(args: argparse.Namespace) -> dict[str, Any]:
    from .validation import publish_p0_candidate, validate_p0_candidate

    pointer = _p0_candidate_pointer(args)
    validation = validate_p0_candidate(pointer, lifecycle=_p0_lifecycle_contract(args))
    result = publish_p0_candidate(
        pointer,
        validation,
        {
            "publish": bool(getattr(args, "publish", False)),
            "approval_token": getattr(args, "approval_token", None),
            "approved_by": getattr(args, "approved_by", None),
            "reason": getattr(args, "reason", None),
        },
        manifest=_p0_manifest_payload(args),
        lifecycle={
            "coverage_denominator": pointer["coverage_denominator"],
            "lifecycle_denominator_ref": getattr(args, "coverage_denominator_ref", None)
            or "cr014-s01-denominator",
        },
        dry_run=True,
    )
    payload = result.to_dict()
    return {"ok": bool(payload.get("publish_allowed")), "command": "p0-publish", **payload}


def cmd_p0_read(args: argparse.Namespace) -> dict[str, Any]:
    from .validation import read_p0_current_truth

    scope = getattr(args, "read_scope", None) or "published_current_truth"
    pointer = _p0_candidate_pointer(args) if getattr(args, "pointer_present", False) else None
    audit = (
        {"candidate_audit_path": getattr(args, "candidate_audit_path", None) or "audit://cr014-s03"}
        if getattr(args, "candidate_audit", False)
        else None
    )
    result = read_p0_current_truth(
        getattr(args, "dataset", None) or DATASET_PRICES,
        pointer,
        read_scope=scope,
        candidate_audit_evidence=audit,
    )
    return {"ok": result.allowed, "command": "p0-read", **result.to_dict()}


def cmd_p0_query(args: argparse.Namespace) -> dict[str, Any]:
    payload = cmd_p0_read(args)
    payload["command"] = "p0-query"
    return payload


HS300_BACKFILL_ERROR_ENUM: tuple[str, ...] = (
    "source_disabled",
    "interface_not_allowed",
    "missing_credential",
    "quota_or_rate_limited",
    "remote_error",
    "schema_mismatch",
    "quality_failed",
    "lake_root_invalid",
    "resume_conflict",
)


TUSHARE_FIRST_ERROR_ENUM: tuple[str, ...] = (
    "source_disabled",
    "interface_not_allowed",
    "unknown_dataset",
    "invalid_date_range",
    "missing_credential",
    "quota_or_rate_limited",
    "remote_error",
    "schema_mismatch",
    "lineage_unavailable",
    "quality_failed",
    "lake_root_missing",
    "lake_root_invalid",
    "old_data_reference_only",
    "resume_conflict",
)

JQDATA_ACQUIRE_ERROR_ENUM: tuple[str, ...] = (
    "source_disabled",
    "interface_not_allowed",
    "unknown_dataset",
    "invalid_date_range",
    "missing_credential",
    "permission_denied",
    "quota_or_rate_limited",
    "remote_error",
    "schema_mismatch",
    "lineage_unavailable",
    "quality_failed",
    "lake_root_missing",
    "lake_root_invalid",
    "old_data_reference_only",
    "resume_conflict",
)

PRICES_LONG_HORIZON_ERROR_ENUM: tuple[str, ...] = (
    "source_disabled",
    "invalid_date_range",
    "lake_root_missing",
    "old_data_reference_only",
    "universe_missing",
    "batch_size_invalid",
    "duplicate_symbol",
    "adjustment_policy_conflict",
    "trade_calendar_required",
)

BENCHMARK_CALENDAR_BACKFILL_ERROR_ENUM: tuple[str, ...] = (
    "source_disabled",
    "invalid_date_range",
    "lake_root_missing",
    "lake_root_invalid",
    "old_data_reference_only",
    "interface_not_allowed",
    "missing_credential",
    "schema_mismatch",
    "lineage_unavailable",
    "quality_failed",
    "calendar_missing",
    "coverage_gap",
    "price_benchmark_overlap_missing",
    "resume_conflict",
)

TUSHARE_FIRST_DATASET_INTERFACES: dict[str, str] = {
    DATASET_PRICES: INTERFACE_PRICES_DAILY,
    DATASET_ADJ_FACTOR: INTERFACE_PRICES_ADJ_FACTOR,
    DATASET_HS300_INDEX: INTERFACE_HS300_INDEX_DAILY,
    DATASET_TRADE_CALENDAR: INTERFACE_TRADE_CALENDAR_DAILY,
    DATASET_INDEX_MEMBERS: INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    DATASET_INDEX_WEIGHTS: INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    DATASET_STOCK_BASIC: INTERFACE_STOCK_BASIC_SNAPSHOT,
    DATASET_TRADE_STATUS: INTERFACE_TRADE_STATUS_DAILY,
    DATASET_PRICES_LIMIT: INTERFACE_PRICES_LIMIT_DAILY,
    DATASET_EVENTS: INTERFACE_EVENTS_DISCLOSURE,
}

JQDATA_DATASET_INTERFACES: dict[str, str] = {
    DATASET_INDEX_MEMBERS: INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    DATASET_INDEX_WEIGHTS: INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    DATASET_STOCK_BASIC: INTERFACE_STOCK_BASIC_SNAPSHOT,
    DATASET_TRADE_STATUS: INTERFACE_TRADE_STATUS_DAILY,
    DATASET_PRICES_LIMIT: INTERFACE_PRICES_LIMIT_DAILY,
    DATASET_EVENTS: INTERFACE_EVENTS_DISCLOSURE,
}


def _jqdata_provider_interface(source_interface: str) -> str:
    return {
        INTERFACE_INDEX_MEMBERS_SNAPSHOT: "get_index_stocks",
        INTERFACE_INDEX_WEIGHTS_SNAPSHOT: "get_index_weights",
        INTERFACE_STOCK_BASIC_SNAPSHOT: "get_all_securities",
        INTERFACE_TRADE_STATUS_DAILY: "get_price+get_extras",
        INTERFACE_PRICES_LIMIT_DAILY: "get_price",
        INTERFACE_EVENTS_DISCLOSURE: "get_extras",
    }.get(source_interface, source_interface)


@dataclass(frozen=True, slots=True)
class TushareFirstRunSpec:
    dataset: str
    start_date: str
    end_date: str
    lake_root: str
    source_interface: str | None = None
    source: str = SOURCE_TUSHARE
    credential_env: str = "TUSHARE_TOKEN"
    run_id: str = "run-tushare-first"
    batch_id: str = "b1"
    dry_run: bool = True
    index_code: str = "399300.SZ"
    symbol: str | None = None
    exchange: str = "SSE"
    list_status: str = "L"
    fields: str | None = None
    symbols: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class JQDataRunSpec:
    dataset: str
    start_date: str
    end_date: str
    lake_root: str
    source: str = SOURCE_JQDATA
    source_interface: str | None = None
    credential_env_username: str = "JQDATA_USERNAME"
    credential_env_password: str = "JQDATA_PASSWORD"
    run_id: str = "run-jqdata-index-members"
    batch_id: str = "b1"
    dry_run: bool = True
    index_code: str = "399300.SZ"
    symbols: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PricesLongHorizonPlanSpec:
    start_date: str
    end_date: str
    lake_root: str
    symbols: tuple[str, ...] = ()
    universe_source: str | None = None
    symbol_batch_size: int = 100
    slice_days: int = 31
    run_id: str = "run-prices-long-horizon"
    adjustment_policy: str = "qfq"
    dry_run: bool = True
    source: str = SOURCE_TUSHARE
    credential_env: str = "TUSHARE_TOKEN"
    open_trade_dates: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BenchmarkCalendarPlanSpec:
    start_date: str
    end_date: str
    lake_root: str
    index_code: str = "399300.SZ"
    exchange: str = "SSE"
    run_id: str = "run-benchmark-calendar"
    dry_run: bool = True
    source: str = SOURCE_TUSHARE
    credential_env: str = "TUSHARE_TOKEN"


def _parse_contract_date(value: str) -> str:
    text = str(value).strip()
    try:
        if len(text) == 8 and text.isdigit():
            return datetime.strptime(text, "%Y%m%d").date().isoformat()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return date.fromisoformat(text[:10]).isoformat()
    except ValueError as exc:
        raise StructuredCliError("invalid_date_range", f"日期不合法: {text}") from exc
    raise StructuredCliError("invalid_date_range", f"日期格式不合法: {text}")


def _contract_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    start = _parse_contract_date(start_date)
    end = _parse_contract_date(end_date)
    if start > end:
        raise StructuredCliError("invalid_date_range", "start_date 不能晚于 end_date")
    return start, end


def _require_tushare_first_lake_root(lake_root: str | None) -> str:
    if not lake_root:
        raise LakeRootMissingError(
            "Tushare-first acquisition 需要显式 --lake-root；不得默认使用旧 repo data/**"
        )
    path = Path(lake_root)
    if not path.is_absolute() and path.parts and path.parts[0] == "data":
        raise StructuredCliError(
            "old_data_reference_only",
            "旧 repo data/** 仅 reference-only，不能作为 Tushare-first lake root",
        )
    return lake_root


def _require_configured_external_lake_root(lake_root: str | None, command_name: str) -> str:
    resolved = _resolve_lake_root(lake_root, required=True)
    path = Path(resolved)
    if not path.is_absolute() and path.parts and path.parts[0] == "data":
        raise StructuredCliError(
            "old_data_reference_only",
            f"{command_name} 不能默认使用旧 repo data/**；请传 --lake-root 或配置 MARKET_DATA_LAKE_ROOT",
        )
    return resolved


def _safe_lake_root_label(lake_root: str) -> str:
    del lake_root
    return "<configured-lake-root>"


def _resume_policy_payload() -> dict[str, str]:
    from .runtime import resume_policy_to_dict

    return resume_policy_to_dict()


def _old_data_operations_zero() -> dict[str, int]:
    return {
        "read": 0,
        "list": 0,
        "migrate": 0,
        "copy": 0,
        "compare": 0,
        "delete": 0,
    }


def _interface_for_tushare_first(dataset: str, source_interface: str | None) -> str:
    if dataset not in DATASETS or dataset not in TUSHARE_FIRST_DATASET_INTERFACES:
        raise StructuredCliError("unknown_dataset", f"不支持的 Tushare-first dataset: {dataset}")
    expected = TUSHARE_FIRST_DATASET_INTERFACES[dataset]
    if source_interface is not None and source_interface != expected:
        raise StructuredCliError(
            "interface_not_allowed",
            f"dataset={dataset} 只允许 exact interface={expected}",
        )
    return expected


def _tushare_first_params(spec: TushareFirstRunSpec, start: str, end: str) -> dict[str, Any]:
    params: dict[str, Any] = {
        "target_dataset": spec.dataset,
        "start_date": start,
        "end_date": end,
    }
    if spec.dataset == DATASET_HS300_INDEX:
        params["index_code"] = spec.index_code.strip().upper()
        params["benchmark_kind"] = "price_index"
    elif spec.dataset == DATASET_PRICES:
        if spec.symbol:
            params["symbol"] = spec.symbol.strip().upper()
        params["adjustment_policy"] = "qfq"
    elif spec.dataset == DATASET_ADJ_FACTOR:
        if spec.symbol:
            params["symbol"] = spec.symbol.strip().upper()
        params["adjustment_policy"] = "qfq"
    elif spec.dataset == DATASET_TRADE_CALENDAR:
        params["exchange"] = spec.exchange.strip().upper()
    elif spec.dataset in {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS}:
        params["index_code"] = spec.index_code.strip().upper()
    elif spec.dataset == DATASET_STOCK_BASIC:
        params["snapshot_date"] = end
        params["exchange"] = spec.exchange.strip().upper() if spec.exchange else ""
        params["list_status"] = spec.list_status.strip().upper()
        if spec.fields:
            params["fields"] = spec.fields
    elif spec.dataset in {DATASET_TRADE_STATUS, DATASET_PRICES_LIMIT, DATASET_EVENTS}:
        symbols = _dedupe_symbols([*spec.symbols, *([spec.symbol] if spec.symbol else [])])
        if not symbols:
            raise StructuredCliError(
                "schema_mismatch",
                f"dataset={spec.dataset} 需要显式 --symbols 或 --symbol，不能隐式读取旧 data/**",
            )
        params["symbols"] = list(symbols)
    return params


def _dedupe_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(symbol.strip().upper() for symbol in symbols if symbol.strip())
    if len(set(normalized)) != len(normalized):
        raise StructuredCliError("duplicate_symbol", "symbols 不能包含重复项")
    return normalized


def _batched(values: Sequence[str], batch_size: int) -> list[tuple[str, ...]]:
    return [tuple(values[index : index + batch_size]) for index in range(0, len(values), batch_size)]


def _date_slices(start: str, end: str, slice_days: int) -> list[dict[str, Any]]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    slices: list[dict[str, Any]] = []
    cursor = start_date
    while cursor <= end_date:
        slice_end = min(cursor + timedelta(days=slice_days - 1), end_date)
        slices.append(
            {
                "slice_id": f"d{len(slices) + 1:03d}",
                "start_date": cursor.isoformat(),
                "end_date": slice_end.isoformat(),
                "calendar_days": (slice_end - cursor).days + 1,
            }
        )
        cursor = slice_end + timedelta(days=1)
    return slices


def _batch_suffix(interface: str) -> str:
    return "adj-factor" if interface == INTERFACE_PRICES_ADJ_FACTOR else "daily"


def _prices_batch_id(date_slice: Mapping[str, Any], symbol_index: int, interface: str) -> str:
    start_token = str(date_slice["start_date"]).replace("-", "")
    end_token = str(date_slice["end_date"]).replace("-", "")
    return f"prices-{start_token}-{end_token}-s{symbol_index:03d}-{_batch_suffix(interface)}"


def _prices_request_params(
    *,
    spec: PricesLongHorizonPlanSpec,
    start: str,
    end: str,
    symbols: Sequence[str],
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "target_dataset": DATASET_PRICES,
        "start_date": start,
        "end_date": end,
        "adjustment_policy": spec.adjustment_policy,
        "offline": True,
    }
    if symbols:
        params["symbols"] = list(symbols)
    else:
        params["universe_source"] = spec.universe_source
        params["requires_universe_resolution"] = True
    return params


def build_prices_long_horizon_plan(spec: PricesLongHorizonPlanSpec) -> dict[str, Any]:
    lake_root = _require_tushare_first_lake_root(spec.lake_root)
    start, end = _contract_date_range(spec.start_date, spec.end_date)
    if spec.symbol_batch_size < 1 or spec.slice_days < 1:
        raise StructuredCliError("batch_size_invalid", "symbol_batch_size 和 slice_days 必须大于 0")
    symbols = _dedupe_symbols(spec.symbols)
    universe_source = (spec.universe_source or "").strip() or None
    if not symbols and not universe_source:
        raise StructuredCliError(
            "universe_missing",
            "长周期 prices planner 必须显式提供 --symbols 或 --universe-source",
        )
    daily_policy = spec.adjustment_policy
    adj_factor_policy = spec.adjustment_policy
    if daily_policy != adj_factor_policy:
        raise StructuredCliError("adjustment_policy_conflict", "prices.daily 与 prices.adj_factor 复权口径冲突")

    layout = LakeLayout(lake_root)
    date_slices = _date_slices(start, end, spec.slice_days)
    symbol_batches = _batched(symbols, spec.symbol_batch_size) if symbols else [()]
    requests: list[dict[str, Any]] = []
    interfaces = (INTERFACE_PRICES_DAILY, INTERFACE_PRICES_ADJ_FACTOR)
    for symbol_index, symbol_batch in enumerate(symbol_batches, start=1):
        for date_slice in date_slices:
            for interface in interfaces:
                batch_id = _prices_batch_id(date_slice, symbol_index, interface)
                target_dataset = DATASET_ADJ_FACTOR if interface == INTERFACE_PRICES_ADJ_FACTOR else DATASET_PRICES
                raw_path = layout.raw_run_batch_path(
                    spec.source,
                    interface,
                    str(date_slice["start_date"]),
                    spec.run_id,
                    batch_id,
                )
                requests.append(
                    {
                        "batch_id": batch_id,
                        "source": spec.source,
                        "interface": interface,
                        "target_dataset": target_dataset,
                        "date_slice": dict(date_slice),
                        "symbols": list(symbol_batch),
                        "universe_source": universe_source if not symbol_batch else None,
                        "symbols_resolved": bool(symbol_batch),
                        "params": _prices_request_params(
                            spec=spec,
                            start=str(date_slice["start_date"]),
                            end=str(date_slice["end_date"]),
                            symbols=symbol_batch,
                        ),
                        "target_paths": {
                            "raw_path": str(raw_path.relative_to(layout.lake_root)),
                        },
                    }
                )

    from .validation import build_prices_coverage_gate

    coverage_gate = build_prices_coverage_gate(
        start_date=start,
        end_date=end,
        symbols_count=len(symbols),
        date_slices=date_slices,
        open_trade_dates=spec.open_trade_dates or None,
    )
    return {
        "ok": True,
        "command": "prices-long-horizon-plan",
        "planner_mode": "dry_run",
        "dataset": DATASET_PRICES,
        "source": spec.source,
        "interfaces": [
            {
                "interface": INTERFACE_PRICES_DAILY,
                "target_dataset": DATASET_PRICES,
                "adjustment_policy": spec.adjustment_policy,
            },
            {
                "interface": INTERFACE_PRICES_ADJ_FACTOR,
                "target_dataset": DATASET_ADJ_FACTOR,
                "adjustment_policy": spec.adjustment_policy,
            },
        ],
        "credential_env": spec.credential_env,
        "start_date": start,
        "end_date": end,
        "symbols_or_universe": {
            "symbols": list(symbols),
            "symbols_count": len(symbols),
            "universe_source": universe_source,
            "symbols_resolved": bool(symbols),
            "symbol_batch_size": spec.symbol_batch_size,
            "symbol_batch_count": len(symbol_batches),
        },
        "batch_count": len(requests),
        "date_slices": date_slices,
        "run_id": spec.run_id,
        "resume_policy": _resume_policy_payload(),
        "target_paths": {
            "lake_root": _safe_lake_root_label(lake_root),
            "manifest_path": str(layout.manifest_path().relative_to(layout.lake_root)),
            "canonical_path": str(
                (
                    layout.canonical_dataset_root(DATASET_PRICES)
                    / f"run_id={spec.run_id}"
                ).relative_to(layout.lake_root)
            ),
            "quality_path": str((layout.quality_root / DATASET_PRICES / spec.run_id).relative_to(layout.lake_root)),
            "catalog_path": str((layout.catalog_root / "catalog.json").relative_to(layout.lake_root)),
            "gold_path": str(
                (
                    layout.gold_root
                    / DATASET_PRICES
                    / "1.0"
                    / f"run_id={spec.run_id}"
                ).relative_to(layout.lake_root)
            ),
        },
        "coverage_gate": coverage_gate,
        "planned_connector_requests": requests,
        "dry_run": bool(spec.dry_run),
        "network_calls": 0,
        "writes": 0,
        "real_execution_requires_user_authorization": True,
        "error_enum": list(PRICES_LONG_HORIZON_ERROR_ENUM),
        "old_data_operations": _old_data_operations_zero(),
        "old_quality_report_operations": {"read": 0, "open": 0, "overwrite": 0},
    }


def build_tushare_first_plan(spec: TushareFirstRunSpec) -> dict[str, Any]:
    lake_root = _require_tushare_first_lake_root(spec.lake_root)
    start, end = _contract_date_range(spec.start_date, spec.end_date)
    source_interface = _interface_for_tushare_first(spec.dataset, spec.source_interface)
    layout = LakeLayout(lake_root)
    params = _tushare_first_params(spec, start, end)
    raw_path = layout.raw_run_batch_path(
        spec.source,
        source_interface,
        start,
        spec.run_id,
        spec.batch_id,
    )
    canonical_path = (
        layout.canonical_dataset_root(spec.dataset)
        / f"run_id={spec.run_id}"
        / f"part-{spec.batch_id}.parquet"
    )
    quality_path = layout.quality_root / spec.dataset / spec.run_id / "quality.csv"
    catalog_path = layout.catalog_root / "catalog.json"
    gold_path = (
        layout.gold_root
        / spec.dataset
        / "1.0"
        / f"run_id={spec.run_id}"
        / f"part-{spec.batch_id}.parquet"
    )
    return {
        "ok": True,
        "command": "tushare-first-acquire",
        "dataset": spec.dataset,
        "source": spec.source,
        "interface": source_interface,
        "source_interface": source_interface,
        "credential_env": spec.credential_env,
        "start_date": start,
        "end_date": end,
        "lake_root": _safe_lake_root_label(lake_root),
        "lake_root_is_configured": True,
        "run_id": spec.run_id,
        "batch_id": spec.batch_id,
        "resume_policy": _resume_policy_payload(),
        "dry_run": bool(spec.dry_run),
        "params": params,
        "raw_path": str(raw_path.relative_to(layout.lake_root)),
        "manifest_path": str(layout.manifest_path().relative_to(layout.lake_root)),
        "canonical_path": str(canonical_path.relative_to(layout.lake_root)),
        "quality_path": str(quality_path.relative_to(layout.lake_root)),
        "catalog_path": str(catalog_path.relative_to(layout.lake_root)),
        "gold_path": str(gold_path.relative_to(layout.lake_root)),
        "error_enum": list(TUSHARE_FIRST_ERROR_ENUM),
        "network_calls": 0 if spec.dry_run else None,
        "writes": 0 if spec.dry_run else None,
        "raw_manifest_role": "audit_resume_replay_quality_trace_only",
        "runtime_consumers_for_raw_manifest": [],
        "old_data_operations": {
            "read": 0,
            "list": 0,
            "migrate": 0,
            "copy": 0,
            "compare": 0,
            "delete": 0,
        },
    }


def build_jqdata_plan(spec: JQDataRunSpec) -> dict[str, Any]:
    lake_root = _require_configured_external_lake_root(
        spec.lake_root,
        "JQData acquisition",
    )
    expected_interface = JQDATA_DATASET_INTERFACES.get(spec.dataset)
    if expected_interface is None:
        raise StructuredCliError(
            "unknown_dataset",
            f"JQData 不支持 dataset={spec.dataset}",
        )
    source_interface = spec.source_interface or expected_interface
    if source_interface != expected_interface:
        raise StructuredCliError(
            "interface_not_allowed",
            f"dataset={spec.dataset} 只允许 exact interface={expected_interface}",
        )
    start, end = _contract_date_range(spec.start_date, spec.end_date)
    layout = LakeLayout(lake_root)
    params = {
        "target_dataset": spec.dataset,
        "start_date": start,
        "end_date": end,
    }
    if spec.dataset in {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS}:
        params["index_code"] = spec.index_code.strip().upper()
    if spec.dataset == DATASET_STOCK_BASIC:
        params["snapshot_date"] = end
    if spec.dataset in {DATASET_TRADE_STATUS, DATASET_PRICES_LIMIT, DATASET_EVENTS}:
        if not spec.symbols:
            raise StructuredCliError(
                "schema_mismatch",
                f"dataset={spec.dataset} 需要显式 --symbols，不能隐式读取旧 data/** 或替代 universe",
            )
        params["symbols"] = list(spec.symbols)
    raw_path = layout.raw_run_batch_path(
        spec.source,
        source_interface,
        start,
        spec.run_id,
        spec.batch_id,
    )
    canonical_path = (
        layout.canonical_dataset_root(spec.dataset)
        / f"run_id={spec.run_id}"
        / f"part-{spec.batch_id}.parquet"
    )
    quality_path = layout.quality_root / spec.dataset / spec.run_id / "quality.csv"
    catalog_path = layout.catalog_root / "catalog.json"
    gold_path = (
        layout.gold_root
        / spec.dataset
        / "1.0"
        / f"run_id={spec.run_id}"
        / f"part-{spec.batch_id}.parquet"
    )
    target_paths = {
        "lake_root": _safe_lake_root_label(lake_root),
        "raw_path": str(raw_path.relative_to(layout.lake_root)),
        "manifest_path": str(layout.manifest_path().relative_to(layout.lake_root)),
        "canonical_path": str(canonical_path.relative_to(layout.lake_root)),
        "quality_path": str(quality_path.relative_to(layout.lake_root)),
        "catalog_path": str(catalog_path.relative_to(layout.lake_root)),
        "gold_path": str(gold_path.relative_to(layout.lake_root)),
    }
    return {
        "ok": True,
        "command": "jqdata-acquire",
        "dataset": spec.dataset,
        "source": spec.source,
        "interface": source_interface,
        "source_interface": source_interface,
        "provider_interface": _jqdata_provider_interface(source_interface),
        "credential_env_username": spec.credential_env_username,
        "credential_env_password": spec.credential_env_password,
        "start_date": start,
        "end_date": end,
        "index_code": params.get("index_code"),
        "symbols_count": len(spec.symbols),
        "lake_root": _safe_lake_root_label(lake_root),
        "lake_root_is_configured": True,
        "run_id": spec.run_id,
        "batch_id": spec.batch_id,
        "resume_policy": _resume_policy_payload(),
        "dry_run": bool(spec.dry_run),
        "params": params,
        "target_paths": target_paths,
        "raw_path": target_paths["raw_path"],
        "manifest_path": target_paths["manifest_path"],
        "canonical_path": target_paths["canonical_path"],
        "quality_path": target_paths["quality_path"],
        "catalog_path": target_paths["catalog_path"],
        "gold_path": target_paths["gold_path"],
        "error_enum": list(JQDATA_ACQUIRE_ERROR_ENUM),
        "network_calls": 0 if spec.dry_run else None,
        "writes": 0 if spec.dry_run else None,
        "raw_manifest_role": "audit_resume_replay_quality_trace_only",
        "runtime_consumers_for_raw_manifest": [],
        "real_execution_requires_user_authorization": True,
        "old_data_operations": _old_data_operations_zero(),
    }


def emit_tushare_first_runbook_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    status = "planned" if result.get("dry_run") else "executed"
    if not result.get("ok", False):
        status = "failed"
    return {
        "ok": bool(result.get("ok", False)),
        "status": status,
        "dataset": result.get("dataset"),
        "source": result.get("source", SOURCE_TUSHARE),
        "source_interface": result.get("source_interface") or result.get("interface"),
        "run_id": result.get("run_id"),
        "quality_status": result.get("quality_status"),
        "dataset_status": result.get("dataset_status"),
        "safe_lake_root": "<configured-lake-root>",
        "raw_manifest_role": "audit_resume_replay_quality_trace_only",
        "runtime_consumers_for_raw_manifest": [],
        "old_data_reference_only": True,
        "old_data_operations": {
            "read": 0,
            "list": 0,
            "migrate": 0,
            "copy": 0,
            "compare": 0,
            "delete": 0,
        },
        "next_step": (
            "review quality/catalog before runtime consumption"
            if result.get("quality_status") in {"pass", "warn", None}
            else "fix data quality before runtime consumption"
        ),
    }


def emit_jqdata_runbook_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    status = "planned" if result.get("dry_run") else "executed"
    if not result.get("ok", False):
        status = "failed"
    return {
        "ok": bool(result.get("ok", False)),
        "status": status,
        "dataset": result.get("dataset"),
        "source": SOURCE_JQDATA,
        "source_interface": result.get("source_interface") or result.get("interface"),
        "provider_interface": result.get("provider_interface"),
        "run_id": result.get("run_id"),
        "safe_lake_root": "<configured-lake-root>",
        "limited_pit_window": "2025-02-11..2026-02-18",
        "raw_manifest_role": "audit_resume_replay_quality_trace_only",
        "old_data_reference_only": True,
        "old_data_operations": _old_data_operations_zero(),
        "next_step": "normalize_validate_publish_read_revalidate_replay_if_quality_passes",
    }


def _tushare_first_spec_from_args(args: argparse.Namespace) -> TushareFirstRunSpec:
    return TushareFirstRunSpec(
        dataset=args.dataset,
        source_interface=args.interface,
        start_date=args.start_date,
        end_date=args.end_date,
        lake_root=args.lake_root,
        credential_env=args.credential_env,
        run_id=_run_id(args),
        batch_id=_batch_id(args),
        dry_run=_parse_bool(args.dry_run),
        index_code=args.index_code,
        symbol=args.symbol,
        exchange=args.exchange,
        list_status=args.list_status,
        fields=args.fields,
        symbols=tuple(_split_csv(getattr(args, "symbols", None))),
    )


def cmd_tushare_first_acquire(args: argparse.Namespace) -> dict[str, Any]:
    spec = _tushare_first_spec_from_args(args)
    plan = build_tushare_first_plan(spec)
    if plan["dry_run"]:
        return {**plan, "runbook_summary": emit_tushare_first_runbook_summary(plan)}
    if not args.enable_real_source:
        raise RealSourceDisabledError(
            "Tushare-first 真实执行必须显式传 --enable-real-source"
        )
    if not os.environ.get(spec.credential_env):
        raise StructuredCliError(
            "missing_credential",
            f"missing credential env var: {spec.credential_env}",
        )

    from .connectors.protocol import AdapterConfig, ConnectorRequest
    from .connectors.tushare import TushareAdapter
    from .runtime import RuntimeContext, RuntimePolicy, execute_batches

    params = dict(plan["params"])
    params["explicit_real_execution"] = True
    params["offline"] = False
    request = ConnectorRequest(
        source=SOURCE_TUSHARE,
        interface=str(plan["interface"]),
        params=params,
        run_id=str(plan["run_id"]),
        batch_id=str(plan["batch_id"]),
    )
    results = execute_batches(
        [request],
        TushareAdapter(
            AdapterConfig(
                source=SOURCE_TUSHARE,
                enabled=True,
                allow_interfaces=(str(plan["interface"]),),
                credential_env_vars=(spec.credential_env,),
            )
        ),
        LakeLayout(spec.lake_root),
        RuntimePolicy(max_retries=0, throttle_seconds=0.0),
        context=RuntimeContext(str(plan["run_id"])),
    )
    payload = {
        **plan,
        "dry_run": False,
        "network_calls": len(results),
        "results": [
            {
                "batch_id": item.batch_id,
                "status": item.status,
                "error_type": item.error_type,
                "raw_path": item.raw_path,
            }
            for item in results
        ],
    }
    return {**payload, "runbook_summary": emit_tushare_first_runbook_summary(payload)}


def _jqdata_spec_from_args(args: argparse.Namespace) -> JQDataRunSpec:
    return JQDataRunSpec(
        dataset=args.dataset,
        source_interface=getattr(args, "interface", None),
        start_date=args.start_date,
        end_date=args.end_date,
        lake_root=_resolve_lake_root(args.lake_root, required=True),
        credential_env_username=args.credential_env_username,
        credential_env_password=args.credential_env_password,
        run_id=_run_id(args),
        batch_id=_batch_id(args),
        dry_run=_parse_bool(args.dry_run),
        index_code=args.index_code,
        symbols=tuple(_split_csv(getattr(args, "symbols", None))),
    )


def cmd_jqdata_acquire(args: argparse.Namespace) -> dict[str, Any]:
    spec = _jqdata_spec_from_args(args)
    plan = build_jqdata_plan(spec)
    if plan["dry_run"]:
        return {**plan, "runbook_summary": emit_jqdata_runbook_summary(plan)}
    if not args.enable_real_source:
        raise RealSourceDisabledError(
            "JQData 真实执行必须显式传 --enable-real-source"
        )
    missing = [
        name
        for name in (spec.credential_env_username, spec.credential_env_password)
        if not os.environ.get(name)
    ]
    if missing:
        raise StructuredCliError(
            "missing_credential",
            f"missing credential env var: {','.join(missing)}",
        )

    from .connectors.jqdata import JQDataAdapter
    from .connectors.protocol import AdapterConfig, ConnectorRequest
    from .runtime import RuntimeContext, RuntimePolicy, execute_batches

    params = dict(plan["params"])
    params["explicit_real_execution"] = True
    params["offline"] = False
    request = ConnectorRequest(
        source=SOURCE_JQDATA,
        interface=str(plan["interface"]),
        params=params,
        run_id=str(plan["run_id"]),
        batch_id=str(plan["batch_id"]),
    )
    results = execute_batches(
        [request],
        JQDataAdapter(
            AdapterConfig(
                source=SOURCE_JQDATA,
                enabled=True,
                allow_interfaces=(str(plan["interface"]),),
                credential_env_vars=(
                    spec.credential_env_username,
                    spec.credential_env_password,
                ),
            ),
            provider_factory=getattr(args, "provider_factory", None),
            clock=getattr(args, "clock", None),
        ),
        LakeLayout(spec.lake_root),
        RuntimePolicy(max_retries=0, throttle_seconds=0.0),
        context=RuntimeContext(str(plan["run_id"])),
    )
    if plan["interface"] in {INTERFACE_INDEX_MEMBERS_SNAPSHOT, INTERFACE_INDEX_WEIGHTS_SNAPSHOT}:
        provider_calls_per_attempt = len(_date_values(str(plan["start_date"]), str(plan["end_date"])))
    elif plan["interface"] == INTERFACE_TRADE_STATUS_DAILY:
        provider_calls_per_attempt = 2
    else:
        provider_calls_per_attempt = 1
    payload = {
        **plan,
        "dry_run": False,
        "network_calls": sum(
            0 if item.status == "skipped" else provider_calls_per_attempt * max(1, item.attempts)
            for item in results
        ),
        "writes": sum(1 for item in results if item.status != "skipped"),
        "results": [
            {
                "batch_id": item.batch_id,
                "status": item.status,
                "attempts": item.attempts,
                "error_type": item.error_type,
                "raw_path": item.raw_path,
            }
            for item in results
        ],
    }
    return {**payload, "runbook_summary": emit_jqdata_runbook_summary(payload)}


def _prices_long_horizon_spec_from_args(args: argparse.Namespace) -> PricesLongHorizonPlanSpec:
    return PricesLongHorizonPlanSpec(
        start_date=args.start_date,
        end_date=args.end_date,
        lake_root=args.lake_root,
        symbols=tuple(_split_csv(args.symbols)),
        universe_source=args.universe_source,
        symbol_batch_size=args.symbol_batch_size,
        slice_days=args.slice_days,
        run_id=_run_id(args),
        adjustment_policy=args.adjustment_policy,
        dry_run=_parse_bool(args.dry_run),
        credential_env=args.credential_env,
        open_trade_dates=tuple(_split_csv(args.open_trade_dates)),
    )


def cmd_prices_long_horizon_plan(args: argparse.Namespace) -> dict[str, Any]:
    spec = _prices_long_horizon_spec_from_args(args)
    plan = build_prices_long_horizon_plan(spec)
    if not spec.dry_run:
        raise RealSourceDisabledError(
            "prices long-horizon planner 当前只授权 dry-run；真实执行必须另行授权"
        )
    return plan


def build_benchmark_calendar_backfill_plan(spec: BenchmarkCalendarPlanSpec) -> dict[str, Any]:
    lake_root = _require_tushare_first_lake_root(spec.lake_root)
    start, end = _contract_date_range(spec.start_date, spec.end_date)
    index_code = spec.index_code.strip().upper()
    exchange = spec.exchange.strip().upper()
    calendar_plan = build_tushare_first_plan(
        TushareFirstRunSpec(
            dataset=DATASET_TRADE_CALENDAR,
            source_interface=INTERFACE_TRADE_CALENDAR_DAILY,
            start_date=start,
            end_date=end,
            lake_root=lake_root,
            source=spec.source,
            credential_env=spec.credential_env,
            run_id=f"{spec.run_id}-calendar",
            batch_id="trade-calendar-b1",
            dry_run=spec.dry_run,
            exchange=exchange,
        )
    )
    hs300_plan = build_tushare_first_plan(
        TushareFirstRunSpec(
            dataset=DATASET_HS300_INDEX,
            source_interface=INTERFACE_HS300_INDEX_DAILY,
            start_date=start,
            end_date=end,
            lake_root=lake_root,
            source=spec.source,
            credential_env=spec.credential_env,
            run_id=f"{spec.run_id}-hs300",
            batch_id="hs300-index-b1",
            dry_run=spec.dry_run,
            index_code=index_code,
        )
    )
    return {
        "ok": True,
        "command": "benchmark-calendar-backfill",
        "planner_mode": "dry_run",
        "datasets": [DATASET_TRADE_CALENDAR, DATASET_HS300_INDEX],
        "source": spec.source,
        "interfaces": [
            {
                "dataset": DATASET_TRADE_CALENDAR,
                "interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "exchange": exchange,
            },
            {
                "dataset": DATASET_HS300_INDEX,
                "interface": INTERFACE_HS300_INDEX_DAILY,
                "index_code": index_code,
            },
        ],
        "credential_env": spec.credential_env,
        "start_date": start,
        "end_date": end,
        "index_code": index_code,
        "exchange": exchange,
        "run_id": spec.run_id,
        "resume_policy": _resume_policy_payload(),
        "target_paths": {
            "lake_root": _safe_lake_root_label(lake_root),
            "manifest_path": calendar_plan["manifest_path"],
            "catalog_path": calendar_plan["catalog_path"],
        },
        "dataset_plans": [
            {
                "dataset": DATASET_TRADE_CALENDAR,
                "interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "run_id": calendar_plan["run_id"],
                "batch_id": calendar_plan["batch_id"],
                "params": calendar_plan["params"],
                "raw_path": calendar_plan["raw_path"],
                "canonical_path": calendar_plan["canonical_path"],
                "quality_path": calendar_plan["quality_path"],
                "catalog_path": calendar_plan["catalog_path"],
                "gold_path": calendar_plan["gold_path"],
                "network_calls": calendar_plan["network_calls"],
                "writes": calendar_plan["writes"],
            },
            {
                "dataset": DATASET_HS300_INDEX,
                "interface": INTERFACE_HS300_INDEX_DAILY,
                "run_id": hs300_plan["run_id"],
                "batch_id": hs300_plan["batch_id"],
                "params": hs300_plan["params"],
                "raw_path": hs300_plan["raw_path"],
                "canonical_path": hs300_plan["canonical_path"],
                "quality_path": hs300_plan["quality_path"],
                "catalog_path": hs300_plan["catalog_path"],
                "gold_path": hs300_plan["gold_path"],
                "network_calls": hs300_plan["network_calls"],
                "writes": hs300_plan["writes"],
            },
        ],
        "coverage_gate": {
            "benchmark_dataset": DATASET_HS300_INDEX,
            "calendar_dataset": DATASET_TRADE_CALENDAR,
            "denominator_mode": "trade_calendar_open_dates",
            "denominator_filter": "trade_calendar.is_open == true",
            "required_ratio": 1.0,
            "natural_day_denominator_allowed": False,
            "coverage_pass_claimed": False,
        },
        "dry_run": bool(spec.dry_run),
        "network_calls": 0,
        "writes": 0,
        "real_execution_requires_user_authorization": True,
        "error_enum": list(BENCHMARK_CALENDAR_BACKFILL_ERROR_ENUM),
        "old_data_operations": _old_data_operations_zero(),
        "old_quality_report_operations": {"read": 0, "open": 0, "overwrite": 0},
    }


def _benchmark_calendar_spec_from_args(args: argparse.Namespace) -> BenchmarkCalendarPlanSpec:
    return BenchmarkCalendarPlanSpec(
        start_date=args.start_date,
        end_date=args.end_date,
        lake_root=args.lake_root,
        index_code=args.index_code,
        exchange=args.exchange,
        run_id=_run_id(args),
        dry_run=_parse_bool(args.dry_run),
        credential_env=args.credential_env,
    )


def cmd_benchmark_calendar_backfill(args: argparse.Namespace) -> dict[str, Any]:
    spec = _benchmark_calendar_spec_from_args(args)
    plan = build_benchmark_calendar_backfill_plan(spec)
    if not spec.dry_run:
        raise RealSourceDisabledError(
            "benchmark-calendar backfill 当前只授权 dry-run；真实执行必须另行授权"
        )
    return plan


def _hs300_plan_payload(args: argparse.Namespace, lake_root: str) -> dict[str, Any]:
    start, end = _date_range(args)
    index_code = str(args.index_code or "399300.SZ").strip().upper()
    run_id = _run_id(args)
    batch_id = _batch_id(args)
    layout = LakeLayout(lake_root)
    raw_path = layout.raw_run_batch_path(
        SOURCE_TUSHARE,
        INTERFACE_HS300_INDEX_DAILY,
        start,
        run_id,
        batch_id,
    )
    canonical_path = (
        layout.canonical_dataset_root(DATASET_HS300_INDEX)
        / f"run_id={run_id}"
        / f"part-{batch_id}.parquet"
    )
    quality_path = layout.quality_root / DATASET_HS300_INDEX / run_id / "quality.csv"
    catalog_path = layout.catalog_root / "market_data_catalog.json"
    gold_path = (
        layout.gold_root
        / DATASET_HS300_INDEX
        / "1.0"
        / f"run_id={run_id}"
        / f"part-{batch_id}.parquet"
    )
    return {
        "ok": True,
        "command": "hs300-backfill",
        "dataset": DATASET_HS300_INDEX,
        "target_dataset": DATASET_HS300_INDEX,
        "source": SOURCE_TUSHARE,
        "interface": INTERFACE_HS300_INDEX_DAILY,
        "provider_interface": "index_daily",
        "index_code": index_code,
        "start_date": start,
        "end_date": end,
        "lake_root": lake_root,
        "run_id": run_id,
        "batch_id": batch_id,
        "resume_policy": {
            "success": "skip",
            "failed": "retry",
            "partial_success": "retry",
            "duplicate_manifest": "fail",
        },
        "dry_run": _parse_bool(args.dry_run),
        "raw_path": str(raw_path.relative_to(layout.lake_root)),
        "manifest_path": str(layout.manifest_path().relative_to(layout.lake_root)),
        "canonical_path": str(canonical_path.relative_to(layout.lake_root)),
        "quality_path": str(quality_path.relative_to(layout.lake_root)),
        "catalog_path": str(catalog_path.relative_to(layout.lake_root)),
        "gold_path": str(gold_path.relative_to(layout.lake_root)),
        "error_enum": list(HS300_BACKFILL_ERROR_ENUM),
        "network_calls": 0 if _parse_bool(args.dry_run) else None,
        "writes": 0 if _parse_bool(args.dry_run) else None,
    }


def cmd_hs300_backfill(args: argparse.Namespace) -> dict[str, Any]:
    lake_root = _resolve_lake_root(args.lake_root, required=True)
    plan = _hs300_plan_payload(args, lake_root)
    if plan["dry_run"]:
        return plan
    if not args.enable_real_source:
        raise RealSourceDisabledError(
            "hs300_index backfill 真实执行必须显式传 --enable-real-source"
        )
    if not os.environ.get("TUSHARE_TOKEN"):
        raise StructuredCliError("missing_credential", "missing credential env var: TUSHARE_TOKEN")

    from .connectors.protocol import AdapterConfig, ConnectorRequest
    from .connectors.tushare import TushareAdapter
    from .runtime import RuntimeContext, RuntimePolicy, execute_batches

    request = ConnectorRequest(
        source=SOURCE_TUSHARE,
        interface=INTERFACE_HS300_INDEX_DAILY,
        params={
            "target_dataset": DATASET_HS300_INDEX,
            "index_code": plan["index_code"],
            "start_date": plan["start_date"],
            "end_date": plan["end_date"],
            "explicit_real_execution": True,
            "offline": False,
        },
        run_id=str(plan["run_id"]),
        batch_id=str(plan["batch_id"]),
    )
    results = execute_batches(
        [request],
        TushareAdapter(
            AdapterConfig(
                source=SOURCE_TUSHARE,
                enabled=True,
                allow_interfaces=(INTERFACE_HS300_INDEX_DAILY,),
                credential_env_vars=("TUSHARE_TOKEN",),
            )
        ),
        LakeLayout(lake_root),
        RuntimePolicy(max_retries=0, throttle_seconds=0.0),
        context=RuntimeContext(str(plan["run_id"])),
    )
    return {
        **plan,
        "dry_run": False,
        "network_calls": sum(item.attempts for item in results),
        "writes": sum(1 for item in results if item.status != "skipped"),
        "results": [
            {
                "batch_id": item.batch_id,
                "status": item.status,
                "attempts": item.attempts,
                "error_type": item.error_type,
                "raw_path": item.raw_path,
            }
            for item in results
        ],
    }


def _fake_request(args: argparse.Namespace):
    from .connectors.protocol import ConnectorRequest

    symbols = _split_csv(args.symbols)
    _require_symbols(symbols)
    start, end = _date_range(args)
    params = {
        "symbols": symbols,
        "start_date": start,
        "end_date": end,
        "seed": args.seed,
        "target_dataset": args.dataset,
        "adjustment_policy": "none",
    }
    return ConnectorRequest(
        source=args.source,
        interface=args.interface,
        params=params,
        run_id=_run_id(args),
        batch_id=_batch_id(args),
    )


def _real_source_error(args: argparse.Namespace) -> None:
    if args.source == SOURCE_FAKE:
        return
    if not args.enable_real_source:
        raise RealSourceDisabledError(
            f"真实 source 未显式启用: {args.source}.{args.interface}"
        )
    raise RealSourceDisabledError(
        f"真实 source 成功联网不属于本 Story 默认路径: {args.source}.{args.interface}"
    )


def cmd_fetch(args: argparse.Namespace) -> dict[str, Any]:
    _require_prices(args.dataset)
    _real_source_error(args)
    if args.interface != INTERFACE_PRICES_DAILY:
        raise CliUsageError(f"本批次仅支持 interface={INTERFACE_PRICES_DAILY}: {args.interface}")
    from .connectors.fake import FakeConnector
    from .runtime import RuntimeContext, RuntimePolicy, execute_batches

    layout = LakeLayout(args.lake_root)
    request = _fake_request(args)
    results = execute_batches(
        [request],
        FakeConnector(seed=args.seed),
        layout,
        RuntimePolicy(max_retries=args.max_retries, throttle_seconds=0.0),
        context=RuntimeContext(_run_id(args)),
    )
    return {
        "ok": True,
        "command": "fetch",
        "run_id": _run_id(args),
        "manifest_path": layout.manifest_path(),
        "results": [
            {
                "batch_id": item.batch_id,
                "status": item.status,
                "attempts": item.attempts,
                "raw_path": item.raw_path,
                "error_type": item.error_type,
            }
            for item in results
        ],
    }


def cmd_normalize(args: argparse.Namespace) -> dict[str, Any]:
    from .normalization import normalize_run

    lake_root = _resolve_lake_root(args.lake_root)
    layout = LakeLayout(lake_root)
    result = normalize_run(
        layout.manifest_path(),
        lake_root,
        dataset=args.dataset,
        run_id=args.run_id,
    )
    return {
        "ok": True,
        "command": "normalize",
        "dataset": result.dataset,
        "run_id": result.run_id,
        "row_count": result.row_count,
        "canonical_paths": list(result.canonical_paths),
        "skipped_status_counts": result.skipped_status_counts,
    }


def _trade_calendar_from_open_dates(open_trade_dates: Sequence[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": [str(item) for item in open_trade_dates],
            "is_open": [True] * len(open_trade_dates),
        }
    )


def _trade_calendar_from_catalog(args: argparse.Namespace) -> pd.DataFrame | None:
    from .readers import read_dataset

    result = read_dataset(
        DATASET_TRADE_CALENDAR,
        _resolve_lake_root(args.lake_root),
        filters={"start": args.start_date, "end": args.end_date},
    )
    return result.frame if result.available and result.frame is not None else None


def _read_manifest_context(layout: LakeLayout, run_id: str | None) -> list[dict[str, Any]]:
    from .storage import read_manifest_records

    records = []
    for record in read_manifest_records(layout):
        if record.get("status") != "success":
            continue
        if run_id is not None and record.get("run_id") != run_id:
            continue
        records.append(record)
    return records


def _canonical_paths_for_run(
    layout: LakeLayout,
    dataset: str,
    run_id: str | None,
) -> list[Path]:
    root = layout.canonical_dataset_root(dataset)
    if run_id:
        root = root / f"run_id={run_id}"
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.parquet") if ".tmp" not in path.name)


def _catalog_canonical_path(
    layout: LakeLayout,
    dataset: str,
    canonical_paths: Sequence[Path],
    run_id: str | None,
) -> Path | None:
    paths = list(canonical_paths)
    if len(paths) == 1:
        return paths[0]
    if run_id:
        run_root = layout.canonical_dataset_root(dataset) / f"run_id={run_id}"
        if run_root.exists():
            return run_root
    return None


def _filter_hs300_canonical_for_request(
    canonical_paths: Sequence[Path],
    *,
    index_code: str,
    start: str,
    end: str,
    output_dir: Path,
) -> list[Path]:
    frames = [pd.read_parquet(path) for path in canonical_paths]
    if frames:
        frame = pd.concat(frames, ignore_index=True)
    else:
        frame = pd.DataFrame()
    if "index_code" in frame.columns:
        frame = frame[frame["index_code"].astype(str).str.upper() == str(index_code).upper()]
    if "trade_date" in frame.columns:
        dates = frame["trade_date"].astype(str)
        frame = frame[(dates >= start) & (dates <= end)]
    filtered_path = output_dir / "hs300_index-request-scope.parquet"
    frame.to_parquet(filtered_path, index=False)
    return [filtered_path]


def _validate_quality_csv(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        row = next(reader, None)
    if row is None:
        raise QualityReportShapeError(f"quality CSV 为空: {path}")
    missing = [field for field in QUALITY_REQUIRED_FIELDS if field not in row]
    if missing:
        raise QualityReportShapeError(f"quality CSV 缺少字段: {','.join(missing)}")
    for field, value in row.items():
        if field.endswith("_json"):
            json.loads(value)
    return row


def _first_canonical_value(path: Path | None, column: str) -> str | None:
    if path is None or not path.exists():
        return None
    try:
        frame = pd.read_parquet(path, columns=[column])
    except Exception:
        return None
    values = [str(item) for item in frame[column].dropna().unique() if str(item)]
    return values[0] if values else None


def _coverage_ratio(actual: int, expected: int) -> float:
    return (actual / expected) if expected else 0.0


def _catalog_entry_from_quality(
    *,
    dataset: str,
    layout: LakeLayout,
    quality: Any,
    canonical_path: Path | None,
    csv_path: Path,
    md_path: Path,
    start_date: str | None = None,
    end_date: str | None = None,
    published: bool = False,
) -> Any:
    from .catalog import CatalogEntry

    coverage_row = quality.to_csv_row()
    limitations = [
        {"code": code}
        for code in list(getattr(quality, "warnings", []) or [])
        + list(getattr(quality, "issue_codes", []) or [])
    ]
    expected_rows = int(getattr(quality.coverage, "expected_rows", 0) or 0)
    actual_rows = int(getattr(quality.coverage, "actual_rows", 0) or 0)
    available_at_rule = _first_canonical_value(canonical_path, "available_at_rule")
    if dataset == DATASET_EVENTS and not available_at_rule and quality.quality_status != "fail":
        if quality.source_name == SOURCE_TUSHARE and quality.source_interface == INTERFACE_EVENTS_DISCLOSURE:
            available_at_rule = "tushare_stock_st_09:20"
        else:
            available_at_rule = "daily_close_fact"
    return CatalogEntry(
        dataset=dataset,
        start_date=start_date or getattr(quality.coverage, "requested_start", None),
        end_date=end_date or getattr(quality.coverage, "requested_end", None),
        coverage=coverage_row,
        quality_status=quality.quality_status,
        dataset_status=quality.dataset_status,
        latest_manifest_run_id=quality.run_id,
        source=quality.source_name,
        source_interface=quality.source_interface,
        lineage_raw_checksum=quality.lineage_raw_checksum,
        canonical_path=str(canonical_path.relative_to(layout.lake_root)) if canonical_path else None,
        quality_csv_path=str(csv_path.relative_to(layout.lake_root)),
        quality_path=str(md_path.relative_to(layout.lake_root)),
        generated_at=quality.generated_at,
        updated_at=quality.generated_at,
        published=published,
        published_at=quality.generated_at if published else None,
        readiness_status=getattr(quality, "readiness_status", None),
        pit_status=getattr(quality, "pit_status", None),
        available_at_rule=available_at_rule,
        known_limitations=limitations,
        coverage_denominator=expected_rows,
        coverage_ratio=_coverage_ratio(actual_rows, expected_rows),
    )


def _cmd_validate_hs300_index(args: argparse.Namespace) -> dict[str, Any]:
    from .catalog import CatalogStore
    from .validation import QualityThresholds, validate_hs300_index, write_quality_reports

    lake_root = _resolve_lake_root(args.lake_root)
    layout = LakeLayout(lake_root)
    start, end = _date_range(args)
    open_trade_dates = _split_csv(args.open_trade_dates)
    trade_calendar = (
        _trade_calendar_from_open_dates(open_trade_dates)
        if open_trade_dates
        else _trade_calendar_from_catalog(args)
    )
    if trade_calendar is None:
        raise CliUsageError(
            "dataset=hs300_index validate 需要 --open-trade-dates，"
            "或先登记 trade_calendar 到 catalog"
        )
    thresholds = QualityThresholds(
        prices_missing_rate_pass=args.prices_missing_rate_pass,
        prices_missing_rate_warn=args.prices_missing_rate_warn,
        prices_missing_rate_fail=args.prices_missing_rate_fail,
    )
    canonical_paths = _canonical_paths_for_run(layout, args.dataset, args.run_id)
    with tempfile.TemporaryDirectory(prefix="hs300-validate-") as tmp_dir:
        scoped_paths = _filter_hs300_canonical_for_request(
            canonical_paths,
            index_code=args.index_code,
            start=start,
            end=end,
            output_dir=Path(tmp_dir),
        )
        quality = validate_hs300_index(
            lake_root,
            args.index_code,
            (start, end),
            trade_calendar,
            thresholds,
            canonical_paths=scoped_paths,
        )
    csv_path, md_path = write_quality_reports(quality, layout)
    csv_row = _validate_quality_csv(csv_path)
    canonical_path = _catalog_canonical_path(
        layout,
        args.dataset,
        canonical_paths,
        args.run_id,
    )
    CatalogStore(layout).upsert(
        _catalog_entry_from_quality(
            dataset=args.dataset,
            layout=layout,
            quality=quality,
            canonical_path=canonical_path,
            csv_path=csv_path,
            md_path=md_path,
            start_date=start,
            end_date=end,
            published=False,
        )
    )
    return {
        "ok": True,
        "command": "validate",
        "dataset": args.dataset,
        "quality_status": quality.quality_status,
        "fetch_status": quality.fetch_status,
        "dataset_status": quality.dataset_status,
        "quality_csv_path": csv_path,
        "quality_markdown_path": md_path,
        "coverage": asdict(quality.coverage),
        "thresholds": asdict(thresholds),
        "denominator_mode": quality.denominator_mode,
        "input_config_hash": quality.input_config_hash,
        "quality_csv_fields": sorted(csv_row),
        "catalog_status": "candidate_unpublished",
    }


def _date_values(start: str, end: str) -> list[str]:
    cursor = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    values: list[str] = []
    while cursor <= end_date:
        values.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return values


def _cmd_validate_trade_calendar(args: argparse.Namespace) -> dict[str, Any]:
    from .catalog import CatalogStore
    from .validation import QualityThresholds, validate_dataset, write_quality_reports

    lake_root = _resolve_lake_root(args.lake_root)
    layout = LakeLayout(lake_root)
    start, end = _date_range(args)
    exchange = str(args.exchange or "SSE").strip().upper()
    canonical_paths = _canonical_paths_for_run(layout, args.dataset, args.run_id)
    thresholds = QualityThresholds(
        prices_missing_rate_pass=args.prices_missing_rate_pass,
        prices_missing_rate_warn=args.prices_missing_rate_warn,
        prices_missing_rate_fail=args.prices_missing_rate_fail,
    )
    quality = validate_dataset(
        args.dataset,
        lake_root,
        (start, end),
        [exchange],
        thresholds,
        {
            "canonical_paths": canonical_paths,
            "expected_dates": _date_values(start, end),
            "exchange": exchange,
            "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
            "fetch_status": "not_applicable",
        },
        required=True,
    )
    csv_path, md_path = write_quality_reports(quality, layout)
    csv_row = _validate_quality_csv(csv_path)
    canonical_path = _catalog_canonical_path(
        layout,
        args.dataset,
        canonical_paths,
        args.run_id,
    )
    CatalogStore(layout).upsert(
        _catalog_entry_from_quality(
            dataset=args.dataset,
            layout=layout,
            quality=quality,
            canonical_path=canonical_path,
            csv_path=csv_path,
            md_path=md_path,
            start_date=start,
            end_date=end,
            published=False,
        )
    )
    return {
        "ok": True,
        "command": "validate",
        "dataset": args.dataset,
        "exchange": exchange,
        "quality_status": quality.quality_status,
        "fetch_status": quality.fetch_status,
        "dataset_status": quality.dataset_status,
        "quality_csv_path": csv_path,
        "quality_markdown_path": md_path,
        "coverage": asdict(quality.coverage),
        "thresholds": asdict(thresholds),
        "denominator_mode": quality.denominator_mode,
        "input_config_hash": quality.input_config_hash,
        "quality_csv_fields": sorted(csv_row),
        "catalog_status": "candidate_unpublished",
    }


def cmd_validate(args: argparse.Namespace) -> dict[str, Any]:
    from .catalog import CatalogStore
    from .validation import QualityThresholds, validate_dataset, write_quality_reports

    if args.dataset == DATASET_HS300_INDEX:
        return _cmd_validate_hs300_index(args)
    if args.dataset == DATASET_TRADE_CALENDAR:
        return _cmd_validate_trade_calendar(args)

    lake_root = _resolve_lake_root(args.lake_root)
    layout = LakeLayout(lake_root)
    symbols = _split_csv(args.symbols)
    if args.dataset in {DATASET_PRICES, DATASET_ADJ_FACTOR}:
        _require_symbols(symbols)
    elif args.dataset not in {
        DATASET_INDEX_MEMBERS,
        DATASET_INDEX_WEIGHTS,
        DATASET_STOCK_BASIC,
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
        DATASET_EVENTS,
    }:
        raise CliUsageError(f"validate 暂不支持 dataset={args.dataset}")
    start, end = _date_range(args)
    records = _read_manifest_context(layout, args.run_id)
    canonical_paths = _canonical_paths_for_run(layout, args.dataset, args.run_id)
    thresholds = QualityThresholds(
        prices_missing_rate_pass=args.prices_missing_rate_pass,
        prices_missing_rate_warn=args.prices_missing_rate_warn,
        prices_missing_rate_fail=args.prices_missing_rate_fail,
    )
    validation_context: dict[str, Any] = {
        "manifest_records": records,
        "canonical_paths": canonical_paths,
        "run_id": args.run_id,
    }
    if args.dataset in {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS}:
        index_code = str(args.index_code or "399300.SZ").strip().upper()
        validation_context["index_code"] = index_code
    if args.dataset in {DATASET_TRADE_STATUS, DATASET_PRICES_LIMIT}:
        _require_symbols(symbols)
    open_trade_dates = _split_csv(args.open_trade_dates)
    if open_trade_dates:
        validation_context["open_trade_dates"] = open_trade_dates
        validation_context["expected_dates"] = open_trade_dates
    if getattr(args, "use_trade_status_denominator", False) and args.dataset in {
        DATASET_PRICES,
        DATASET_ADJ_FACTOR,
    }:
        from .readers import read_dataset

        trade_status = read_dataset(
            DATASET_TRADE_STATUS,
            lake_root,
            filters={
                "start_date": start,
                "end_date": end,
                "symbols": symbols or None,
            },
            required=True,
        )
        if not trade_status.available or trade_status.frame is None:
            raise CliExecutionError(
                "trade_status denominator 不可用，不能声明 production prices coverage"
            )
        tradable = trade_status.frame
        if "is_tradable" in tradable.columns:
            tradable = tradable[tradable["is_tradable"].astype(bool)]
        validation_context["expected_pairs"] = [
            {"trade_date": row.trade_date, "symbol": row.symbol}
            for row in tradable[["trade_date", "symbol"]].itertuples(index=False)
        ]
    if getattr(args, "is_pit_universe", False):
        validation_context["is_pit_universe"] = True
        validation_context["universe_mode"] = "pit_index_members"
    if getattr(args, "decision_time", None):
        validation_context["decision_time"] = args.decision_time
    quality = validate_dataset(
        args.dataset,
        lake_root,
        (start, end),
        symbols or None,
        thresholds,
        validation_context,
        required=True,
    )
    csv_path, md_path = write_quality_reports(quality, layout)
    csv_row = _validate_quality_csv(csv_path)
    canonical_path = _catalog_canonical_path(
        layout,
        args.dataset,
        canonical_paths,
        args.run_id,
    )
    CatalogStore(layout).upsert(
        _catalog_entry_from_quality(
            dataset=args.dataset,
            layout=layout,
            quality=quality,
            canonical_path=canonical_path,
            csv_path=csv_path,
            md_path=md_path,
            published=False,
        )
    )
    return {
        "ok": True,
        "command": "validate",
        "dataset": args.dataset,
        "quality_status": quality.quality_status,
        "fetch_status": quality.fetch_status,
        "dataset_status": quality.dataset_status,
        "quality_csv_path": csv_path,
        "quality_markdown_path": md_path,
        "coverage": asdict(quality.coverage),
        "thresholds": asdict(thresholds),
        "denominator_mode": quality.denominator_mode,
        "input_config_hash": quality.input_config_hash,
        "quality_csv_fields": sorted(csv_row),
        "catalog_status": "candidate_unpublished",
    }


def cmd_revalidate(args: argparse.Namespace) -> dict[str, Any]:
    from .catalog import CatalogError, CatalogStore

    lake_root = _resolve_lake_root(args.lake_root)
    store = CatalogStore(LakeLayout(lake_root))
    try:
        previous = store.get(args.dataset)
    except CatalogError:
        previous = None
    payload = cmd_validate(args)
    if previous is not None and previous.published:
        try:
            current = store.get(args.dataset)
        except CatalogError:
            current = None
        if (
            current is not None
            and current.latest_manifest_run_id == previous.latest_manifest_run_id
            and current.quality_status != "fail"
        ):
            store.upsert(
                replace(
                    current,
                    published=True,
                    published_at=previous.published_at,
                    updated_at=current.updated_at,
                )
            )
    return {
        **payload,
        "command": "revalidate",
        "network_calls": 0,
        "canonical_writes": 0,
        "quality_writes": 2,
        "catalog_writes": 1,
    }


def cmd_publish(args: argparse.Namespace) -> dict[str, Any]:
    from .catalog import CatalogError, CatalogStore

    lake_root = _resolve_lake_root(args.lake_root)
    layout = LakeLayout(lake_root)
    store = CatalogStore(layout)
    try:
        entry = store.get(args.dataset)
    except CatalogError as exc:
        raise StructuredCliError("catalog_missing", str(exc)) from exc
    if entry.quality_status == "fail":
        raise StructuredCliError(
            "quality_failed",
            f"dataset={args.dataset} quality_status=fail，禁止 publish",
        )
    if entry.quality_status == "warn" and not args.allow_warn:
        raise StructuredCliError(
            "quality_warn_blocked",
            f"dataset={args.dataset} quality_status=warn；如需发布必须显式 --allow-warn",
        )
    published_at = datetime.now(timezone.utc).isoformat()
    published = replace(
        entry,
        published=True,
        published_at=published_at,
        updated_at=published_at,
    )
    path = store.upsert(published)
    return {
        "ok": True,
        "command": "publish",
        "dataset": args.dataset,
        "publish_status": "published",
        "published_at": published_at,
        "quality_status": published.quality_status,
        "readiness_status": published.readiness_status,
        "pit_status": published.pit_status,
        "catalog_path": path,
    }


def cmd_report_readiness(args: argparse.Namespace) -> dict[str, Any]:
    from .catalog import build_catalog_coverage_report, build_production_readiness_report

    lake_root = _resolve_lake_root(args.lake_root, required=True)
    datasets = tuple(_split_csv(args.datasets)) if args.datasets else None
    required_source = str(getattr(args, "required_source", "") or "").strip() or None
    if args.report == "coverage":
        if datasets is None:
            return build_catalog_coverage_report(lake_root)
        return build_catalog_coverage_report(lake_root, datasets=datasets)
    if datasets is None:
        return build_production_readiness_report(
            lake_root,
            realism_mode=args.realism_mode,
            required_source=required_source,
        )
    return build_production_readiness_report(
        lake_root,
        datasets=datasets,
        realism_mode=args.realism_mode,
        required_source=required_source,
    )


def _backup_request_from_args(args: argparse.Namespace) -> Any:
    from .backup_restore import BackupRequest

    return BackupRequest(
        release_id=args.release_id,
        run_id=args.run_id,
        dataset=args.dataset,
        lake_root=args.lake_root,
        archive_root=args.archive_root,
        backup_root=args.backup_root,
        restore_root=args.restore_root,
        include_raw=bool(args.include_raw),
        include_canonical=bool(args.include_canonical),
        include_gold=bool(args.include_gold),
        include_quality=bool(args.include_quality),
        execute=bool(getattr(args, "execute", False)),
    )


def _restore_request_from_args(args: argparse.Namespace) -> Any:
    from .backup_restore import RestoreRequest

    return RestoreRequest(
        release_id=args.release_id,
        run_id=args.run_id,
        dataset=args.dataset,
        lake_root=args.lake_root,
        archive_root=args.archive_root,
        backup_root=args.backup_root,
        restore_root=args.restore_root,
        include_raw=bool(args.include_raw),
        include_canonical=bool(args.include_canonical),
        include_gold=bool(args.include_gold),
        include_quality=bool(args.include_quality),
        execute=bool(getattr(args, "execute", False)),
    )


def _map_backup_restore_error(exc: Exception) -> StructuredCliError:
    code = str(getattr(exc, "code", "backup_restore_error"))
    return StructuredCliError(code, str(exc))


def cmd_backup_plan(args: argparse.Namespace) -> dict[str, Any]:
    from .backup_restore import BackupRestoreError, backup_plan

    try:
        return backup_plan(_backup_request_from_args(args))
    except BackupRestoreError as exc:
        raise _map_backup_restore_error(exc) from exc


def cmd_backup_run(args: argparse.Namespace) -> dict[str, Any]:
    from .backup_restore import BackupRestoreError, backup_run

    try:
        return backup_run(_backup_request_from_args(args))
    except BackupRestoreError as exc:
        raise _map_backup_restore_error(exc) from exc


def cmd_backup_verify(args: argparse.Namespace) -> dict[str, Any]:
    from .backup_restore import BackupRestoreError, backup_verify

    try:
        return backup_verify(_backup_request_from_args(args))
    except BackupRestoreError as exc:
        raise _map_backup_restore_error(exc) from exc


def cmd_backup_report(args: argparse.Namespace) -> dict[str, Any]:
    from .backup_restore import BackupRestoreError, backup_report

    try:
        return backup_report(_backup_request_from_args(args))
    except BackupRestoreError as exc:
        raise _map_backup_restore_error(exc) from exc


def cmd_restore_plan(args: argparse.Namespace) -> dict[str, Any]:
    from .backup_restore import BackupRestoreError, restore_plan

    try:
        return restore_plan(_restore_request_from_args(args))
    except BackupRestoreError as exc:
        raise _map_backup_restore_error(exc) from exc


def cmd_restore_run(args: argparse.Namespace) -> dict[str, Any]:
    from .backup_restore import BackupRestoreError, restore_run

    try:
        return restore_run(_restore_request_from_args(args))
    except BackupRestoreError as exc:
        raise _map_backup_restore_error(exc) from exc


def cmd_restore_drill(args: argparse.Namespace) -> dict[str, Any]:
    from .backup_restore import BackupRestoreError, restore_drill

    try:
        return restore_drill(_restore_request_from_args(args))
    except BackupRestoreError as exc:
        raise _map_backup_restore_error(exc) from exc


def _hs300_replay_params(args: argparse.Namespace) -> dict[str, Any]:
    start, end = _date_range(args)
    return {
        "target_dataset": DATASET_HS300_INDEX,
        "index_code": str(args.index_code or "399300.SZ").strip().upper(),
        "start_date": start,
        "end_date": end,
        "explicit_real_execution": True,
        "offline": False,
    }


def _date_matches(actual: object, expected: str | None) -> bool:
    if expected is None:
        return True
    try:
        return _parse_contract_date(str(actual)) == _parse_contract_date(str(expected))
    except StructuredCliError:
        return False


def _manifest_matches_replay_request(
    record: Mapping[str, Any],
    args: argparse.Namespace,
) -> bool:
    from .normalization import DatasetMappingError, map_raw_to_dataset

    if record.get("status") != "success":
        return False
    if record.get("run_id") != _run_id(args) or record.get("batch_id") != _batch_id(args):
        return False
    try:
        mapped_dataset = map_raw_to_dataset(record)
    except DatasetMappingError:
        return False
    if mapped_dataset != args.dataset:
        return False
    params = record.get("params")
    params = params if isinstance(params, Mapping) else {}
    if args.dataset == DATASET_HS300_INDEX:
        requested_index_code = str(args.index_code or "399300.SZ").strip().upper()
        actual_index_code = str(params.get("index_code", "399300.SZ")).strip().upper()
        if actual_index_code != requested_index_code:
            return False
    start = getattr(args, "start_date", None)
    end = getattr(args, "end_date", None)
    actual_start = params.get("start_date") or params.get("trade_date")
    actual_end = params.get("end_date") or params.get("trade_date")
    if actual_start is not None and not _date_matches(actual_start, start):
        return False
    if actual_end is not None and not _date_matches(actual_end, end):
        return False
    return True


def cmd_replay(args: argparse.Namespace) -> dict[str, Any]:
    lake_root = _resolve_lake_root(args.lake_root, required=True)
    layout = LakeLayout(lake_root)

    from .storage import load_manifest_index, verify_manifest_raw

    for record in load_manifest_index(layout, verify_raw=False).values():
        if _manifest_matches_replay_request(record, args):
            verify_manifest_raw(record, layout)
            return {
                "ok": True,
                "command": "replay",
                "dataset": args.dataset,
                "run_id": _run_id(args),
                "batch_id": _batch_id(args),
                "source": record.get("source"),
                "interface": record.get("interface"),
                "idempotency_key": record.get("idempotency_key"),
                "status": "skipped"
                if args.dataset == DATASET_HS300_INDEX
                else "ready_for_offline_replay",
                "attempts": 0,
                "network_calls": 0,
                "writes": 0,
                "canonical_writes": 0,
                "quality_writes": 0,
                "raw_path": record.get("raw_path"),
                "replay_source": "manifest_raw",
                "auto_execute": False,
            }
    raise StructuredCliError(
        "replay_missing",
        f"缺少 dataset={args.dataset} run_id/batch_id/start/end 对应的 success manifest，replay 不会触发真实 source",
    )


def cmd_read(args: argparse.Namespace) -> dict[str, Any]:
    lake_root = _resolve_lake_root(args.lake_root)
    from .readers import QualityPolicy, read_dataset

    filters = {
        "start": args.start_date,
        "end": args.end_date,
        "symbols": _split_csv(args.symbols) or None,
        "columns": _split_csv(args.columns) or None,
    }
    if args.dataset == DATASET_HS300_INDEX:
        filters["index_code"] = args.index_code
    if args.dataset == DATASET_TRADE_CALENDAR:
        filters["exchange"] = str(args.exchange or "SSE").strip().upper()
    result = read_dataset(
        args.dataset,
        lake_root,
        filters=filters,
        quality_policy=QualityPolicy(allow_warn=bool(getattr(args, "allow_warn", False)), required=True),
        required=True,
    )
    if not result.available or result.frame is None:
        codes = ",".join(str(issue.get("code")) for issue in result.issues)
        raise CliExecutionError(
            f"dataset={args.dataset} 不可读: {result.status}; issues={codes}"
        )
    frame = result.frame

    return {
        "ok": True,
        "command": "read",
        "dataset": args.dataset,
        "row_count": int(len(frame)),
        "columns": list(frame.columns),
        "sample": frame.head(args.limit).to_dict("records"),
    }


def _canonical_frame(args: argparse.Namespace) -> pd.DataFrame:
    layout = LakeLayout(args.lake_root)
    paths = sorted(layout.canonical_dataset_root(args.dataset).rglob("*.parquet"))
    if not paths:
        raise CliExecutionError("canonical parquet 不存在，无法 compare")
    return pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)


def _reference_frame(left: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    from .comparison import load_comparison_frame

    if args.right_path:
        return load_comparison_frame(args.right_path)
    if args.reference_fixture == "fake":
        right = left.copy()
        right["source"] = "reference"
        return right
    raise CliUsageError("compare 需要 --right-path 或 --reference-fixture fake")


def cmd_compare(args: argparse.Namespace) -> dict[str, Any]:
    _require_prices(args.dataset)
    from .comparison import (
        compare_sources,
        load_comparison_frame,
        status_counts,
        write_comparison_csv,
    )

    left = load_comparison_frame(args.left_path) if args.left_path else _canonical_frame(args)
    right = _reference_frame(left, args)
    rows = compare_sources(
        left,
        right,
        args.dataset,
        _split_csv(args.keys),
        _split_csv(args.fields),
        args.tolerance,
    )
    output_path = None
    if args.output:
        output_path = write_comparison_csv(rows, args.output)
    return {
        "ok": True,
        "command": "compare",
        "dataset": args.dataset,
        "comparison_mode": "fake_reference",
        "row_count": len(rows),
        "status_counts": status_counts(rows),
        "comparison_rows": [row.to_dict() for row in rows],
        "output_path": output_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m market_data.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common_plan(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--lake-root", default="data/market_data")
        subparser.add_argument("--dataset", default=DATASET_PRICES)
        subparser.add_argument("--source", default=SOURCE_FAKE)
        subparser.add_argument("--interface", default=INTERFACE_PRICES_DAILY)
        subparser.add_argument("--symbols", required=True)
        subparser.add_argument("--start-date", required=True)
        subparser.add_argument("--end-date", required=True)

    plan = subparsers.add_parser("plan")
    common_plan(plan)
    plan.set_defaults(handler=cmd_plan)

    def common_p0(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--datasets")
        subparser.add_argument("--dataset", default=DATASET_PRICES)
        subparser.add_argument("--start-date")
        subparser.add_argument("--end-date")
        subparser.add_argument("--as-of-trade-date")
        subparser.add_argument("--coverage-denominator-ref")
        subparser.add_argument("--coverage-denominator", type=int, default=0)
        subparser.add_argument("--run-id", default="run-cr014-s03")
        subparser.add_argument("--batch-id", default="p0-01")
        subparser.add_argument("--candidate-path")
        subparser.add_argument("--candidate-audit-path")
        subparser.add_argument("--quality-status", default="pass")
        subparser.add_argument("--readiness-status", default="available")
        subparser.add_argument("--lineage-checksum", default="lineage-fixture")

    p0_plan = subparsers.add_parser("p0-plan")
    common_p0(p0_plan)
    p0_plan.set_defaults(handler=cmd_p0_plan)

    p0_run = subparsers.add_parser("p0-run")
    common_p0(p0_run)
    p0_run.add_argument("--authorization-id")
    p0_run.add_argument("--approved-by")
    p0_run.add_argument("--allowed-sources")
    p0_run.add_argument("--allowed-interfaces")
    p0_run.add_argument("--cp5-approved", action="store_true")
    p0_run.add_argument("--lld-confirmed", action="store_true")
    p0_run.add_argument("--dependencies-satisfied", action="store_true")
    p0_run.add_argument("--file-conflict-free", action="store_true")
    p0_run.set_defaults(handler=cmd_p0_run)

    p0_normalize = subparsers.add_parser("p0-normalize")
    common_p0(p0_normalize)
    p0_normalize.add_argument("--source", default="fixture")
    p0_normalize.add_argument("--source-interface", default="fixture.p0")
    p0_normalize.add_argument("--schema-hash", default="schema-fixture")
    p0_normalize.add_argument("--row-count", type=int, default=0)
    p0_normalize.add_argument("--raw-ref")
    p0_normalize.set_defaults(handler=cmd_p0_normalize)

    p0_replay = subparsers.add_parser("p0-replay")
    common_p0(p0_replay)
    p0_replay.add_argument("--source", default="fixture")
    p0_replay.add_argument("--source-interface", default="fixture.p0")
    p0_replay.add_argument("--schema-hash", default="schema-fixture")
    p0_replay.add_argument("--row-count", type=int, default=0)
    p0_replay.add_argument("--manifest-present", action="store_true")
    p0_replay.set_defaults(handler=cmd_p0_replay)

    p0_validate = subparsers.add_parser("p0-validate")
    common_p0(p0_validate)
    p0_validate.set_defaults(handler=cmd_p0_validate)

    p0_publish = subparsers.add_parser("p0-publish")
    common_p0(p0_publish)
    p0_publish.add_argument("--source", default="fixture")
    p0_publish.add_argument("--source-interface", default="fixture.p0")
    p0_publish.add_argument("--schema-hash", default="schema-fixture")
    p0_publish.add_argument("--row-count", type=int, default=0)
    p0_publish.add_argument("--published-at")
    p0_publish.add_argument("--universe-scope", default="all_a_share")
    p0_publish.add_argument("--publish", action="store_true")
    p0_publish.add_argument("--approval-token")
    p0_publish.add_argument("--approved-by")
    p0_publish.add_argument("--reason")
    p0_publish.set_defaults(handler=cmd_p0_publish)

    p0_read = subparsers.add_parser("p0-read")
    common_p0(p0_read)
    p0_read.add_argument(
        "--read-scope",
        choices=("published_current_truth", "candidate_audit"),
        default="published_current_truth",
    )
    p0_read.add_argument("--pointer-present", action="store_true")
    p0_read.add_argument("--candidate-audit", action="store_true")
    p0_read.set_defaults(handler=cmd_p0_read)

    p0_query = subparsers.add_parser("p0-query")
    common_p0(p0_query)
    p0_query.add_argument(
        "--read-scope",
        choices=("published_current_truth", "candidate_audit"),
        default="published_current_truth",
    )
    p0_query.add_argument("--pointer-present", action="store_true")
    p0_query.add_argument("--candidate-audit", action="store_true")
    p0_query.set_defaults(handler=cmd_p0_query)

    def common_s09(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--authorization-id")
        subparser.add_argument("--approved-by")
        subparser.add_argument("--datasets")
        subparser.add_argument("--dataset", default=DATASET_PRICES)
        subparser.add_argument("--start-date")
        subparser.add_argument("--end-date")
        subparser.add_argument("--source", default=SOURCE_TUSHARE)
        subparser.add_argument("--interface", default=INTERFACE_PRICES_DAILY)
        subparser.add_argument("--lake-root")
        subparser.add_argument(
            "--window-policy",
            choices=("year", "quarter", "month", "trading-day-chunk"),
            default="month",
        )
        subparser.add_argument("--trading-day-chunk-size", type=int, default=20)
        subparser.add_argument("--credential-envs", default="TUSHARE_TOKEN")
        subparser.add_argument("--cp5-approved", action="store_true")
        subparser.add_argument("--lld-confirmed", action="store_true")
        subparser.add_argument("--dependencies-satisfied", action="store_true")
        subparser.add_argument("--file-conflict-free", action="store_true")
        subparser.add_argument("--implementation-allowed", action="store_true")
        subparser.add_argument("--stop-on-error", action="store_true")

    s09_plan = subparsers.add_parser("s09-plan")
    common_s09(s09_plan)
    s09_plan.set_defaults(handler=cmd_s09_plan)

    s09_run_gate = subparsers.add_parser("s09-run-gate")
    common_s09(s09_run_gate)
    s09_run_gate.set_defaults(handler=cmd_s09_run_gate)

    s09_rollback_preview = subparsers.add_parser("s09-rollback-preview")
    s09_rollback_preview.add_argument("--authorization-id")
    s09_rollback_preview.set_defaults(handler=cmd_s09_rollback_preview)

    fetch = subparsers.add_parser("fetch")
    common_plan(fetch)
    fetch.add_argument("--run-id")
    fetch.add_argument("--batch-id")
    fetch.add_argument("--seed", type=int, default=7)
    fetch.add_argument("--max-retries", type=int, default=0)
    fetch.add_argument("--enable-real-source", action="store_true")
    fetch.set_defaults(handler=cmd_fetch)

    hs300 = subparsers.add_parser("hs300-backfill")
    hs300.add_argument("--lake-root")
    hs300.add_argument("--start-date", required=True)
    hs300.add_argument("--end-date", required=True)
    hs300.add_argument("--index-code", default="399300.SZ")
    hs300.add_argument("--run-id", default="run-hs300-index")
    hs300.add_argument("--batch-id", default="b1")
    hs300.add_argument("--dry-run", default="true")
    hs300.add_argument("--enable-real-source", action="store_true")
    hs300.set_defaults(handler=cmd_hs300_backfill)

    tushare_first = subparsers.add_parser("tushare-first-acquire")
    tushare_first.add_argument("--lake-root", required=True)
    tushare_first.add_argument("--dataset", required=True)
    tushare_first.add_argument("--interface")
    tushare_first.add_argument("--start-date", required=True)
    tushare_first.add_argument("--end-date", required=True)
    tushare_first.add_argument("--index-code", default="399300.SZ")
    tushare_first.add_argument("--symbol")
    tushare_first.add_argument("--symbols")
    tushare_first.add_argument("--exchange", default="SSE")
    tushare_first.add_argument("--list-status", default="L")
    tushare_first.add_argument("--fields")
    tushare_first.add_argument("--credential-env", default="TUSHARE_TOKEN")
    tushare_first.add_argument("--run-id", default="run-tushare-first")
    tushare_first.add_argument("--batch-id", default="b1")
    tushare_first.add_argument("--dry-run", default="true")
    tushare_first.add_argument("--enable-real-source", action="store_true")
    tushare_first.set_defaults(handler=cmd_tushare_first_acquire)

    jqdata_acquire = subparsers.add_parser("jqdata-acquire")
    jqdata_acquire.add_argument("--lake-root")
    jqdata_acquire.add_argument("--dataset", required=True)
    jqdata_acquire.add_argument("--interface")
    jqdata_acquire.add_argument("--index-code", default="399300.SZ")
    jqdata_acquire.add_argument("--symbols")
    jqdata_acquire.add_argument("--start-date", required=True)
    jqdata_acquire.add_argument("--end-date", required=True)
    jqdata_acquire.add_argument("--credential-env-username", default="JQDATA_USERNAME")
    jqdata_acquire.add_argument("--credential-env-password", default="JQDATA_PASSWORD")
    jqdata_acquire.add_argument("--run-id", default="run-jqdata-index-members")
    jqdata_acquire.add_argument("--batch-id", default="b1")
    jqdata_acquire.add_argument("--dry-run", default="true")
    jqdata_acquire.add_argument("--enable-real-source", action="store_true")
    jqdata_acquire.add_argument("--json", action="store_true")
    jqdata_acquire.set_defaults(handler=cmd_jqdata_acquire)

    prices_long_horizon = subparsers.add_parser("prices-long-horizon-plan")
    prices_long_horizon.add_argument("--lake-root", required=True)
    prices_long_horizon.add_argument("--start-date", required=True)
    prices_long_horizon.add_argument("--end-date", required=True)
    prices_long_horizon.add_argument("--symbols")
    prices_long_horizon.add_argument("--universe-source")
    prices_long_horizon.add_argument("--symbol-batch-size", type=int, default=100)
    prices_long_horizon.add_argument("--slice-days", type=int, default=31)
    prices_long_horizon.add_argument("--run-id", default="run-prices-long-horizon")
    prices_long_horizon.add_argument("--adjustment-policy", default="qfq")
    prices_long_horizon.add_argument("--credential-env", default="TUSHARE_TOKEN")
    prices_long_horizon.add_argument("--open-trade-dates")
    prices_long_horizon.add_argument("--dry-run", default="true")
    prices_long_horizon.set_defaults(handler=cmd_prices_long_horizon_plan)

    benchmark_calendar = subparsers.add_parser("benchmark-calendar-backfill")
    benchmark_calendar.add_argument("--lake-root", required=True)
    benchmark_calendar.add_argument("--start-date", required=True)
    benchmark_calendar.add_argument("--end-date", required=True)
    benchmark_calendar.add_argument("--index-code", default="399300.SZ")
    benchmark_calendar.add_argument("--exchange", default="SSE")
    benchmark_calendar.add_argument("--credential-env", default="TUSHARE_TOKEN")
    benchmark_calendar.add_argument("--run-id", default="run-benchmark-calendar")
    benchmark_calendar.add_argument("--dry-run", default="true")
    benchmark_calendar.set_defaults(handler=cmd_benchmark_calendar_backfill)

    normalize = subparsers.add_parser("normalize")
    normalize.add_argument("--lake-root")
    normalize.add_argument("--dataset", default=DATASET_PRICES)
    normalize.add_argument("--run-id")
    normalize.set_defaults(handler=cmd_normalize)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--lake-root")
    validate.add_argument("--dataset", default=DATASET_PRICES)
    validate.add_argument("--symbols")
    validate.add_argument("--index-code", default="399300.SZ")
    validate.add_argument("--exchange", default="SSE")
    validate.add_argument("--start-date", required=True)
    validate.add_argument("--end-date", required=True)
    validate.add_argument("--run-id")
    validate.add_argument("--open-trade-dates")
    validate.add_argument("--decision-time")
    validate.add_argument("--is-pit-universe", action="store_true")
    validate.add_argument("--use-trade-status-denominator", action="store_true")
    validate.add_argument("--prices-missing-rate-pass", type=float, default=0.0)
    validate.add_argument("--prices-missing-rate-warn", type=float, default=0.02)
    validate.add_argument("--prices-missing-rate-fail", type=float, default=0.05)
    validate.set_defaults(handler=cmd_validate)

    publish = subparsers.add_parser("publish")
    publish.add_argument("--lake-root")
    publish.add_argument("--dataset", default=DATASET_PRICES)
    publish.add_argument("--allow-warn", action="store_true")
    publish.set_defaults(handler=cmd_publish)

    revalidate = subparsers.add_parser("revalidate")
    revalidate.add_argument("--lake-root")
    revalidate.add_argument("--dataset", default=DATASET_PRICES)
    revalidate.add_argument("--symbols")
    revalidate.add_argument("--index-code", default="399300.SZ")
    revalidate.add_argument("--exchange", default="SSE")
    revalidate.add_argument("--start-date", required=True)
    revalidate.add_argument("--end-date", required=True)
    revalidate.add_argument("--run-id")
    revalidate.add_argument("--open-trade-dates")
    revalidate.add_argument("--decision-time")
    revalidate.add_argument("--is-pit-universe", action="store_true")
    revalidate.add_argument("--use-trade-status-denominator", action="store_true")
    revalidate.add_argument("--prices-missing-rate-pass", type=float, default=0.0)
    revalidate.add_argument("--prices-missing-rate-warn", type=float, default=0.02)
    revalidate.add_argument("--prices-missing-rate-fail", type=float, default=0.05)
    revalidate.set_defaults(handler=cmd_revalidate)

    replay = subparsers.add_parser("replay")
    replay.add_argument("--lake-root")
    replay.add_argument("--dataset", default=DATASET_HS300_INDEX)
    replay.add_argument("--start-date", required=True)
    replay.add_argument("--end-date", required=True)
    replay.add_argument("--index-code", default="399300.SZ")
    replay.add_argument("--run-id", required=True)
    replay.add_argument("--batch-id", required=True)
    replay.set_defaults(handler=cmd_replay)

    read = subparsers.add_parser("read")
    read.add_argument("--lake-root")
    read.add_argument("--dataset", default=DATASET_PRICES)
    read.add_argument("--start-date")
    read.add_argument("--end-date")
    read.add_argument("--symbols")
    read.add_argument("--index-code", default="399300.SZ")
    read.add_argument("--exchange", default="SSE")
    read.add_argument("--columns")
    read.add_argument("--limit", type=int, default=5)
    read.add_argument("--allow-warn", action="store_true")
    read.set_defaults(handler=cmd_read)

    readiness = subparsers.add_parser("report-readiness")
    readiness.add_argument("--lake-root", required=True)
    readiness.add_argument("--report", choices=("coverage", "production"), default="production")
    readiness.add_argument("--realism-mode", choices=("production_strict", "exploratory"), default="production_strict")
    readiness.add_argument("--datasets")
    readiness.add_argument("--required-source")
    readiness.set_defaults(handler=cmd_report_readiness)

    def common_backup_restore(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--lake-root")
        subparser.add_argument("--archive-root")
        subparser.add_argument("--backup-root")
        subparser.add_argument("--restore-root")
        subparser.add_argument("--release-id", required=True)
        subparser.add_argument("--run-id")
        subparser.add_argument("--dataset")
        subparser.add_argument("--include-raw", action=argparse.BooleanOptionalAction, default=True)
        subparser.add_argument("--include-canonical", action=argparse.BooleanOptionalAction, default=True)
        subparser.add_argument("--include-gold", action=argparse.BooleanOptionalAction, default=True)
        subparser.add_argument("--include-quality", action=argparse.BooleanOptionalAction, default=True)
        subparser.add_argument("--json", action="store_true")

    backup_plan_parser = subparsers.add_parser("backup-plan")
    common_backup_restore(backup_plan_parser)
    backup_plan_parser.set_defaults(handler=cmd_backup_plan)

    backup_run_parser = subparsers.add_parser("backup-run")
    common_backup_restore(backup_run_parser)
    backup_run_parser.add_argument("--execute", action="store_true")
    backup_run_parser.set_defaults(handler=cmd_backup_run)

    backup_verify_parser = subparsers.add_parser("backup-verify")
    common_backup_restore(backup_verify_parser)
    backup_verify_parser.set_defaults(handler=cmd_backup_verify)

    backup_report_parser = subparsers.add_parser("backup-report")
    common_backup_restore(backup_report_parser)
    backup_report_parser.set_defaults(handler=cmd_backup_report)

    restore_plan_parser = subparsers.add_parser("restore-plan")
    common_backup_restore(restore_plan_parser)
    restore_plan_parser.set_defaults(handler=cmd_restore_plan)

    restore_run_parser = subparsers.add_parser("restore-run")
    common_backup_restore(restore_run_parser)
    restore_run_parser.add_argument("--execute", action="store_true")
    restore_run_parser.set_defaults(handler=cmd_restore_run)

    restore_drill_parser = subparsers.add_parser("restore-drill")
    common_backup_restore(restore_drill_parser)
    restore_drill_parser.add_argument("--execute", action="store_true")
    restore_drill_parser.set_defaults(handler=cmd_restore_drill)

    compare = subparsers.add_parser("compare")
    compare.add_argument("--lake-root", default="data/market_data")
    compare.add_argument("--dataset", default=DATASET_PRICES)
    compare.add_argument("--left-path")
    compare.add_argument("--right-path")
    compare.add_argument("--reference-fixture", choices=("fake",), default="fake")
    compare.add_argument("--keys", default="trade_date,symbol")
    compare.add_argument("--fields", default="close")
    compare.add_argument("--tolerance", type=float, default=0.0)
    compare.add_argument("--output")
    compare.set_defaults(handler=cmd_compare)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        payload = args.handler(args)
        _print_json(payload)
        return 0
    except SystemExit:
        raise
    except (CliUsageError, CliExecutionError) as exc:
        print(json.dumps(_error_payload(exc), ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:
        wrapped = CliExecutionError(str(exc))
        print(json.dumps(_error_payload(wrapped), ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return wrapped.exit_code


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CliExecutionError",
    "CliUsageError",
    "QualityReportShapeError",
    "RealSourceDisabledError",
    "LakeRootMissingError",
    "BenchmarkCalendarPlanSpec",
    "JQDataRunSpec",
    "PricesLongHorizonPlanSpec",
    "TushareFirstRunSpec",
    "build_benchmark_calendar_backfill_plan",
    "build_jqdata_plan",
    "build_prices_long_horizon_plan",
    "build_tushare_first_plan",
    "cmd_benchmark_calendar_backfill",
    "cmd_backup_plan",
    "cmd_backup_report",
    "cmd_backup_run",
    "cmd_backup_verify",
    "cmd_p0_plan",
    "cmd_p0_publish",
    "cmd_p0_query",
    "cmd_p0_read",
    "cmd_p0_replay",
    "cmd_p0_run",
    "cmd_p0_normalize",
    "cmd_p0_validate",
    "cmd_prices_long_horizon_plan",
    "cmd_publish",
    "cmd_jqdata_acquire",
    "cmd_report_readiness",
    "cmd_restore_drill",
    "cmd_restore_plan",
    "cmd_restore_run",
    "cmd_s09_plan",
    "cmd_s09_rollback_preview",
    "cmd_s09_run_gate",
    "cmd_tushare_first_acquire",
    "emit_jqdata_runbook_summary",
    "emit_tushare_first_runbook_summary",
    "build_parser",
    "main",
]
