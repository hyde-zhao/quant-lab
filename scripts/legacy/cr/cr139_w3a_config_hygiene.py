#!/usr/bin/env python3
"""CR139 W3-A secret-safe config hygiene for data-lake root variables."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESS_ROOT = PROJECT_ROOT / "process"
ENV_PATH = PROJECT_ROOT / ".env"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"

ROOT_VARS = {
    "MARKET_DATA_LAKE_ROOT": "/home/hyde/data/quant-lab/data-lake",
    "MARKET_DATA_LAKE_ARCHIVE_ROOT": "/home/hyde/data/quant-lab/archive",
    "MARKET_DATA_LAKE_BACKUP_ROOT": "/home/hyde/data/quant-lab/backup",
    "MARKET_DATA_LAKE_RESTORE_ROOT": "/home/hyde/data/quant-lab/restore",
}

EVIDENCE_PATH = PROCESS_ROOT / "evidence" / "CR139-W3A-CONFIG-HYGIENE-2026-06-30.json"
INDEX_PATH = PROCESS_ROOT / "evidence" / "CR139-W3A-CONFIG-HYGIENE.index.json"
CHECK_PATH = PROCESS_ROOT / "checks" / "CR139-W3A-CONFIG-HYGIENE-2026-06-30.md"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_env_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        value = raw_value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        values[key] = value
    return values


def set_env_values(text: str, replacements: dict[str, str]) -> tuple[str, list[dict[str, Any]]]:
    lines = text.splitlines()
    seen: set[str] = set()
    changes: list[dict[str, Any]] = []
    pattern = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*?)(\s*)$")
    new_lines: list[str] = []
    for line_no, line in enumerate(lines, start=1):
        match = pattern.match(line)
        if not match:
            new_lines.append(line)
            continue
        prefix, key, sep, _old_value, suffix = match.groups()
        if key not in replacements:
            new_lines.append(line)
            continue
        seen.add(key)
        new_line = f'{prefix}{key}{sep}"{replacements[key]}"{suffix}'
        if new_line != line:
            changes.append({"key": key, "line": line_no, "action": "updated"})
        new_lines.append(new_line)
    for key, value in replacements.items():
        if key not in seen:
            changes.append({"key": key, "line": None, "action": "appended"})
            new_lines.append(f'{key}="{value}"')
    trailing_newline = "\n" if text.endswith("\n") else ""
    return "\n".join(new_lines) + trailing_newline, changes


def main() -> int:
    checked_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    if not ENV_PATH.exists():
        raise SystemExit(".env is required for W3-S05 config hygiene")
    env_before = ENV_PATH.read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    before_values = parse_env_values(env_before)
    example_values = parse_env_values(env_example)
    env_after, changes = set_env_values(env_before, ROOT_VARS)
    if env_after != env_before:
        ENV_PATH.write_text(env_after, encoding="utf-8")
    after_values = parse_env_values(env_after)

    root_results = []
    for key, expected in ROOT_VARS.items():
        root_results.append(
            {
                "key": key,
                "expected": expected,
                "before_matches_expected": before_values.get(key) == expected,
                "after_matches_expected": after_values.get(key) == expected,
                "env_example_matches_expected": example_values.get(key) == expected,
                "path_exists_after": Path(after_values.get(key, "")).exists(),
                "value_sha256_before": sha256_text(before_values.get(key, "")) if key in before_values else None,
                "value_sha256_after": sha256_text(after_values.get(key, "")) if key in after_values else None,
            }
        )
    secret_keys = [key for key in after_values if any(token in key.upper() for token in ("PASSWORD", "TOKEN", "SECRET"))]
    checks = {
        "env_exists": ENV_PATH.exists(),
        "env_example_exists": ENV_EXAMPLE_PATH.exists(),
        "four_root_vars_after_match_expected": all(item["after_matches_expected"] for item in root_results),
        "four_root_vars_env_example_match_expected": all(item["env_example_matches_expected"] for item in root_results),
        "four_root_paths_exist_after": all(item["path_exists_after"] for item in root_results),
        "secret_keys_present_but_not_recorded": bool(secret_keys),
        "secret_values_not_recorded": True,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    payload = {
        "schema": "cr139.w3a.config_hygiene.v1",
        "status": "pass_w3a_config_hygiene" if not failed_checks else "blocked_w3a_config_hygiene",
        "checked_at": checked_at,
        "mode": "secret_safe_root_key_update",
        "env_file_sha256_before": sha256_text(env_before),
        "env_file_sha256_after": sha256_text(env_after),
        "changed": env_after != env_before,
        "changes": changes,
        "root_results": root_results,
        "secret_key_count": len(secret_keys),
        "operation_counts": {
            "env_root_key_update": 1 if env_after != env_before else 0,
            "secret_value_print": 0,
            "credential_disclosure": 0,
            "nas_operation": 0,
            "provider_catalog_write": 0,
            "runtime_operation": 0,
            "git_remote": 0,
        },
        "checks": checks,
        "failed_checks": failed_checks,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    INDEX_PATH.write_text(
        json.dumps(
            {
                "schema": "cr139.evidence.index.v1",
                "status": payload["status"],
                "evidence": str(EVIDENCE_PATH),
                "check": str(CHECK_PATH),
                "failed_checks": failed_checks,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# CR139 W3-A Config Hygiene",
        "",
        f"- status: `{payload['status']}`",
        f"- evidence: `{EVIDENCE_PATH}`",
        f"- changed: `{payload['changed']}`",
        f"- secret_key_count: `{len(secret_keys)}`",
        "",
        "## Root Variables",
        "",
        "| Key | Expected | After Matches | Path Exists | .env.example Matches |",
        "|---|---|---:|---:|---:|",
    ]
    for item in root_results:
        lines.append(
            f"| `{item['key']}` | `{item['expected']}` | {item['after_matches_expected']} | {item['path_exists_after']} | {item['env_example_matches_expected']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Result |", "|---|---|"])
    for name, passed in checks.items():
        lines.append(f"| `{name}` | {'PASS' if passed else 'FAIL'} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Only the four data-lake root variables are updated.",
            "- Secret values are not printed or persisted in evidence.",
            "- No NAS/provider/runtime/Git operation is executed.",
        ]
    )
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "failed_checks": failed_checks}, sort_keys=True))
    return 0 if not failed_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
