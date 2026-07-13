from __future__ import annotations

from pathlib import Path

from engine.walk_forward_oos_evidence import validate_walk_forward_oos_input
from tests.research.walk_forward_oos_test_support import evidence_input


def test_fixture_authorization_has_zero_forbidden_operations() -> None:
    value = evidence_input()
    assert validate_walk_forward_oos_input(value).passed
    assert set(value.authorization.operation_counts) >= {
        "credential_read",
        "real_lake_read",
        "provider_fetch",
        "runtime_call",
        "broker_access",
        "external_framework_run",
    }
    assert sum(value.authorization.operation_counts.values()) == 0


def test_producer_module_has_no_external_dereference_or_runtime_imports() -> None:
    source = Path("engine/walk_forward_oos_evidence.py").read_text(encoding="utf-8")
    forbidden_imports = (
        "import requests",
        "import httpx",
        "from pathlib import Path",
        "import os",
        "import socket",
        "import boto",
        "import tushare",
        "import xtquant",
    )
    assert not any(item in source for item in forbidden_imports)
    assert "open(" not in source
    assert "getenv(" not in source


def test_cr166_claim_ceiling_keeps_stage3_and_real_evidence_false() -> None:
    claims = {
        "stage2_complete": True,
        "stage2_to_stage3_bridge_enhancement": True,
        "stage3_started": False,
        "real_fold_oos_evidence_available": False,
        "runtime_authorized": False,
        "real_data_connected": False,
    }
    assert claims["stage2_complete"] is True
    assert claims["stage2_to_stage3_bridge_enhancement"] is True
    assert not any(claims[key] for key in ("stage3_started", "real_fold_oos_evidence_available", "runtime_authorized", "real_data_connected"))
