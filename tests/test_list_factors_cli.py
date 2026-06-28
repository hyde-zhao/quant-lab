from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "list_factors.py"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_list_factors_default_table_contains_core_columns() -> None:
    result = _run_cli()

    assert result.returncode == 0
    assert "factor_id" in result.stdout
    assert "status" in result.stdout
    assert "used_by" in result.stdout


def test_list_factors_json_output_is_parseable() -> None:
    result = _run_cli("--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert any(item["factor_id"] == "market_beta_252" for item in payload)


def test_list_factors_status_stage3_active_only_returns_stage3_factors() -> None:
    result = _run_cli("--format", "json", "--status", "stage3_active")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert {item["factor_id"] for item in payload} == {
        "momentum_20d",
        "reversal_5d",
        "volatility_20d",
        "liquidity_adv20",
        "value_pb_inverse",
    }


def test_list_factors_factor_id_returns_single_detail() -> None:
    result = _run_cli("--format", "json", "--factor-id", "momentum_20d")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["factor_id"] == "momentum_20d"
    assert payload["status"] == "stage3_active"
    assert "stage3_mature_multifactor" in payload["used_by"]


def test_list_factors_unknown_factor_id_returns_clear_error() -> None:
    result = _run_cli("--factor-id", "does_not_exist")

    assert result.returncode != 0
    assert "unknown factor_id: does_not_exist" in result.stderr


def test_list_factors_can_include_admitted_anomaly_candidates(tmp_path: Path) -> None:
    candidates_path = tmp_path / "anomaly_candidates.json"
    decisions_path = tmp_path / "anomaly_admission_decisions.json"
    candidates_path.write_text(
        json.dumps(
            [
                {
                    "anomaly_id": "auto_value_pb_inverse",
                    "name": "Auto PB Inverse Value",
                    "source_type": "financial_extension",
                    "expected_direction": "positive",
                    "input_fields": ["pb"],
                    "required_factor_ids": ["pb"],
                    "formula": "-pb",
                    "prior_logic_ref": "controlled-template:valuation:pb_inverse",
                }
            ]
        ),
        encoding="utf-8",
    )
    decisions_path.write_text(
        json.dumps(
            [
                {
                    "anomaly_id": "auto_value_pb_inverse",
                    "factor_id": "auto_value_pb_inverse",
                    "admission_status": "stage3_candidate",
                    "evidence_refs": ["artifact://unit/anomaly_research_report.json"],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = _run_cli(
        "--format",
        "json",
        "--factor-id",
        "auto_value_pb_inverse",
        "--anomaly-candidates",
        str(candidates_path),
        "--anomaly-decisions",
        str(decisions_path),
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["factor_id"] == "auto_value_pb_inverse"
    assert payload["family"] == "anomaly_discovery_candidate"
    assert "stage3_candidate" in payload["used_by"]
