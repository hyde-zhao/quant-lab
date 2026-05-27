from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd

from engine.research_dataset import (
    GateResult,
    ResearchDataset,
    apply_adjustment_audit_gate,
    evaluate_adjustment_audit,
)
from market_data.catalog import CatalogEntry
from market_data.contracts import DATASET_ADJ_FACTOR, DATASET_PRICES
from market_data.readers import (
    AdjustmentAuditRequest,
    DATASET_CORPORATE_ACTIONS,
    ReaderResult,
    evaluate_corporate_action_availability,
    read_adjustment_audit_inputs,
)


TARGET_FILES = (
    Path("market_data/readers.py"),
    Path("engine/research_dataset.py"),
)


def test_read_adjustment_audit_inputs_missing_lake_root_is_typed_and_does_not_call_reader() -> None:
    calls: list[str] = []

    result = read_adjustment_audit_inputs(
        AdjustmentAuditRequest(lake_root=None, start_date="2026-01-02", end_date="2026-01-05"),
        reader=lambda dataset, *_args, **_kwargs: calls.append(dataset),
    )

    assert calls == []
    assert result.status == "required_missing"
    assert result.adjustment_audit_status == "required_missing"
    assert result.adj_factor_lineage["missing_reason"] == "lake_root_missing"
    assert result.remediation_spec["auto_execute"] is False
    assert result.remediation_spec["dry_run_default"] is True


def test_adjustment_audit_outputs_required_fields_and_complete_claims_when_inputs_available(tmp_path: Path) -> None:
    audit_reader = read_adjustment_audit_inputs(
        {
            "lake_root": tmp_path / "lake",
            "start_date": "2026-01-02",
            "end_date": "2026-01-05",
            "adjustment_policy": "qfq",
            "decision_time": "2026-01-06",
        },
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_ADJ_FACTOR: available_reader(DATASET_ADJ_FACTOR, adj_factor_frame()),
                DATASET_CORPORATE_ACTIONS: available_reader(DATASET_CORPORATE_ACTIONS, corporate_actions_frame()),
            }
        ),
    )
    dataset = base_dataset(prices_frame())

    evaluated = apply_adjustment_audit_gate(
        dataset,
        {"adjustment_policy": "qfq", "realism_mode": "production_strict"},
        audit_result=audit_reader,
    )

    for field in ("adjustment_policy", "adj_factor_lineage", "corporate_action_status", "adjustment_audit_status"):
        assert field in evaluated.metadata
        assert field in evaluated.metadata["adjustment_audit"]
    assert evaluated.metadata["adjustment_policy"] == "qfq"
    assert evaluated.metadata["corporate_action_status"] == "available"
    assert evaluated.metadata["adjustment_audit_status"] == "pass"
    assert evaluated.metadata["lineage_raw_checksum"] == "adj-factor-checksum"
    assert evaluated.metadata["mixed_adjustment_policy_count"] == 0
    assert {"adjusted_price_used", "adjustment_policy_consistent", "corporate_action_audited"} <= set(evaluated.allowed_claims)
    assert not evaluated.blocked_claims


def test_mixed_adjustment_policy_blocks_factor_calculation_and_is_auditable(tmp_path: Path) -> None:
    mixed_prices = prices_frame(policies=("qfq", "hfq"))
    audit_reader = read_adjustment_audit_inputs(
        {"lake_root": tmp_path / "lake", "adjustment_policy": "qfq"},
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, mixed_prices),
                DATASET_ADJ_FACTOR: available_reader(DATASET_ADJ_FACTOR, adj_factor_frame(policy="qfq")),
                DATASET_CORPORATE_ACTIONS: available_reader(DATASET_CORPORATE_ACTIONS, corporate_actions_frame()),
            }
        ),
    )

    evaluated = apply_adjustment_audit_gate(
        base_dataset(mixed_prices),
        {"adjustment_policy": "qfq", "realism_mode": "production_strict"},
        audit_result=audit_reader,
    )

    assert evaluated.status == "gate_failed"
    assert evaluated.gate_result.status == "fail"
    assert evaluated.metadata["adjustment_audit_status"] == "quality_failed"
    assert evaluated.metadata["mixed_adjustment_policy_count"] == 2
    assert evaluated.metadata["factor_calculation_entry_count"] == 0
    assert "adjustment_consistent_research" not in evaluated.allowed_claims
    assert any(item["reason"] == "adjustment_policy_mixed" for item in evaluated.blocked_claims)


def test_missing_corporate_actions_blocks_complete_audit_claims_but_keeps_conservative_claims(tmp_path: Path) -> None:
    audit_reader = read_adjustment_audit_inputs(
        {"lake_root": tmp_path / "lake", "adjustment_policy": "qfq"},
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_ADJ_FACTOR: available_reader(DATASET_ADJ_FACTOR, adj_factor_frame()),
                DATASET_CORPORATE_ACTIONS: ReaderResult(
                    status="required_missing",
                    issues=[{"code": "corporate_actions_source_unresolved", "dataset": DATASET_CORPORATE_ACTIONS}],
                    remediation_spec={"action": "confirm_corporate_actions_source", "auto_execute": False},
                ),
            }
        ),
    )

    evaluated = apply_adjustment_audit_gate(
        base_dataset(prices_frame()),
        {"adjustment_policy": "qfq", "realism_mode": "production_strict"},
        audit_result=audit_reader,
    )

    assert evaluated.status == "available_with_warnings"
    assert evaluated.gate_result.status == "warn"
    assert evaluated.metadata["corporate_action_status"] == "required_missing"
    assert evaluated.metadata["adjustment_audit_status"] == "required_missing"
    assert {"adjusted_price_used", "adjustment_policy_consistent"} <= set(evaluated.allowed_claims)
    complete_claims = {"corporate_action_audited", "auditable_adjustment_chain", "complete_corporate_action_audit"}
    assert complete_claims.isdisjoint(evaluated.allowed_claims)
    assert complete_claims <= {item["claim"] for item in evaluated.blocked_claims}


def test_corporate_actions_without_explicit_available_at_are_required_missing() -> None:
    result = evaluate_corporate_action_availability(
        available_reader(
            DATASET_CORPORATE_ACTIONS,
            corporate_actions_frame().drop(columns=["available_at"]),
        )
    )

    assert result["corporate_action_status"] == "required_missing"
    assert result["issues"][0]["code"] == "corporate_actions_required_fields_missing"


def test_s04_adjustment_metadata_survives_s05_gate() -> None:
    dataset = base_dataset(
        prices_frame(),
        metadata={
            "adjustment": {"adjustment_status": "available", "policies_seen": ["qfq"]},
            "allowed_claims": ["framework_validation"],
        },
        gate_checks=[{"name": "adjustment_gate", "status": "pass"}],
    )
    audit = evaluate_adjustment_audit(
        dataset,
        {"adjustment_policy": "qfq", "realism_mode": "production_strict"},
        audit_result={
            "status": "required_missing",
            "adjustment_policy": "qfq",
            "adj_factor_lineage": {
                "status": "available",
                "source_dataset": DATASET_ADJ_FACTOR,
                "source_run_id": "adj-run",
                "lineage_raw_checksum": "adj-factor-checksum",
            },
            "corporate_action_status": "required_missing",
            "adjustment_audit_status": "required_missing",
            "issues": [{"code": "corporate_actions_source_unresolved", "dataset": DATASET_CORPORATE_ACTIONS}],
        },
    )
    evaluated = apply_adjustment_audit_gate(dataset, {"adjustment_policy": "qfq"}, audit_result=audit)

    assert evaluated.metadata["adjustment"] == {"adjustment_status": "available", "policies_seen": ["qfq"]}
    assert evaluated.metadata["adjustment_audit"]["adj_factor_lineage"]["source_run_id"] == "adj-run"
    assert {"adjustment_gate", "adjustment_audit_gate"} <= {check["name"] for check in evaluated.gate_result.checks}


def test_s05_forbidden_boundaries_are_static_and_no_secret_leakage(monkeypatch) -> None:
    fake_secret = "CR011_S05_FAKE_SECRET_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("CR011_S05_FAKE_SECRET", fake_secret)
    forbidden_modules = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
    }
    for path in TARGET_FILES:
        imports = imported_modules(path)
        assert not any(module == forbidden or module.startswith(forbidden + ".") for module in imports for forbidden in forbidden_modules)
        source = path.read_text(encoding="utf-8")
        assert "reports/experiment_17_21/factor_strategy_report.md" not in source
        assert "TUSHARE_TOKEN" not in source
        assert ".env" not in source

    evaluated = apply_adjustment_audit_gate(
        base_dataset(prices_frame()),
        {"adjustment_policy": "qfq"},
        audit_result={
            "status": "required_missing",
            "adjustment_policy": "qfq",
            "adj_factor_lineage": {
                "status": "available",
                "source_dataset": DATASET_ADJ_FACTOR,
                "source_run_id": "adj-run",
                "lineage_raw_checksum": "adj-factor-checksum",
            },
            "corporate_action_status": "required_missing",
            "adjustment_audit_status": "required_missing",
            "issues": [{"code": "corporate_actions_source_unresolved", "dataset": DATASET_CORPORATE_ACTIONS}],
        },
    )
    combined = json.dumps([evaluated.metadata, [issue.to_dict() for issue in evaluated.issues]], ensure_ascii=False, default=str)
    assert fake_secret not in combined
    assert evaluated.metadata["network_calls"] == 0
    assert evaluated.metadata["lake_writes"] == 0
    assert evaluated.metadata["credential_reads"] == 0
    assert evaluated.metadata["legacy_data_operations"] == 0


def base_dataset(
    prices: pd.DataFrame,
    *,
    metadata: dict[str, Any] | None = None,
    gate_checks: list[dict[str, Any]] | None = None,
) -> ResearchDataset:
    values = {
        "adjustment_policy": "qfq",
        "known_limitations": [],
        "allowed_claims": ["framework_validation"],
        "blocked_claims": [],
    }
    values.update(metadata or {})
    return ResearchDataset(
        status="available",
        prices=prices,
        metadata=values,
        gate_result=GateResult(status="pass", checks=list(gate_checks or [])),
        allowed_claims=list(values.get("allowed_claims") or []),
        known_limitations=list(values.get("known_limitations") or []),
        blocked_claims=list(values.get("blocked_claims") or []),
    )


def prices_frame(*, policies: tuple[str, ...] = ("qfq", "qfq")) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, (trade_date, symbol) in enumerate((("2026-01-02", "AAA"), ("2026-01-05", "BBB"))):
        policy = policies[index % len(policies)]
        rows.append(
            {
                "trade_date": trade_date,
                "symbol": symbol,
                "close": 10.0 + index,
                "adjusted_close": 10.0 + index,
                "adj_factor": 1.0 + index * 0.01,
                "adjustment_policy": policy,
                "source_run_id": "prices-run",
                "source_interface": "prices.daily",
                "lineage_raw_checksum": "prices-checksum",
            }
        )
    return pd.DataFrame(rows)


def adj_factor_frame(*, policy: str = "qfq") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "AAA",
                "adj_factor": 1.01,
                "adjustment_policy": policy,
                "source_run_id": "adj-run",
                "source_interface": "prices.adj_factor",
                "lineage_raw_checksum": "adj-factor-checksum",
                "available_at": "2026-01-02",
            }
        ]
    )


def corporate_actions_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "event_date": "2026-01-02",
                "event_type": "split",
                "available_at": "2026-01-03",
                "payload": {"ratio": "10:1"},
                "source_run_id": "ca-run",
                "source_interface": "corporate_actions.fixture",
                "lineage_raw_checksum": "ca-checksum",
            }
        ]
    )


def available_reader(dataset: str, frame: pd.DataFrame) -> ReaderResult:
    return ReaderResult(
        status="available",
        frame=frame,
        catalog_entry=CatalogEntry(
            dataset=dataset,
            quality_status="pass",
            dataset_status="available",
            readiness_status="available",
            source="fixture",
            source_interface=f"{dataset}.fixture",
            latest_manifest_run_id=f"{dataset}-manifest",
            lineage_raw_checksum=f"{dataset}-checksum",
            available_at_rule="explicit_available_at",
        ),
    )


def make_reader(results: dict[str, ReaderResult]) -> Any:
    def reader(
        dataset: str,
        _lake_root: Path,
        filters: dict[str, Any] | None = None,
        **_kwargs: Any,
    ) -> ReaderResult:
        result = results[dataset]
        if result.frame is None or not filters:
            return result
        frame = result.frame.copy()
        if filters.get("symbols") is not None and "symbol" in frame.columns:
            frame = frame[frame["symbol"].astype(str).isin({str(item) for item in filters["symbols"]})]
        if filters.get("start_date") and "trade_date" in frame.columns:
            frame = frame[frame["trade_date"].astype(str) >= str(filters["start_date"])]
        if filters.get("end_date") and "trade_date" in frame.columns:
            frame = frame[frame["trade_date"].astype(str) <= str(filters["end_date"])]
        return ReaderResult(
            status=result.status,
            frame=frame.reset_index(drop=True),
            issues=list(result.issues),
            catalog_entry=result.catalog_entry,
            remediation_spec=dict(result.remediation_spec),
        )

    return reader


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules
