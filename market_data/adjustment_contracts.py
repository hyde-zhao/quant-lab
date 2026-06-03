"""CR017 raw prices 与 adj_factor 事实源合同。"""

from __future__ import annotations

import math
from dataclasses import dataclass, field as dataclass_field
from typing import Any, Mapping, Sequence

from .contracts import (
    CR017_ADJ_FACTOR_REQUIRED_FIELDS,
    CR017_DERIVED_VIEW_IDS,
    CR017_FORBIDDEN_OPERATION_COUNTERS,
    CR017_PRICES_RAW_REQUIRED_FIELDS,
    CR017_REQUIRED_FIELD_SETS,
    CR017_SOURCE_LINEAGE_REQUIRED_FIELDS,
    CR017_VIEW_ADJ_FACTOR,
    CR017_VIEW_PRICES_RAW,
)
from .validation import (
    CR017_DERIVED_OVERWRITES_RAW,
    CR017_INVALID_ADJ_FACTOR,
    CR017_INVALID_FACTOR_DIRECTION,
    CR017_INVALID_RAW_OHLC,
    CR017_MISSING_FACTOR_DIRECTION,
    CR017_MISSING_LINEAGE,
)

CONTRACT_STATUS_PASS = "pass"
CONTRACT_STATUS_FAIL = "fail"
CONTRACT_STATUS_REQUIRED_MISSING = "required_missing"

PROVIDER_FACTOR_DIRECTION_QFQ_RATIO = "raw_times_trade_factor_div_asof_factor"
PROVIDER_FACTOR_DIRECTION_INVERSE_RATIO = "raw_times_asof_factor_div_trade_factor"
PROVIDER_FACTOR_DIRECTION_VALUES: tuple[str, ...] = (
    PROVIDER_FACTOR_DIRECTION_QFQ_RATIO,
    PROVIDER_FACTOR_DIRECTION_INVERSE_RATIO,
)

FACTOR_BASE_DATE_POLICY_AS_OF = "as_of_trade_date"
FACTOR_BASE_DATE_POLICY_PROVIDER_BASE = "provider_base_date"
FACTOR_BASE_DATE_POLICY_VALUES: tuple[str, ...] = (
    FACTOR_BASE_DATE_POLICY_AS_OF,
    FACTOR_BASE_DATE_POLICY_PROVIDER_BASE,
)


def zero_operation_counts() -> dict[str, int]:
    return dict(CR017_FORBIDDEN_OPERATION_COUNTERS)


@dataclass(frozen=True, slots=True)
class ContractCheckResult:
    status: str
    passed: bool
    reason_code: str = ""
    field: str = ""
    missing_fields: tuple[str, ...] = ()
    derivation_allowed: bool = True
    operation_counts: dict[str, int] = dataclass_field(default_factory=zero_operation_counts)
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "reason_code": self.reason_code,
            "field": self.field,
            "missing_fields": list(self.missing_fields),
            "derivation_allowed": self.derivation_allowed,
            "operation_counts": dict(self.operation_counts),
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class LineageRef:
    source_run_id: str
    batch_id: str
    lineage_checksum: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LineageRef":
        return cls(
            source_run_id=str(value.get("source_run_id") or ""),
            batch_id=str(value.get("batch_id") or ""),
            lineage_checksum=str(value.get("lineage_checksum") or ""),
        )


@dataclass(frozen=True, slots=True)
class RawPriceContract:
    view_id: str = CR017_VIEW_PRICES_RAW
    required_fields: tuple[str, ...] = CR017_PRICES_RAW_REQUIRED_FIELDS
    source_of_truth: bool = True
    overwrite_allowed: bool = False


@dataclass(frozen=True, slots=True)
class AdjFactorContract:
    view_id: str = CR017_VIEW_ADJ_FACTOR
    required_fields: tuple[str, ...] = CR017_ADJ_FACTOR_REQUIRED_FIELDS
    source_of_truth: bool = True
    direction_required: bool = True


def build_required_field_sets() -> dict[str, tuple[str, ...]]:
    return {view_id: tuple(fields) for view_id, fields in CR017_REQUIRED_FIELD_SETS.items()}


def validate_source_lineage(metadata: Mapping[str, Any] | LineageRef) -> ContractCheckResult:
    payload = (
        {
            "source_run_id": metadata.source_run_id,
            "batch_id": metadata.batch_id,
            "lineage_checksum": metadata.lineage_checksum,
        }
        if isinstance(metadata, LineageRef)
        else dict(metadata)
    )
    missing = _missing_fields(payload, CR017_SOURCE_LINEAGE_REQUIRED_FIELDS)
    if missing:
        return _required_missing(CR017_MISSING_LINEAGE, missing)
    return ContractCheckResult(status=CONTRACT_STATUS_PASS, passed=True)


def validate_prices_raw_contract(rows_or_schema: Any) -> ContractCheckResult:
    rows, columns = _rows_and_columns(rows_or_schema)
    missing = _missing_columns(columns, CR017_PRICES_RAW_REQUIRED_FIELDS)
    if missing:
        return _required_missing("missing_prices_raw_required_field", missing)
    if not rows:
        return ContractCheckResult(status=CONTRACT_STATUS_PASS, passed=True)
    for row in rows:
        required_missing = _missing_fields(row, CR017_PRICES_RAW_REQUIRED_FIELDS)
        if required_missing:
            return _required_missing("missing_prices_raw_required_field", required_missing)
        lineage = validate_source_lineage(row)
        if not lineage.passed:
            return lineage
        invalid = _invalid_ohlc(row)
        if invalid:
            return _fail(
                CR017_INVALID_RAW_OHLC,
                invalid,
                details=({"view_id": CR017_VIEW_PRICES_RAW},),
            )
    return ContractCheckResult(status=CONTRACT_STATUS_PASS, passed=True)


def validate_adj_factor_contract(rows_or_schema: Any) -> ContractCheckResult:
    rows, columns = _rows_and_columns(rows_or_schema)
    missing = _missing_columns(columns, CR017_ADJ_FACTOR_REQUIRED_FIELDS)
    if missing:
        if "provider_factor_direction" in missing:
            return _required_missing(CR017_MISSING_FACTOR_DIRECTION, ("provider_factor_direction",))
        return _required_missing("missing_adj_factor_required_field", missing)
    if not rows:
        return ContractCheckResult(status=CONTRACT_STATUS_PASS, passed=True)
    for row in rows:
        required_missing = _missing_fields(row, CR017_ADJ_FACTOR_REQUIRED_FIELDS)
        if required_missing:
            if "provider_factor_direction" in required_missing:
                return _required_missing(CR017_MISSING_FACTOR_DIRECTION, ("provider_factor_direction",))
            return _required_missing("missing_adj_factor_required_field", required_missing)
        lineage = validate_source_lineage(row)
        if not lineage.passed:
            return lineage
        direction = str(row.get("provider_factor_direction") or "")
        if direction not in PROVIDER_FACTOR_DIRECTION_VALUES:
            return _fail(CR017_INVALID_FACTOR_DIRECTION, "provider_factor_direction")
        base_policy = str(row.get("factor_base_date_policy") or "")
        if base_policy not in FACTOR_BASE_DATE_POLICY_VALUES:
            return _fail("invalid_factor_base_date_policy", "factor_base_date_policy")
        factor = _to_float(row.get("adj_factor"))
        if factor is None or factor <= 0:
            return _fail(CR017_INVALID_ADJ_FACTOR, "adj_factor")
    return ContractCheckResult(status=CONTRACT_STATUS_PASS, passed=True)


def validate_derived_view_isolated(
    derived_view_id: str,
    *,
    raw_view_id: str = CR017_VIEW_PRICES_RAW,
) -> ContractCheckResult:
    if derived_view_id == raw_view_id:
        return _fail(CR017_DERIVED_OVERWRITES_RAW, "view_id")
    if derived_view_id not in CR017_DERIVED_VIEW_IDS:
        return _fail("invalid_derived_view_id", "view_id")
    return ContractCheckResult(status=CONTRACT_STATUS_PASS, passed=True)


def _rows_and_columns(value: Any) -> tuple[list[Mapping[str, Any]], tuple[str, ...]]:
    if isinstance(value, Mapping):
        if "columns" in value:
            return [], tuple(str(item) for item in value.get("columns") or ())
        return [value], tuple(str(item) for item in value.keys())
    if hasattr(value, "columns") and hasattr(value, "to_dict"):
        columns = tuple(str(item) for item in value.columns)
        records = value.to_dict("records")
        return [dict(item) for item in records], columns
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        rows = [dict(item) for item in value if isinstance(item, Mapping)]
        columns = tuple(str(item) for row in rows for item in row.keys())
        return rows, tuple(dict.fromkeys(columns))
    return [], ()


def _missing_columns(columns: tuple[str, ...], required: tuple[str, ...]) -> tuple[str, ...]:
    available = set(columns)
    return tuple(field for field in required if field not in available)


def _missing_fields(row: Mapping[str, Any], required: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(field for field in required if _is_missing(row.get(field)))


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


def _invalid_ohlc(row: Mapping[str, Any]) -> str:
    prices = {field: _to_float(row.get(field)) for field in ("open", "high", "low", "close")}
    for field, value in prices.items():
        if value is None or value <= 0:
            return field
    open_price = prices["open"]
    high_price = prices["high"]
    low_price = prices["low"]
    close_price = prices["close"]
    if high_price < max(open_price, low_price, close_price):
        return "high"
    if low_price > min(open_price, high_price, close_price):
        return "low"
    for field in ("volume", "amount"):
        value = _to_float(row.get(field))
        if value is None or value < 0:
            return field
    return ""


def _required_missing(reason_code: str, missing_fields: tuple[str, ...]) -> ContractCheckResult:
    return ContractCheckResult(
        status=CONTRACT_STATUS_REQUIRED_MISSING,
        passed=False,
        reason_code=reason_code,
        field=missing_fields[0] if missing_fields else "",
        missing_fields=missing_fields,
        derivation_allowed=False,
    )


def _fail(
    reason_code: str,
    field_name: str,
    *,
    details: tuple[dict[str, Any], ...] = (),
) -> ContractCheckResult:
    return ContractCheckResult(
        status=CONTRACT_STATUS_FAIL,
        passed=False,
        reason_code=reason_code,
        field=field_name,
        derivation_allowed=False,
        details=details,
    )


__all__ = [
    "CONTRACT_STATUS_FAIL",
    "CONTRACT_STATUS_PASS",
    "CONTRACT_STATUS_REQUIRED_MISSING",
    "FACTOR_BASE_DATE_POLICY_AS_OF",
    "FACTOR_BASE_DATE_POLICY_PROVIDER_BASE",
    "FACTOR_BASE_DATE_POLICY_VALUES",
    "PROVIDER_FACTOR_DIRECTION_INVERSE_RATIO",
    "PROVIDER_FACTOR_DIRECTION_QFQ_RATIO",
    "PROVIDER_FACTOR_DIRECTION_VALUES",
    "AdjFactorContract",
    "ContractCheckResult",
    "LineageRef",
    "RawPriceContract",
    "build_required_field_sets",
    "validate_adj_factor_contract",
    "validate_derived_view_isolated",
    "validate_prices_raw_contract",
    "validate_source_lineage",
    "zero_operation_counts",
]
