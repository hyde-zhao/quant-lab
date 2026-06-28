from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

import yaml


ALLOWED_ENDPOINTS = {"health", "capabilities", "query_positions_readonly"}
ALLOWED_EXECUTION_MODES = {
    "codex-runner-authorized",
    "user-manual-windows-side",
    "blocked-preflight",
}
ALLOWED_POSITION_BUCKETS = {"zero", "one_to_ten", "gt_ten", "unknown"}
REQUIRED_ABORT_CONDITIONS = {
    "missing_cp5_approval",
    "missing_runtime_authorization",
    "missing_or_ambiguous_env_ref",
    "endpoint_not_in_allowlist",
    "redaction_gate_unavailable",
    "forbidden_counter_non_zero",
    "raw_payload_detected",
}
REQUIRED_FORBIDDEN_COUNTERS = {
    "account_id_values",
    "security_code_values",
    "raw_quantity_values",
    "raw_cash_values",
    "order_fields",
    "fill_fields",
    "submit_cancel_calls",
    "buy_sell_calls",
    "nas_operations",
    "provider_lake_publish",
}
FORBIDDEN_TEXT_MARKERS = (
    ".env",
    "account_id=",
    "api_key",
    "apikey",
    "auth_token",
    "bearer ",
    "buy_order",
    "cancel_order",
    "catalog_publish",
    "credential",
    "fill_id",
    "lake_write",
    "nas://",
    "order_id",
    "password",
    "provider_fetch",
    "raw_cash",
    "raw_payload",
    "raw_positions",
    "raw_quantity",
    "secret",
    "security_code=",
    "sell_order",
    "submit_order",
    "token",
)
FORBIDDEN_KEY_MARKERS = (
    "api_key",
    "apikey",
    "auth_token",
    "credential",
    "password",
    "raw_payload",
    "raw_positions",
    "secret",
    "token",
)
ALLOWED_FORBIDDEN_COUNTER_KEY_MARKERS = {
    "account_id_values",
    "security_code_values",
    "raw_quantity_values",
    "raw_cash_values",
}
ALLOWED_STRUCTURAL_KEYS = {
    "raw_payload_allowed",
    "raw_payload_emitted",
    "secret_values_allowed_in_contract",
    "abort_conditions",
}
ALLOWED_STRUCTURAL_TEXT_VALUES = REQUIRED_ABORT_CONDITIONS | {
    "blocked-preflight",
}


@dataclass(frozen=True)
class CR099CheckResult:
    path: str
    mode: str
    passed: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "cr099-runner-real-readonly-smoke-check-v1",
            "path": self.path,
            "mode": self.mode,
            "passed": self.passed,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "not_runtime_authorization": True,
        }


def _load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("input must be a YAML/JSON mapping")
    return data


def _as_mapping(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    errors.append(f"{label} must be a mapping")
    return {}


def _as_string_set(value: Any, label: str, errors: list[str]) -> set[str]:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return set(value)
    errors.append(f"{label} must be a list of strings")
    return set()


def _walk(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    items = [(path, value)]
    if isinstance(value, dict):
        for key, nested in value.items():
            items.extend(_walk(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            items.extend(_walk(nested, f"{path}[{index}]"))
    return items


def _validate_forbidden_markers(payload: dict[str, Any], errors: list[str]) -> None:
    for path, value in _walk(payload):
        if path.startswith("$.forbidden_counters."):
            continue
        key = path.rsplit(".", 1)[-1].lower()
        if (
            key not in ALLOWED_FORBIDDEN_COUNTER_KEY_MARKERS
            and key not in ALLOWED_STRUCTURAL_KEYS
            and any(
                marker in key for marker in FORBIDDEN_KEY_MARKERS
            )
        ):
            errors.append(f"{path}: forbidden key marker")
        if isinstance(value, str):
            if value in ALLOWED_STRUCTURAL_TEXT_VALUES:
                continue
            lowered = value.lower()
            for marker in FORBIDDEN_TEXT_MARKERS:
                if marker in lowered:
                    errors.append(f"{path}: forbidden text marker {marker!r}")


def check_run_contract(path: Path) -> CR099CheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return CR099CheckResult(str(path), "contract", False, (f"{path}: file not found",))
    if path.name == ".env":
        return CR099CheckResult(str(path), "contract", False, (".env is forbidden input",))

    try:
        contract = _load_mapping(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return CR099CheckResult(str(path), "contract", False, (str(exc),))

    if contract.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if contract.get("cr_id") != "CR-099":
        errors.append("cr_id must be CR-099")
    for key in ("run_id", "authorization_ref", "authorized_by", "authorized_at"):
        if not contract.get(key):
            errors.append(f"{key} is required")

    gateway = _as_mapping(contract.get("gateway"), "gateway", errors)
    if not gateway.get("host"):
        errors.append("gateway.host is required")
    if not gateway.get("port"):
        errors.append("gateway.port is required")
    if gateway.get("scheme") not in {"http", "https"}:
        errors.append("gateway.scheme must be http or https")
    allowlist = _as_string_set(gateway.get("allowlist"), "gateway.allowlist", errors)
    if allowlist != ALLOWED_ENDPOINTS:
        errors.append("gateway.allowlist must exactly contain: " + ", ".join(sorted(ALLOWED_ENDPOINTS)))

    client_env = _as_mapping(contract.get("client_env"), "client_env", errors)
    if client_env.get("secret_values_allowed_in_contract") is not False:
        errors.append("client_env.secret_values_allowed_in_contract must be false")
    if client_env.get("handling") != "explicit-user-authorized-reference-only":
        errors.append("client_env.handling must be explicit-user-authorized-reference-only")
    if not client_env.get("env_ref"):
        errors.append("client_env.env_ref is required")

    evidence = _as_mapping(contract.get("evidence"), "evidence", errors)
    if evidence.get("raw_payload_allowed") is not False:
        errors.append("evidence.raw_payload_allowed must be false")
    output_dir = str(evidence.get("output_dir", ""))
    if not output_dir:
        errors.append("evidence.output_dir is required")
    elif ".quant-lab/evidence/qmt/cr099/redacted/" not in output_dir:
        warnings.append("evidence.output_dir is outside the recommended CR099 redacted path")

    abort_conditions = _as_string_set(contract.get("abort_conditions"), "abort_conditions", errors)
    missing_abort = REQUIRED_ABORT_CONDITIONS - abort_conditions
    if missing_abort:
        errors.append("abort_conditions missing: " + ", ".join(sorted(missing_abort)))

    _validate_forbidden_markers(contract, errors)
    return CR099CheckResult(str(path), "contract", not errors, tuple(errors), tuple(warnings))


def check_redacted_evidence(path: Path) -> CR099CheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return CR099CheckResult(str(path), "evidence", False, (f"{path}: file not found",))
    if path.name == ".env":
        return CR099CheckResult(str(path), "evidence", False, (".env is forbidden input",))

    try:
        evidence = _load_mapping(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return CR099CheckResult(str(path), "evidence", False, (str(exc),))

    if evidence.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if evidence.get("cr_id") != "CR-099":
        errors.append("cr_id must be CR-099")
    for key in ("run_id", "authorization_ref", "generated_at"):
        if not evidence.get(key):
            errors.append(f"{key} is required")
    execution_mode = evidence.get("execution_mode")
    if execution_mode not in ALLOWED_EXECUTION_MODES:
        errors.append("execution_mode must be one of: " + ", ".join(sorted(ALLOWED_EXECUTION_MODES)))

    endpoints = _as_mapping(evidence.get("endpoints"), "endpoints", errors)
    extra_endpoints = set(endpoints) - ALLOWED_ENDPOINTS
    missing_endpoints = ALLOWED_ENDPOINTS - set(endpoints)
    if extra_endpoints:
        errors.append("endpoints contains forbidden values: " + ", ".join(sorted(extra_endpoints)))
    if missing_endpoints:
        errors.append("endpoints missing: " + ", ".join(sorted(missing_endpoints)))

    for endpoint in sorted(ALLOWED_ENDPOINTS & set(endpoints)):
        current = _as_mapping(endpoints.get(endpoint), f"endpoints.{endpoint}", errors)
        if current.get("attempted") is not True:
            errors.append(f"endpoints.{endpoint}.attempted must be true")
        if current.get("raw_payload_emitted") is not False:
            errors.append(f"endpoints.{endpoint}.raw_payload_emitted must be false")

    positions = _as_mapping(endpoints.get("query_positions_readonly"), "endpoints.query_positions_readonly", errors)
    if positions:
        if positions.get("position_count_bucket") not in ALLOWED_POSITION_BUCKETS:
            errors.append(
                "endpoints.query_positions_readonly.position_count_bucket must be one of: "
                + ", ".join(sorted(ALLOWED_POSITION_BUCKETS))
            )
        digest = str(positions.get("positions_digest", ""))
        if not digest:
            errors.append("endpoints.query_positions_readonly.positions_digest is required")
        elif not digest.startswith("sha256:"):
            errors.append("endpoints.query_positions_readonly.positions_digest must start with sha256:")
        if int(positions.get("items_redacted_count", 0) or 0) < 0:
            errors.append("endpoints.query_positions_readonly.items_redacted_count must be >= 0")

    counters = _as_mapping(evidence.get("forbidden_counters"), "forbidden_counters", errors)
    missing_counters = REQUIRED_FORBIDDEN_COUNTERS - set(counters)
    if missing_counters:
        errors.append("forbidden_counters missing: " + ", ".join(sorted(missing_counters)))
    for key in REQUIRED_FORBIDDEN_COUNTERS & set(counters):
        if counters.get(key) != 0:
            errors.append(f"forbidden_counters.{key} must be 0")

    _validate_forbidden_markers(evidence, errors)
    if execution_mode == "blocked-preflight":
        warnings.append("blocked-preflight evidence does not prove a successful runner smoke")
    return CR099CheckResult(str(path), "evidence", not errors, tuple(errors), tuple(warnings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check one explicitly provided CR099 run contract or redacted evidence file."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--contract", type=Path)
    group.add_argument("--evidence", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = check_run_contract(args.contract) if args.contract else check_redacted_evidence(args.evidence)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"CR099 {result.mode} check passed={result.passed}")
        for warning in result.warnings:
            print(f"warning: {warning}", file=sys.stderr)
        for error in result.errors:
            print(error, file=sys.stderr)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
