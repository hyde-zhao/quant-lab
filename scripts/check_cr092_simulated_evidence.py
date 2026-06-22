from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

import yaml


ALLOWED_SCOPE = {"health", "capabilities", "query_positions_readonly"}
REQUIRED_COUNTERS = {
    "nas_access",
    "credential_read",
    "real_account_read",
    "submit_cancel",
    "simulation_live",
    "provider_lake_publish",
}
REQUIRED_STATUSES = {"PASS", "FAIL", "N/A"}
FORBIDDEN_TEXT_MARKERS = (
    ".env",
    "api_key",
    "apikey",
    "auth_token",
    "bearer ",
    "cancel_order",
    "catalog_publish",
    "credential",
    "lake_write",
    "live",
    "nas://",
    "password",
    "provider_fetch",
    "real_account",
    "secret",
    "submit_order",
    "token",
)
FORBIDDEN_KEY_MARKERS = (
    "api_key",
    "apikey",
    "auth_token",
    "credential",
    "password",
    "real_account",
    "secret",
    "token",
)


@dataclass(frozen=True)
class EvidenceCheckResult:
    evidence_path: str
    passed: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "cr092-simulated-account-evidence-check-v1",
            "evidence_path": self.evidence_path,
            "passed": self.passed,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "not_authorization": True,
        }


def _load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("evidence must be a YAML/JSON mapping")
    return data


def _walk(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    items = [(path, value)]
    if isinstance(value, dict):
        for key, nested in value.items():
            items.extend(_walk(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            items.extend(_walk(nested, f"{path}[{index}]"))
    return items


def _validate_forbidden_markers(evidence: dict[str, Any], errors: list[str]) -> None:
    for path, value in _walk(evidence):
        if path.startswith("$.forbidden_counters."):
            continue
        key = path.rsplit(".", 1)[-1].lower()
        if any(marker in key for marker in FORBIDDEN_KEY_MARKERS):
            errors.append(f"{path}: forbidden key marker")
        if isinstance(value, str):
            lowered = value.lower()
            for marker in FORBIDDEN_TEXT_MARKERS:
                if marker in lowered:
                    errors.append(f"{path}: forbidden text marker {marker!r}")


def check_evidence(path: Path) -> EvidenceCheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return EvidenceCheckResult(str(path), False, (f"{path}: evidence file not found",))
    if path.name == ".env":
        return EvidenceCheckResult(str(path), False, (".env is forbidden evidence input",))

    try:
        evidence = _load_mapping(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return EvidenceCheckResult(str(path), False, (str(exc),))

    if evidence.get("schema_version") != "cr092-simulated-account-evidence-v1":
        errors.append("schema_version must be cr092-simulated-account-evidence-v1")
    if evidence.get("change_id") != "CR-092":
        errors.append("change_id must be CR-092")
    if evidence.get("not_authorization") is not True:
        errors.append("not_authorization must be true")
    if evidence.get("runtime_authorization_status") not in {
        "not_authorized_by_template",
        "not_authorized",
    }:
        errors.append("runtime_authorization_status must remain not_authorized")
    if evidence.get("account_mode") != "simulated":
        errors.append("account_mode must be simulated")
    if not evidence.get("run_id"):
        errors.append("run_id is required")
    if not evidence.get("evidence_source"):
        errors.append("evidence_source is required")

    scope = evidence.get("scope")
    if not isinstance(scope, list) or not all(isinstance(item, str) for item in scope):
        errors.append("scope must be a list of strings")
    else:
        extra_scope = set(scope) - ALLOWED_SCOPE
        if extra_scope:
            errors.append("scope contains forbidden values: " + ", ".join(sorted(extra_scope)))

    for key in ("health_status", "capabilities_status", "query_positions_status", "redaction_status"):
        value = evidence.get(key)
        allowed = {"PASS", "FAIL"} if key == "redaction_status" else REQUIRED_STATUSES
        if value not in allowed:
            errors.append(f"{key} must be one of {sorted(allowed)}")

    counters = evidence.get("forbidden_counters")
    if not isinstance(counters, dict):
        errors.append("forbidden_counters must be a mapping")
    else:
        missing = REQUIRED_COUNTERS - set(counters)
        if missing:
            errors.append("forbidden_counters missing: " + ", ".join(sorted(missing)))
        for key in REQUIRED_COUNTERS & set(counters):
            if counters.get(key) != 0:
                errors.append(f"forbidden_counters.{key} must be 0")

    _validate_forbidden_markers(evidence, errors)

    if "simulated_account_summary" not in evidence:
        warnings.append("simulated_account_summary is recommended")

    return EvidenceCheckResult(str(path), not errors, tuple(errors), tuple(warnings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check one explicitly provided CR092 simulated-account evidence file."
    )
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = check_evidence(args.evidence)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"CR092 evidence check passed={result.passed}")
        for error in result.errors:
            print(error, file=sys.stderr)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
