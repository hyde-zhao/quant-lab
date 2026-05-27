"""CR014 全 A universe lifecycle 与 code-change 合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping, Sequence

from .contracts import (
    CR014_CLAIM_FULL_A_SINCE_INCEPTION,
    CR014_CODE_CHANGE_CHAIN_CONFLICT,
    CR014_LIFECYCLE_REQUIRED_FIELDS,
    CR014_LIFECYCLE_STATUS_ACTIVE,
    CR014_LIFECYCLE_STATUS_DELISTED,
    CR014_LIFECYCLE_STATUS_NOT_YET_LISTED,
    CR014_LIFECYCLE_STATUS_SUSPENDED,
    CR014_LIST_STATUS_PRE_LISTED,
    CR014_LIST_STATUS_SUSPENDED,
    CR014_LIST_STATUS_UNKNOWN,
    CR014_REQUIRED_MISSING_CODE_CHANGE,
    CR014_REQUIRED_MISSING_LIFECYCLE,
    CR014_SECURITY_IDENTITY_FIELDS,
    CR014_UNKNOWN_LIFECYCLE_STATUS,
)


IDENTITY_INPUT_REQUIRED_FIELDS: tuple[str, ...] = ("security_id", "symbol")
CODE_CHANGE_REQUIRED_FIELDS: tuple[str, ...] = ("security_id", "effective_date")


@dataclass(frozen=True, slots=True)
class RequiredMissingItem:
    code: str
    field: str
    security_id: str | None = None
    symbol: str | None = None
    as_of_trade_date: str | None = None
    evidence_ref: str = "in_memory_fixture"
    unblock_condition: str = "provide_required_contract_field"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "field": self.field,
            "security_id": self.security_id,
            "symbol": self.symbol,
            "as_of_trade_date": self.as_of_trade_date,
            "evidence_ref": self.evidence_ref,
            "unblock_condition": self.unblock_condition,
        }
        if self.details:
            payload["details"] = dict(self.details)
        return payload


@dataclass(frozen=True, slots=True)
class BlockedClaim:
    claim: str
    reason_code: str
    field: str | None = None
    security_id: str | None = None
    symbol: str | None = None
    as_of_trade_date: str | None = None
    evidence_ref: str = "in_memory_fixture"
    unblock_condition: str = "resolve_required_missing_before_claim"

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "reason_code": self.reason_code,
            "field": self.field,
            "security_id": self.security_id,
            "symbol": self.symbol,
            "as_of_trade_date": self.as_of_trade_date,
            "evidence_ref": self.evidence_ref,
            "unblock_condition": self.unblock_condition,
        }


@dataclass(frozen=True, slots=True)
class ClaimBoundaryResult:
    required_missing: tuple[RequiredMissingItem, ...]
    blocked_claims: tuple[BlockedClaim, ...]
    allowed_claims: dict[str, bool]

    @property
    def full_a_allowed_claim_count(self) -> int:
        return int(bool(self.allowed_claims.get(CR014_CLAIM_FULL_A_SINCE_INCEPTION)))


@dataclass(frozen=True, slots=True)
class LifecycleValidationResult:
    passed: bool
    checked_records: int
    required_missing: tuple[RequiredMissingItem, ...]
    blocked_claims: tuple[BlockedClaim, ...]
    allowed_claims: dict[str, bool]

    @property
    def full_a_allowed_claim_count(self) -> int:
        return int(bool(self.allowed_claims.get(CR014_CLAIM_FULL_A_SINCE_INCEPTION)))


@dataclass(frozen=True, slots=True)
class CodeChangeValidationResult:
    passed: bool
    checked_mappings: int
    required_missing: tuple[RequiredMissingItem, ...]
    blocked_claims: tuple[BlockedClaim, ...]
    allowed_claims: dict[str, bool]

    @property
    def full_a_allowed_claim_count(self) -> int:
        return int(bool(self.allowed_claims.get(CR014_CLAIM_FULL_A_SINCE_INCEPTION)))


@dataclass(frozen=True, slots=True)
class UniverseMember:
    security_id: str
    symbol: str
    exchange: str
    list_date: str
    delist_date: str | None
    lifecycle_status: str
    valid_from: str
    valid_to: str | None
    predecessor_id: str | None = None
    successor_id: str | None = None


@dataclass(frozen=True, slots=True)
class UniverseDenominator:
    as_of_trade_date: str
    members: tuple[UniverseMember, ...]
    denominator: int
    trace_records: tuple[UniverseMember, ...]
    required_missing: tuple[RequiredMissingItem, ...]
    blocked_claims: tuple[BlockedClaim, ...]
    allowed_claims: dict[str, bool]

    @property
    def full_a_allowed_claim_count(self) -> int:
        return int(bool(self.allowed_claims.get(CR014_CLAIM_FULL_A_SINCE_INCEPTION)))


def _parse_iso_date(value: object, *, field: str, security_id: str | None = None) -> date:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be YYYY-MM-DD for {security_id or 'record'}")
    return date.fromisoformat(value)


def _value_missing(record: Mapping[str, Any], field_name: str) -> bool:
    if field_name not in record:
        return True
    value = record[field_name]
    if field_name == "delist_date":
        return value == ""
    if field_name == "code_change_mapping":
        return value == ""
    if value is None:
        return True
    return value == ""


def _field_missing_item(
    code: str,
    field_name: str,
    record: Mapping[str, Any],
    *,
    as_of_trade_date: str | None = None,
    unblock_condition: str = "provide_required_contract_field",
) -> RequiredMissingItem:
    return RequiredMissingItem(
        code=code,
        field=field_name,
        security_id=_optional_str(record.get("security_id")),
        symbol=_optional_str(record.get("symbol")),
        as_of_trade_date=as_of_trade_date,
        unblock_condition=unblock_condition,
    )


def _blocked_from_missing(item: RequiredMissingItem) -> BlockedClaim:
    return BlockedClaim(
        claim=CR014_CLAIM_FULL_A_SINCE_INCEPTION,
        reason_code=item.code,
        field=item.field,
        security_id=item.security_id,
        symbol=item.symbol,
        as_of_trade_date=item.as_of_trade_date,
        evidence_ref=item.evidence_ref,
        unblock_condition=item.unblock_condition,
    )


def _claim_boundary(
    required_missing: Sequence[RequiredMissingItem],
    blocked_claims: Sequence[BlockedClaim] = (),
) -> ClaimBoundaryResult:
    missing = tuple(required_missing)
    blocked = tuple(blocked_claims) or tuple(_blocked_from_missing(item) for item in missing)
    return ClaimBoundaryResult(
        required_missing=missing,
        blocked_claims=blocked,
        allowed_claims={CR014_CLAIM_FULL_A_SINCE_INCEPTION: not missing and not blocked},
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def validate_lifecycle_records(records: Sequence[Mapping[str, Any]]) -> LifecycleValidationResult:
    """校验 lifecycle 10 类必需字段和稳定证券身份字段。"""

    required_missing: list[RequiredMissingItem] = []
    if not records:
        required_missing.append(
            RequiredMissingItem(
                code=CR014_REQUIRED_MISSING_LIFECYCLE,
                field="records",
                unblock_condition="provide_lifecycle_records",
            )
        )

    for record in records:
        for field_name in (*IDENTITY_INPUT_REQUIRED_FIELDS, *CR014_LIFECYCLE_REQUIRED_FIELDS):
            if _value_missing(record, field_name):
                required_missing.append(
                    _field_missing_item(CR014_REQUIRED_MISSING_LIFECYCLE, field_name, record)
                )
        list_status = _optional_str(record.get("list_status"))
        if list_status == CR014_LIST_STATUS_UNKNOWN:
            required_missing.append(
                _field_missing_item(
                    CR014_UNKNOWN_LIFECYCLE_STATUS,
                    "list_status",
                    record,
                    unblock_condition="replace_unknown_lifecycle_status",
                )
            )
        for date_field in ("list_date", "effective_date"):
            if not _value_missing(record, date_field):
                try:
                    _parse_iso_date(record[date_field], field=date_field, security_id=_optional_str(record.get("security_id")))
                except ValueError:
                    required_missing.append(
                        _field_missing_item(
                            CR014_REQUIRED_MISSING_LIFECYCLE,
                            date_field,
                            record,
                            unblock_condition="provide_iso_date_contract_field",
                        )
                    )
        if "delist_date" in record and record.get("delist_date") not in (None, ""):
            try:
                _parse_iso_date(record["delist_date"], field="delist_date", security_id=_optional_str(record.get("security_id")))
            except ValueError:
                required_missing.append(
                    _field_missing_item(
                        CR014_REQUIRED_MISSING_LIFECYCLE,
                        "delist_date",
                        record,
                        unblock_condition="provide_iso_date_contract_field",
                    )
                )

    boundary = _claim_boundary(required_missing)
    return LifecycleValidationResult(
        passed=not boundary.required_missing,
        checked_records=len(records),
        required_missing=boundary.required_missing,
        blocked_claims=boundary.blocked_claims,
        allowed_claims=boundary.allowed_claims,
    )


def validate_code_change_chain(mappings: Sequence[Mapping[str, Any]]) -> CodeChangeValidationResult:
    """校验 code-change 映射同日唯一、身份稳定且无显式环路。"""

    required_missing: list[RequiredMissingItem] = []
    blocked_claims: list[BlockedClaim] = []
    seen_security_dates: set[tuple[str, str]] = set()
    symbol_edges: dict[str, str] = {}

    for mapping in mappings:
        for field_name in CODE_CHANGE_REQUIRED_FIELDS:
            if _value_missing(mapping, field_name):
                required_missing.append(
                    _field_missing_item(
                        CR014_REQUIRED_MISSING_CODE_CHANGE,
                        field_name,
                        mapping,
                        unblock_condition="provide_code_change_mapping_field",
                    )
                )
        security_id = _optional_str(mapping.get("security_id"))
        effective_date = _optional_str(mapping.get("effective_date"))
        if security_id and effective_date:
            key = (security_id, effective_date)
            if key in seen_security_dates:
                item = RequiredMissingItem(
                    code=CR014_CODE_CHANGE_CHAIN_CONFLICT,
                    field="effective_date",
                    security_id=security_id,
                    as_of_trade_date=effective_date,
                    unblock_condition="deduplicate_same_day_code_change_mapping",
                )
                required_missing.append(item)
                blocked_claims.append(_blocked_from_missing(item))
            seen_security_dates.add(key)
        predecessor_id = _optional_str(mapping.get("predecessor_id"))
        successor_id = _optional_str(mapping.get("successor_id"))
        if predecessor_id and security_id and predecessor_id != security_id:
            item = RequiredMissingItem(
                code=CR014_CODE_CHANGE_CHAIN_CONFLICT,
                field="predecessor_id",
                security_id=security_id,
                as_of_trade_date=effective_date,
                unblock_condition="keep_stable_security_id_across_code_change",
            )
            required_missing.append(item)
            blocked_claims.append(_blocked_from_missing(item))
        if successor_id and security_id and successor_id != security_id:
            item = RequiredMissingItem(
                code=CR014_CODE_CHANGE_CHAIN_CONFLICT,
                field="successor_id",
                security_id=security_id,
                as_of_trade_date=effective_date,
                unblock_condition="keep_stable_security_id_across_code_change",
            )
            required_missing.append(item)
            blocked_claims.append(_blocked_from_missing(item))
        old_symbol = _optional_str(mapping.get("old_symbol"))
        new_symbol = _optional_str(mapping.get("new_symbol"))
        if old_symbol and new_symbol:
            existing = symbol_edges.get(old_symbol)
            if existing and existing != new_symbol:
                item = RequiredMissingItem(
                    code=CR014_CODE_CHANGE_CHAIN_CONFLICT,
                    field="old_symbol",
                    security_id=security_id,
                    symbol=old_symbol,
                    as_of_trade_date=effective_date,
                    unblock_condition="deduplicate_code_change_successor",
                )
                required_missing.append(item)
                blocked_claims.append(_blocked_from_missing(item))
            symbol_edges[old_symbol] = new_symbol

    for start in tuple(symbol_edges):
        visited: set[str] = set()
        current: str | None = start
        while current in symbol_edges:
            if current in visited:
                item = RequiredMissingItem(
                    code=CR014_CODE_CHANGE_CHAIN_CONFLICT,
                    field="code_change_mapping",
                    symbol=start,
                    unblock_condition="break_code_change_cycle",
                )
                required_missing.append(item)
                blocked_claims.append(_blocked_from_missing(item))
                break
            visited.add(current)
            current = symbol_edges[current]

    boundary = _claim_boundary(required_missing, blocked_claims)
    return CodeChangeValidationResult(
        passed=not boundary.required_missing,
        checked_mappings=len(mappings),
        required_missing=boundary.required_missing,
        blocked_claims=boundary.blocked_claims,
        allowed_claims=boundary.allowed_claims,
    )


def build_universe_denominator(
    records: Sequence[Mapping[str, Any]],
    as_of_trade_date: str,
) -> UniverseDenominator:
    """按 as-of 日期生成全 A denominator，并保留退市后追溯状态。"""

    validation = validate_lifecycle_records(records)
    if not validation.passed:
        return UniverseDenominator(
            as_of_trade_date=as_of_trade_date,
            members=(),
            denominator=0,
            trace_records=(),
            required_missing=validation.required_missing,
            blocked_claims=validation.blocked_claims,
            allowed_claims=validation.allowed_claims,
        )

    as_of_date = _parse_iso_date(as_of_trade_date, field="as_of_trade_date")
    members: list[UniverseMember] = []
    trace_records: list[UniverseMember] = []

    for record in records:
        security_id = str(record["security_id"])
        symbol = str(record["symbol"])
        exchange = str(record["exchange"])
        list_date = _parse_iso_date(record["list_date"], field="list_date", security_id=security_id)
        delist_value = record.get("delist_date")
        delist_date = (
            _parse_iso_date(delist_value, field="delist_date", security_id=security_id)
            if delist_value not in (None, "")
            else None
        )
        if as_of_date < list_date:
            lifecycle_status = CR014_LIFECYCLE_STATUS_NOT_YET_LISTED
        elif delist_date is not None and as_of_date > delist_date:
            lifecycle_status = CR014_LIFECYCLE_STATUS_DELISTED
        elif record.get("list_status") == CR014_LIST_STATUS_SUSPENDED:
            lifecycle_status = CR014_LIFECYCLE_STATUS_SUSPENDED
        elif record.get("list_status") == CR014_LIST_STATUS_PRE_LISTED:
            lifecycle_status = CR014_LIFECYCLE_STATUS_NOT_YET_LISTED
        else:
            lifecycle_status = CR014_LIFECYCLE_STATUS_ACTIVE

        member = UniverseMember(
            security_id=security_id,
            symbol=symbol,
            exchange=exchange,
            list_date=record["list_date"],
            delist_date=_optional_str(delist_value),
            lifecycle_status=lifecycle_status,
            valid_from=str(record.get("valid_from") or record["list_date"]),
            valid_to=_optional_str(record.get("valid_to")) or _optional_str(delist_value),
            predecessor_id=_optional_str(record.get("predecessor_id")),
            successor_id=_optional_str(record.get("successor_id")),
        )
        trace_records.append(member)
        if lifecycle_status in {CR014_LIFECYCLE_STATUS_ACTIVE, CR014_LIFECYCLE_STATUS_SUSPENDED}:
            members.append(member)

    allowed = {CR014_CLAIM_FULL_A_SINCE_INCEPTION: True}
    return UniverseDenominator(
        as_of_trade_date=as_of_trade_date,
        members=tuple(members),
        denominator=len(members),
        trace_records=tuple(trace_records),
        required_missing=(),
        blocked_claims=(),
        allowed_claims=allowed,
    )


def build_full_a_blocked_claims(*results: object) -> ClaimBoundaryResult:
    """聚合 lifecycle、code-change、calendar 等结果，缺任一项时 full-A claim 为 0。"""

    required_missing: list[RequiredMissingItem] = []
    blocked_claims: list[BlockedClaim] = []
    for result in results:
        required_missing.extend(getattr(result, "required_missing", ()) or ())
        blocked_claims.extend(getattr(result, "blocked_claims", ()) or ())
    return _claim_boundary(required_missing, blocked_claims)


def lifecycle_contract_fields() -> dict[str, tuple[str, ...]]:
    return {
        "required_fields": CR014_LIFECYCLE_REQUIRED_FIELDS,
        "identity_fields": CR014_SECURITY_IDENTITY_FIELDS,
    }


__all__ = [
    "IDENTITY_INPUT_REQUIRED_FIELDS",
    "CODE_CHANGE_REQUIRED_FIELDS",
    "RequiredMissingItem",
    "BlockedClaim",
    "ClaimBoundaryResult",
    "LifecycleValidationResult",
    "CodeChangeValidationResult",
    "UniverseMember",
    "UniverseDenominator",
    "validate_lifecycle_records",
    "validate_code_change_chain",
    "build_universe_denominator",
    "build_full_a_blocked_claims",
    "lifecycle_contract_fields",
]
