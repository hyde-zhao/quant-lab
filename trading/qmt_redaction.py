"""CR019-S05 的 QMT 日志脱敏离线合同。

本模块只处理传入的文本或 mapping，不读取文件、环境变量或凭据，
不写日志、不启动服务、不访问外部系统。
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping, Sequence


REDACTED_VALUE = "[REDACTED]"
REDACTION_BLOCKED_VALUE = "[REDACTION_BLOCKED]"
CR020_QMT_REDACTION_SCHEMA_VERSION = "cr020-s04-redaction-gate-v1"

SENSITIVE_FIELD_CATEGORIES: dict[str, tuple[str, ...]] = {
    "secret": ("secret", "client_secret", "secret_ref", "hmac_secret", "private_key"),
    "credential": ("credential", "credential_ref", "credential_path"),
    "signature": ("signature", "hmac_signature"),
    "pairing_code": ("pairing_code", "pair_code", "one_time_code", "code"),
    "token": ("token", "access_token", "refresh_token", "auth_token"),
    "account": ("account", "account_id", "account_no", "broker_account"),
    "session": ("session", "session_id"),
    "cookie": ("cookie", "cookies"),
    "trade_password": ("trade_password", "trade_pwd", "password", "login_password"),
    "dotenv": (".env", "dotenv", "env_file"),
    "private_path": ("private_path", "home_path", "credential_path"),
}

_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private_path",
        re.compile(r"(?:[A-Za-z]:\\Users\\[^\s,;]+|/Users/[^\s,;]+|/home/[^\s,;]+)"),
    ),
    ("dotenv", re.compile(r"(?:^|[\s=:])\.env(?:[\s,;:]|$)", re.IGNORECASE)),
    (
        "trade_password",
        re.compile(
            r"\b(?:trade_password|trade_pwd|password|login_password)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
    ),
    (
        "secret",
        re.compile(
            r"\b(?:secret|client_secret|hmac_secret|private_key)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
    ),
    (
        "credential",
        re.compile(r"\b(?:credential|credential_ref|credential_path)\s*[:=]\s*[^\s,;]+", re.IGNORECASE),
    ),
    (
        "signature",
        re.compile(r"\b(?:signature|hmac_signature)\s*[:=]\s*[^\s,;]+", re.IGNORECASE),
    ),
    ("pairing_code", re.compile(r"\b(?:pairing_code|pair_code|one_time_code)\s*[:=]\s*[^\s,;]+", re.IGNORECASE)),
    ("token", re.compile(r"\b(?:token|access_token|refresh_token|auth_token)\s*[:=]\s*[^\s,;]+", re.IGNORECASE)),
    ("session", re.compile(r"\b(?:session|session_id)\s*[:=]\s*[^\s,;]+", re.IGNORECASE)),
    ("cookie", re.compile(r"\b(?:cookie|cookies)\s*[:=]\s*[^\s,;]+", re.IGNORECASE)),
    ("account", re.compile(r"\b(?:account|account_id|account_no)\s*[:=]\s*[0-9A-Za-z_-]+", re.IGNORECASE)),
    ("account", re.compile(r"\b[0-9]{10,18}\b")),
)


@dataclass(frozen=True, slots=True)
class RedactionReport:
    """脱敏结果摘要；不包含敏感原文。"""

    leak_count: int
    redaction_status: str
    matched_categories: tuple[str, ...] = ()
    replacement_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "leak_count": self.leak_count,
            "redaction_status": self.redaction_status,
            "matched_categories": list(self.matched_categories),
            "replacement_count": self.replacement_count,
        }


@dataclass(frozen=True, slots=True)
class QmtRedactionDecision:
    """CR020 响应 / 错误 / diagnostics 脱敏 gate。"""

    accepted: bool
    redaction_status: str
    redacted_payload: object
    leak_count: int
    matched_categories: tuple[str, ...] = ()
    replacement_count: int = 0
    blocked_reason: str = ""
    payload_kind: str = ""
    raw_fallback_allowed: bool = False
    schema_version: str = CR020_QMT_REDACTION_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return not self.accepted

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "accepted": self.accepted,
            "blocked": self.blocked,
            "redaction_status": self.redaction_status,
            "blocked_reason": self.blocked_reason,
            "payload_kind": self.payload_kind,
            "redacted_payload": self.redacted_payload,
            "leak_count": self.leak_count,
            "matched_categories": list(self.matched_categories),
            "replacement_count": self.replacement_count,
            "raw_fallback_allowed": self.raw_fallback_allowed,
        }


def redact_qmt_text(text: str) -> tuple[str, RedactionReport]:
    """脱敏文本日志，返回脱敏后文本与泄露扫描报告。"""

    redacted, categories, replacement_count = _redact_text(str(text))
    leak_report = scan_for_qmt_sensitive_leaks(redacted)
    report = RedactionReport(
        leak_count=leak_report.leak_count,
        redaction_status="pass" if leak_report.leak_count == 0 else "failed",
        matched_categories=tuple(sorted(set(categories))),
        replacement_count=replacement_count,
    )
    return redacted, report


def redact_qmt_mapping(mapping: Mapping[str, object]) -> tuple[dict[str, object], RedactionReport]:
    """脱敏结构化日志 mapping；敏感 key 的 value 统一替换。"""

    redacted, categories, replacement_count = _redact_mapping(mapping)
    leak_report = scan_for_qmt_sensitive_leaks(redacted)
    report = RedactionReport(
        leak_count=leak_report.leak_count,
        redaction_status="pass" if leak_report.leak_count == 0 else "failed",
        matched_categories=tuple(sorted(set(categories))),
        replacement_count=replacement_count,
    )
    return redacted, report


def scan_for_qmt_sensitive_leaks(payload: object) -> RedactionReport:
    """扫描 payload 中仍然可见的敏感值。"""

    categories: list[str] = []
    leak_count = _scan_payload(payload, categories)
    return RedactionReport(
        leak_count=leak_count,
        redaction_status="pass" if leak_count == 0 else "failed",
        matched_categories=tuple(sorted(set(categories))),
        replacement_count=0,
    )


def redact_qmt_response_payload(payload: object, policy: object | None = None) -> QmtRedactionDecision:
    """脱敏 gateway response；失败时阻断且不返回 raw fallback。"""

    return _redact_payload_decision(payload, payload_kind="response", policy=policy)


def redact_qmt_error_payload(payload: object, policy: object | None = None) -> QmtRedactionDecision:
    """脱敏错误 payload；错误详情不得携带 secret/session/account 原文。"""

    return _redact_payload_decision(payload, payload_kind="error", policy=policy)


def redact_qmt_diagnostics_payload(
    payload: object,
    policy: object | None = None,
) -> QmtRedactionDecision:
    """脱敏 diagnostics / audit payload；禁止 raw fallback。"""

    return _redact_payload_decision(payload, payload_kind="diagnostics", policy=policy)


def scan_qmt_auth_redaction_leaks(payload: object) -> QmtRedactionDecision:
    """以 redaction decision 形态暴露泄露扫描结果。"""

    try:
        report = scan_for_qmt_sensitive_leaks(payload)
    except Exception:
        return _blocked_redaction_decision(
            payload_kind="scan",
            blocked_reason="redaction_scan_failed",
        )
    if report.leak_count:
        return _blocked_redaction_decision(
            payload_kind="scan",
            blocked_reason="redaction_failed",
            leak_count=report.leak_count,
            matched_categories=report.matched_categories,
        )
    return QmtRedactionDecision(
        accepted=True,
        redaction_status="pass",
        redacted_payload=payload,
        leak_count=0,
        matched_categories=report.matched_categories,
        payload_kind="scan",
        raw_fallback_allowed=False,
    )


def _redact_mapping(mapping: Mapping[str, object]) -> tuple[dict[str, object], list[str], int]:
    result: dict[str, object] = {}
    categories: list[str] = []
    replacement_count = 0
    for key, value in mapping.items():
        category = _category_for_key(str(key))
        if category is not None:
            result[str(key)] = REDACTED_VALUE
            categories.append(category)
            replacement_count += 1
            continue
        redacted_value, nested_categories, nested_count = _redact_value(value)
        result[str(key)] = redacted_value
        categories.extend(nested_categories)
        replacement_count += nested_count
    return result, categories, replacement_count


def _redact_payload_decision(
    payload: object,
    *,
    payload_kind: str,
    policy: object | None,
) -> QmtRedactionDecision:
    missing_policy_fields = _missing_policy_fields(policy)
    if missing_policy_fields:
        return _blocked_redaction_decision(
            payload_kind=payload_kind,
            blocked_reason="redaction_policy_incomplete",
            matched_categories=missing_policy_fields,
        )

    try:
        redacted_payload, report = _redact_payload(payload)
    except Exception:
        return _blocked_redaction_decision(
            payload_kind=payload_kind,
            blocked_reason="redaction_failed",
        )
    if report.leak_count:
        return _blocked_redaction_decision(
            payload_kind=payload_kind,
            blocked_reason="redaction_failed",
            leak_count=report.leak_count,
            matched_categories=report.matched_categories,
        )
    return QmtRedactionDecision(
        accepted=True,
        redaction_status="pass",
        redacted_payload=redacted_payload,
        leak_count=0,
        matched_categories=report.matched_categories,
        replacement_count=report.replacement_count,
        payload_kind=payload_kind,
        raw_fallback_allowed=False,
    )


def _redact_payload(payload: object) -> tuple[object, RedactionReport]:
    if isinstance(payload, Mapping):
        return redact_qmt_mapping(payload)
    if isinstance(payload, str):
        return redact_qmt_text(payload)
    if isinstance(payload, Sequence) and not isinstance(payload, (bytes, bytearray, str)):
        redacted_items: list[object] = []
        categories: list[str] = []
        replacement_count = 0
        for item in payload:
            redacted_item, report = _redact_payload(item)
            redacted_items.append(redacted_item)
            categories.extend(report.matched_categories)
            replacement_count += report.replacement_count
        scan_report = scan_for_qmt_sensitive_leaks(redacted_items)
        return redacted_items, RedactionReport(
            leak_count=scan_report.leak_count,
            redaction_status="pass" if scan_report.leak_count == 0 else "failed",
            matched_categories=tuple(sorted(set(categories + list(scan_report.matched_categories)))),
            replacement_count=replacement_count,
        )
    scan_report = scan_for_qmt_sensitive_leaks(payload)
    return payload, RedactionReport(
        leak_count=scan_report.leak_count,
        redaction_status="pass" if scan_report.leak_count == 0 else "failed",
        matched_categories=scan_report.matched_categories,
        replacement_count=0,
    )


def _blocked_redaction_decision(
    *,
    payload_kind: str,
    blocked_reason: str,
    leak_count: int = 0,
    matched_categories: Sequence[str] = (),
) -> QmtRedactionDecision:
    return QmtRedactionDecision(
        accepted=False,
        redaction_status="failed",
        redacted_payload={
            "status": "blocked",
            "blocked_reason": blocked_reason,
            "payload": REDACTION_BLOCKED_VALUE,
        },
        leak_count=int(leak_count),
        matched_categories=tuple(sorted(set(str(item) for item in matched_categories))),
        blocked_reason=blocked_reason,
        payload_kind=payload_kind,
        raw_fallback_allowed=False,
    )


def _missing_policy_fields(policy: object | None) -> tuple[str, ...]:
    if policy is None:
        return ()
    missing = getattr(policy, "missing_fields", ())
    if missing:
        return tuple(str(item) for item in missing)
    if isinstance(policy, Mapping):
        required = _as_text_tuple(policy.get("required_fields", ()))
        redacted = {item.lower() for item in _as_text_tuple(policy.get("redacted_fields", ()))}
        return tuple(item for item in required if item.lower() not in redacted)
    return ()


def _redact_value(value: object) -> tuple[object, list[str], int]:
    if isinstance(value, Mapping):
        return _redact_mapping(value)
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        categories: list[str] = []
        replacement_count = 0
        items: list[object] = []
        for item in value:
            redacted, item_categories, item_count = _redact_value(item)
            items.append(redacted)
            categories.extend(item_categories)
            replacement_count += item_count
        return items, categories, replacement_count
    return value, [], 0


def _redact_text(text: str) -> tuple[str, list[str], int]:
    current = text
    categories: list[str] = []
    replacement_count = 0
    for category, pattern in _TEXT_PATTERNS:
        current, count = pattern.subn(REDACTED_VALUE, current)
        if count:
            categories.append(category)
            replacement_count += count
    return current, categories, replacement_count


def _scan_payload(payload: object, categories: list[str]) -> int:
    if isinstance(payload, Mapping):
        leak_count = 0
        for key, value in payload.items():
            category = _category_for_key(str(key))
            if category is not None:
                if _value_has_visible_sensitive_content(value):
                    categories.append(category)
                    leak_count += 1
                continue
            leak_count += _scan_payload(value, categories)
        return leak_count
    if isinstance(payload, str):
        return _scan_text(payload, categories)
    if isinstance(payload, Sequence) and not isinstance(payload, (bytes, bytearray, str)):
        return sum(_scan_payload(item, categories) for item in payload)
    return 0


def _scan_text(text: str, categories: list[str]) -> int:
    leak_count = 0
    for category, pattern in _TEXT_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            categories.append(category)
            leak_count += len(matches)
    return leak_count


def _value_has_visible_sensitive_content(value: object) -> bool:
    if value == REDACTED_VALUE or value in ("", None):
        return False
    if isinstance(value, str):
        nested_categories: list[str] = []
        if _scan_text(value, nested_categories) > 0:
            return True
        return bool(value.strip())
    return True


def _category_for_key(key: str) -> str | None:
    normalized = key.strip().lower()
    for category, aliases in SENSITIVE_FIELD_CATEGORIES.items():
        if normalized in aliases:
            return category
    return None


def _as_text_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return tuple(str(item) for item in value)
    if value is None:
        return ()
    return (str(value),)
