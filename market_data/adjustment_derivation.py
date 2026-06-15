"""CR017 qfq/hfq/returns_adjusted 离线 candidate 派生。"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .adjustment_contracts import (
    CONTRACT_STATUS_FAIL,
    CONTRACT_STATUS_PASS,
    CONTRACT_STATUS_REQUIRED_MISSING,
    PROVIDER_FACTOR_DIRECTION_INVERSE_RATIO,
    PROVIDER_FACTOR_DIRECTION_QFQ_RATIO,
    validate_adj_factor_contract,
    validate_derived_view_isolated,
    validate_prices_raw_contract,
)
from .contracts import (
    ADJUSTMENT_POLICY_HFQ,
    ADJUSTMENT_POLICY_QFQ,
    CR017_DERIVATION_VERSION,
    CR017_FORBIDDEN_OPERATION_COUNTERS,
    CR017_SCHEMA_VERSION,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_RETURNS_ADJUSTED,
    QUALITY_STATUS_FAIL,
    QUALITY_STATUS_PASS,
)
from .validation import CR017_MISSING_FACTOR_DIRECTION

DERIVATION_STATUS_PASS = CONTRACT_STATUS_PASS
DERIVATION_STATUS_FAIL = CONTRACT_STATUS_FAIL
DERIVATION_STATUS_REQUIRED_MISSING = CONTRACT_STATUS_REQUIRED_MISSING

MISSING_AS_OF_TRADE_DATE = "missing_as_of_trade_date"
MISSING_INPUT_SNAPSHOT_ID = "missing_input_snapshot_id"
MISSING_BASE_TRACE = "missing_hfq_base_trace"
MISSING_FACTOR_FOR_DATE = "missing_factor_for_date"
MIXED_ADJUSTMENT_POLICY = "mixed_adjustment_policy"
MISSING_PRICE_WINDOW = "missing_price_window"
UNSUPPORTED_RETURN_INPUT = "unsupported_return_input"


def zero_operation_counts() -> dict[str, int]:
    return dict(CR017_FORBIDDEN_OPERATION_COUNTERS)


@dataclass(frozen=True, slots=True)
class DerivationInput:
    raw_rows: Sequence[Mapping[str, Any]] = ()
    factor_rows: Sequence[Mapping[str, Any]] = ()
    adjusted_rows: Sequence[Mapping[str, Any]] = ()
    as_of_trade_date: str = ""
    input_snapshot_id: str = ""
    source_run_id: str = ""
    derivation_version: str = CR017_DERIVATION_VERSION
    base_trade_date: str = ""
    base_date_policy: str = ""
    research_adjustment_policy: str = ""
    return_type: str = "simple"


@dataclass(frozen=True, slots=True)
class DerivedViewCandidate:
    view_id: str
    schema_version: str
    derivation_version: str
    source_run_id: str
    input_snapshot_id: str
    quality_status: str
    status: str
    rows: tuple[dict[str, Any], ...] = ()
    lineage_checksum: str = ""
    reason_code: str = ""
    missing_fields: tuple[str, ...] = ()
    operation_counts: dict[str, int] = field(default_factory=zero_operation_counts)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == DERIVATION_STATUS_PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "view_id": self.view_id,
            "schema_version": self.schema_version,
            "derivation_version": self.derivation_version,
            "source_run_id": self.source_run_id,
            "input_snapshot_id": self.input_snapshot_id,
            "quality_status": self.quality_status,
            "status": self.status,
            "rows": [dict(item) for item in self.rows],
            "lineage_checksum": self.lineage_checksum,
            "reason_code": self.reason_code,
            "missing_fields": list(self.missing_fields),
            "operation_counts": dict(self.operation_counts),
            "metadata": dict(self.metadata),
        }


def derive_qfq(input_data: DerivationInput) -> DerivedViewCandidate:
    required = _missing_input_fields(
        {
            "as_of_trade_date": input_data.as_of_trade_date,
            "input_snapshot_id": input_data.input_snapshot_id,
        }
    )
    if required:
        reason = MISSING_AS_OF_TRADE_DATE if "as_of_trade_date" in required else MISSING_INPUT_SNAPSHOT_ID
        return _blocked_candidate(CR017_VIEW_PRICES_QFQ, input_data, reason, required)
    return _derive_price_view(
        input_data,
        view_id=CR017_VIEW_PRICES_QFQ,
        policy=ADJUSTMENT_POLICY_QFQ,
        anchor_trade_date=input_data.as_of_trade_date,
        anchor_kind="as_of_trade_date",
    )


def derive_hfq(input_data: DerivationInput) -> DerivedViewCandidate:
    required = _missing_input_fields(
        {
            "base_trade_date": input_data.base_trade_date,
            "base_date_policy": input_data.base_date_policy,
            "input_snapshot_id": input_data.input_snapshot_id,
        }
    )
    if required:
        return _blocked_candidate(CR017_VIEW_PRICES_HFQ, input_data, MISSING_BASE_TRACE, required)
    return _derive_price_view(
        input_data,
        view_id=CR017_VIEW_PRICES_HFQ,
        policy=ADJUSTMENT_POLICY_HFQ,
        anchor_trade_date=input_data.base_trade_date,
        anchor_kind="base_trade_date",
    )


def derive_returns_adjusted(input_data: DerivationInput) -> DerivedViewCandidate:
    if input_data.adjusted_rows:
        policy_check = _single_adjustment_policy(input_data.adjusted_rows)
        if not policy_check[0]:
            return _blocked_candidate(
                CR017_VIEW_RETURNS_ADJUSTED,
                input_data,
                policy_check[1],
                ("research_adjustment_policy",),
                status=DERIVATION_STATUS_FAIL,
            )
        source_rows = _sorted_rows(input_data.adjusted_rows)
        policy = policy_check[2]
        input_view_id = _view_id_from_policy(policy)
    elif input_data.raw_rows and input_data.factor_rows:
        policy = input_data.research_adjustment_policy
        if policy == ADJUSTMENT_POLICY_QFQ:
            candidate = derive_qfq(input_data)
        elif policy == ADJUSTMENT_POLICY_HFQ:
            candidate = derive_hfq(input_data)
        else:
            return _blocked_candidate(
                CR017_VIEW_RETURNS_ADJUSTED,
                input_data,
                UNSUPPORTED_RETURN_INPUT,
                ("research_adjustment_policy",),
                status=DERIVATION_STATUS_FAIL,
            )
        if not candidate.passed:
            return _copy_failure(CR017_VIEW_RETURNS_ADJUSTED, input_data, candidate)
        source_rows = candidate.rows
        input_view_id = candidate.view_id
    else:
        return _blocked_candidate(
            CR017_VIEW_RETURNS_ADJUSTED,
            input_data,
            UNSUPPORTED_RETURN_INPUT,
            ("adjusted_rows",),
            status=DERIVATION_STATUS_FAIL,
        )

    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in source_rows:
        grouped.setdefault(str(row.get("symbol") or ""), []).append(row)
    if any(len(rows) < 2 for rows in grouped.values()) or not grouped:
        return _blocked_candidate(
            CR017_VIEW_RETURNS_ADJUSTED,
            input_data,
            MISSING_PRICE_WINDOW,
            ("adjusted_rows",),
            status=DERIVATION_STATUS_FAIL,
        )

    candidate_source_run_id = _resolve_source_run_id(input_data, source_rows, ())
    lineage = explain_derivation_lineage(
        input_data,
        view_id=CR017_VIEW_RETURNS_ADJUSTED,
        extra={
            "input_view_id": input_view_id,
            "research_adjustment_policy": policy,
            "return_type": input_data.return_type,
            "source_lineage": _source_lineage(source_rows),
        },
    )
    rows: list[dict[str, Any]] = []
    for symbol, symbol_rows in grouped.items():
        ordered = sorted(symbol_rows, key=lambda item: str(item.get("trade_date") or ""))
        for previous, current in zip(ordered, ordered[1:]):
            start_price = _adjusted_close(previous)
            end_price = _adjusted_close(current)
            if start_price is None or end_price is None or start_price <= 0 or end_price <= 0:
                return _blocked_candidate(
                    CR017_VIEW_RETURNS_ADJUSTED,
                    input_data,
                    MISSING_PRICE_WINDOW,
                    ("adjusted_close",),
                    status=DERIVATION_STATUS_FAIL,
                )
            trade_date = str(current.get("trade_date") or "")
            rows.append(
                {
                    "view_id": CR017_VIEW_RETURNS_ADJUSTED,
                    "schema_version": CR017_SCHEMA_VERSION,
                    "derivation_version": input_data.derivation_version,
                    "source_run_id": candidate_source_run_id,
                    "lineage_checksum": lineage,
                    "quality_status": QUALITY_STATUS_PASS,
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "research_adjustment_policy": policy,
                    "return_type": input_data.return_type,
                    "adjusted_return": (end_price / start_price) - 1.0,
                    "start_price_ref": _price_ref(input_view_id, previous),
                    "end_price_ref": _price_ref(input_view_id, current),
                    "input_snapshot_id": input_data.input_snapshot_id
                    or str(current.get("input_snapshot_id") or ""),
                }
            )

    return DerivedViewCandidate(
        view_id=CR017_VIEW_RETURNS_ADJUSTED,
        schema_version=CR017_SCHEMA_VERSION,
        derivation_version=input_data.derivation_version,
        source_run_id=candidate_source_run_id,
        input_snapshot_id=input_data.input_snapshot_id,
        quality_status=QUALITY_STATUS_PASS,
        status=DERIVATION_STATUS_PASS,
        rows=tuple(rows),
        lineage_checksum=lineage,
        operation_counts=zero_operation_counts(),
        metadata={
            "input_view_id": input_view_id,
            "research_adjustment_policy": policy,
            "return_type": input_data.return_type,
        },
    )


def explain_derivation_lineage(
    input_data: DerivationInput,
    *,
    view_id: str,
    extra: Mapping[str, Any] | None = None,
) -> str:
    payload = {
        "view_id": view_id,
        "schema_version": CR017_SCHEMA_VERSION,
        "derivation_version": input_data.derivation_version,
        "source_run_id": input_data.source_run_id,
        "input_snapshot_id": input_data.input_snapshot_id,
        "as_of_trade_date": input_data.as_of_trade_date,
        "base_trade_date": input_data.base_trade_date,
        "base_date_policy": input_data.base_date_policy,
        "raw_lineage": _source_lineage(input_data.raw_rows),
        "factor_lineage": _source_lineage(input_data.factor_rows),
        "adjusted_lineage": _source_lineage(input_data.adjusted_rows),
        "extra": dict(extra or {}),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _derive_price_view(
    input_data: DerivationInput,
    *,
    view_id: str,
    policy: str,
    anchor_trade_date: str,
    anchor_kind: str,
) -> DerivedViewCandidate:
    isolation = validate_derived_view_isolated(view_id)
    if not isolation.passed:
        return _copy_contract_failure(view_id, input_data, isolation)
    raw_contract = validate_prices_raw_contract(input_data.raw_rows)
    if not raw_contract.passed:
        return _copy_contract_failure(view_id, input_data, raw_contract)
    factor_contract = validate_adj_factor_contract(input_data.factor_rows)
    if not factor_contract.passed:
        reason = factor_contract.reason_code or CR017_MISSING_FACTOR_DIRECTION
        return _copy_contract_failure(view_id, input_data, factor_contract, reason_code=reason)

    raw_rows = _sorted_rows(input_data.raw_rows)
    factor_rows = _sorted_rows(input_data.factor_rows)
    factors = _factor_index(factor_rows)
    symbols = {str(row.get("symbol") or "") for row in raw_rows}
    anchor_factors: dict[str, Mapping[str, Any]] = {}
    for symbol in symbols:
        anchor = factors.get((symbol, anchor_trade_date))
        if anchor is None:
            return _blocked_candidate(
                view_id,
                input_data,
                MISSING_FACTOR_FOR_DATE,
                (anchor_kind,),
            )
        anchor_factors[symbol] = anchor

    source_run_id = _resolve_source_run_id(input_data, raw_rows, factor_rows)
    lineage = explain_derivation_lineage(
        input_data,
        view_id=view_id,
        extra={
            "policy": policy,
            "anchor_trade_date": anchor_trade_date,
            "anchor_kind": anchor_kind,
            "raw_lineage": _source_lineage(raw_rows),
            "factor_lineage": _source_lineage(factor_rows),
        },
    )
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        symbol = str(row.get("symbol") or "")
        trade_date = str(row.get("trade_date") or "")
        trade_factor_row = factors.get((symbol, trade_date))
        if trade_factor_row is None:
            return _blocked_candidate(
                view_id,
                input_data,
                MISSING_FACTOR_FOR_DATE,
                ("trade_date",),
            )
        anchor_factor_row = anchor_factors[symbol]
        ratio = _factor_ratio(trade_factor_row, anchor_factor_row)
        metadata = {
            "view_id": view_id,
            "schema_version": CR017_SCHEMA_VERSION,
            "derivation_version": input_data.derivation_version,
            "source_run_id": source_run_id,
            "lineage_checksum": lineage,
            "quality_status": QUALITY_STATUS_PASS,
            "trade_date": trade_date,
            "symbol": symbol,
            "research_adjustment_policy": policy,
            "input_snapshot_id": input_data.input_snapshot_id,
            "raw_source_run_id": str(row.get("source_run_id") or ""),
            "factor_source_run_id": str(trade_factor_row.get("source_run_id") or ""),
        }
        if view_id == CR017_VIEW_PRICES_QFQ:
            metadata["as_of_trade_date"] = input_data.as_of_trade_date
        else:
            metadata["base_trade_date"] = input_data.base_trade_date
            metadata["factor_base_date_policy"] = input_data.base_date_policy
        for field_name in ("open", "high", "low", "close"):
            raw_value = _to_float(row.get(field_name))
            if raw_value is None or raw_value <= 0:
                return _blocked_candidate(view_id, input_data, "invalid_raw_price", (field_name,))
            metadata[f"raw_{field_name}"] = raw_value
            metadata[f"adjusted_{field_name}"] = raw_value * ratio
        rows.append(metadata)

    return DerivedViewCandidate(
        view_id=view_id,
        schema_version=CR017_SCHEMA_VERSION,
        derivation_version=input_data.derivation_version,
        source_run_id=source_run_id,
        input_snapshot_id=input_data.input_snapshot_id,
        quality_status=QUALITY_STATUS_PASS,
        status=DERIVATION_STATUS_PASS,
        rows=tuple(rows),
        lineage_checksum=lineage,
        operation_counts=zero_operation_counts(),
        metadata={
            "research_adjustment_policy": policy,
            "anchor_trade_date": anchor_trade_date,
            "anchor_kind": anchor_kind,
        },
    )


def _factor_ratio(
    trade_factor_row: Mapping[str, Any],
    anchor_factor_row: Mapping[str, Any],
) -> float:
    trade_factor = _to_float(trade_factor_row.get("adj_factor"))
    anchor_factor = _to_float(anchor_factor_row.get("adj_factor"))
    if trade_factor is None or anchor_factor is None or trade_factor <= 0 or anchor_factor <= 0:
        raise ValueError("adj_factor must be positive after contract validation")
    direction = str(trade_factor_row.get("provider_factor_direction") or "")
    if direction == PROVIDER_FACTOR_DIRECTION_QFQ_RATIO:
        return trade_factor / anchor_factor
    if direction == PROVIDER_FACTOR_DIRECTION_INVERSE_RATIO:
        return anchor_factor / trade_factor
    raise ValueError(f"unsupported provider_factor_direction: {direction}")


def _single_adjustment_policy(rows: Sequence[Mapping[str, Any]]) -> tuple[bool, str, str]:
    policies = {
        _policy_from_row(row)
        for row in rows
        if _policy_from_row(row)
    }
    if len(policies) != 1:
        return False, MIXED_ADJUSTMENT_POLICY, ""
    return True, "", next(iter(policies))


def _policy_from_row(row: Mapping[str, Any]) -> str:
    value = str(row.get("research_adjustment_policy") or row.get("adjustment_policy") or "")
    if value:
        return value
    view_id = str(row.get("view_id") or "")
    if view_id == CR017_VIEW_PRICES_QFQ:
        return ADJUSTMENT_POLICY_QFQ
    if view_id == CR017_VIEW_PRICES_HFQ:
        return ADJUSTMENT_POLICY_HFQ
    return ""


def _view_id_from_policy(policy: str) -> str:
    if policy == ADJUSTMENT_POLICY_HFQ:
        return CR017_VIEW_PRICES_HFQ
    return CR017_VIEW_PRICES_QFQ


def _adjusted_close(row: Mapping[str, Any]) -> float | None:
    value = row.get("adjusted_close", row.get("close"))
    return _to_float(value)


def _price_ref(view_id: str, row: Mapping[str, Any]) -> str:
    return f"{view_id}:{row.get('symbol')}:{row.get('trade_date')}:adjusted_close"


def _copy_contract_failure(
    view_id: str,
    input_data: DerivationInput,
    contract_result: Any,
    *,
    reason_code: str | None = None,
) -> DerivedViewCandidate:
    return _blocked_candidate(
        view_id,
        input_data,
        reason_code or str(getattr(contract_result, "reason_code", "") or "contract_failed"),
        tuple(getattr(contract_result, "missing_fields", ()) or ()),
        status=str(getattr(contract_result, "status", DERIVATION_STATUS_FAIL)),
    )


def _copy_failure(
    view_id: str,
    input_data: DerivationInput,
    candidate: DerivedViewCandidate,
) -> DerivedViewCandidate:
    return _blocked_candidate(
        view_id,
        input_data,
        candidate.reason_code,
        candidate.missing_fields,
        status=candidate.status,
    )


def _blocked_candidate(
    view_id: str,
    input_data: DerivationInput,
    reason_code: str,
    missing_fields: tuple[str, ...],
    *,
    status: str = DERIVATION_STATUS_REQUIRED_MISSING,
) -> DerivedViewCandidate:
    return DerivedViewCandidate(
        view_id=view_id,
        schema_version=CR017_SCHEMA_VERSION,
        derivation_version=input_data.derivation_version,
        source_run_id=_resolve_source_run_id(input_data, input_data.raw_rows, input_data.factor_rows),
        input_snapshot_id=input_data.input_snapshot_id,
        quality_status=QUALITY_STATUS_FAIL,
        status=status,
        rows=(),
        lineage_checksum=explain_derivation_lineage(
            input_data,
            view_id=view_id,
            extra={"blocked_reason": reason_code, "missing_fields": list(missing_fields)},
        ),
        reason_code=reason_code,
        missing_fields=missing_fields,
        operation_counts=zero_operation_counts(),
    )


def _resolve_source_run_id(
    input_data: DerivationInput,
    primary_rows: Sequence[Mapping[str, Any]],
    secondary_rows: Sequence[Mapping[str, Any]],
) -> str:
    if input_data.source_run_id:
        return input_data.source_run_id
    run_ids = [
        str(row.get("source_run_id") or "")
        for row in [*primary_rows, *secondary_rows]
        if str(row.get("source_run_id") or "")
    ]
    return "+".join(dict.fromkeys(run_ids))


def _source_lineage(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "trade_date": str(row.get("trade_date") or ""),
            "symbol": str(row.get("symbol") or ""),
            "source_run_id": str(row.get("source_run_id") or ""),
            "batch_id": str(row.get("batch_id") or ""),
            "lineage_checksum": str(row.get("lineage_checksum") or ""),
        }
        for row in _sorted_rows(rows)
    )


def _factor_index(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    return {
        (str(row.get("symbol") or ""), str(row.get("trade_date") or "")): row
        for row in rows
    }


def _sorted_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return sorted(rows, key=lambda row: (str(row.get("symbol") or ""), str(row.get("trade_date") or "")))


def _missing_input_fields(payload: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(field_name for field_name, value in payload.items() if _is_missing(value))


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value:
        return True
    try:
        return bool(math.isnan(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


def _to_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


__all__ = [
    "DERIVATION_STATUS_FAIL",
    "DERIVATION_STATUS_PASS",
    "DERIVATION_STATUS_REQUIRED_MISSING",
    "MISSING_AS_OF_TRADE_DATE",
    "MISSING_BASE_TRACE",
    "MISSING_FACTOR_FOR_DATE",
    "MISSING_INPUT_SNAPSHOT_ID",
    "MISSING_PRICE_WINDOW",
    "MIXED_ADJUSTMENT_POLICY",
    "UNSUPPORTED_RETURN_INPUT",
    "DerivationInput",
    "DerivedViewCandidate",
    "derive_hfq",
    "derive_qfq",
    "derive_returns_adjusted",
    "explain_derivation_lineage",
    "zero_operation_counts",
]
