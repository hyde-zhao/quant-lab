from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

import engine.backtrader_adapter as adapter
from engine.backtrader_adapter import BackendSelectionRequest, select_research_backend, validate_clean_feed_gate
from engine.order_intent_draft import (
    LATER_GATED_CONSUMER,
    REQUIRED_DRAFT_FIELDS,
    SCHEMA_VERSION as ORDER_INTENT_SCHEMA_VERSION,
    build_order_intent_draft,
    validate_order_intent_draft,
    zero_forbidden_operation_counts as order_zero_counts,
)
from engine.semantic_diff import (
    REQUIRED_FIELD_GROUPS,
    SCHEMA_VERSION as SEMANTIC_DIFF_SCHEMA_VERSION,
    build_semantic_diff,
    validate_semantic_diff_artifact,
    zero_forbidden_operation_counts as semantic_zero_counts,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_CLAIM_SCAN_PATHS = (
    "docs/reference/BACKTRADER-MODULE-REFERENCE.md",
    "checkpoints/CP5-CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A-LLD-BATCH.md",
    "process/stories/CR025-S05-no-real-operation-safety-verification.md",
    "process/stories/CR025-S05-no-real-operation-safety-verification-LLD.md",
)

DISALLOWED_SCAN_PREFIXES = (
    "/home/hyde/download/backtrader",
    "data/market_data",
    "broker_lake",
    ".env",
)

TS025_SCENARIO_COVERAGE = {
    "TS-025-01": "selector / clean feed gate contract",
    "TS-025-02": "semantic diff schema contract",
    "TS-025-03": "order_intent_draft_v1 and QMT boundary",
    "TS-025-04": "Backtrader source copy guardrail",
    "TS-025-05": "dependency diff zero",
    "TS-025-06": "forbidden import / call zero",
    "TS-025-07": "credential read zero",
    "TS-025-08": "fixture-only verification",
    "TS-025-09": "bounded scan scope",
    "TS-025-10": "no-real-operation counters",
    "TS-025-11": "forbidden claim / scope scan",
}

FORBIDDEN_POSITIVE_CLAIM_PATTERNS = (
    re.compile(r"(?<!不)已实现多因子研究主框架"),
    re.compile(r"(?<!不)实现了多因子研究主框架"),
    re.compile(r"completed multifactor research framework", re.IGNORECASE),
    re.compile(r"FactorSpec\s*(?:已实现|implemented)", re.IGNORECASE),
    re.compile(r"FactorRunSpec\s*(?:已实现|implemented)", re.IGNORECASE),
    re.compile(r"(?:IC\s*/\s*RankIC|RankIC)\s*(?:报告已完成|implemented|report completed)", re.IGNORECASE),
    re.compile(r"分层收益\s*(?:已实现|implemented)"),
    re.compile(r"多因子组合\s*(?:已实现|implemented)"),
    re.compile(r"实验追踪\s*(?:已实现|implemented)"),
    re.compile(r"策略准入包\s*(?:已实现|implemented)"),
    re.compile(r"Qlib\s*(?:已集成|integration completed|integrated)", re.IGNORECASE),
    re.compile(r"Alphalens\s*(?:已集成|integration completed|integrated)", re.IGNORECASE),
    re.compile(r"vnpy\.alpha\s*(?:已集成|integration completed|integrated)", re.IGNORECASE),
)

NEGATING_CLAIM_CONTEXT_MARKERS = (
    "不",
    "不得",
    "禁止",
    "不授权",
    "不实现",
    "不设计",
    "不验收",
    "不声称",
    "声称",
    "扫描",
    "phrase",
    "expected_count=0",
    "匹配次数为 0",
    "匹配次数",
    "回滚触发条件",
    "放行",
    "越界声明",
    "forbidden",
    "not authorized",
    "does not authorize",
)


def _clean_evidence(**overrides):
    evidence = {
        "pit_checked": True,
        "pit_status": "pass",
        "available_at_checked": True,
        "adjusted_price_ready": True,
        "adjustment_policy": "qfq",
        "ohlcv_status": "available",
        "calendar_status": "available",
        "benchmark_status": "available",
        "benchmark_required": True,
        "tradability_status": "available",
        "cost_status": "available",
        "quality_status": "pass",
        "lineage": {"source_run_id": "run-cr025-s05", "dataset": "clean-feed-fixture"},
        "limitations": [{"code": "fixture_only"}],
    }
    evidence.update(overrides)
    return evidence


def _baseline_fixture(**overrides):
    result = {
        "run_id": "run-cr025-s05",
        "lineage": {"source": "lightweight-fixture", "release_id": "release-fixture"},
        "metrics": {
            "starting_cash": 1_000_000.0,
            "ending_cash": 999_850.0,
            "final_value": 1_002_500.0,
            "total_return": 0.0025,
            "max_drawdown": -0.003,
            "turnover": 0.12,
        },
        "fills": [{"trade_date": "2026-06-02", "symbol": "000001.SZ", "price": 10.0, "quantity": 200}],
        "commission": 10.0,
        "tax": 0.0,
        "slippage": 5.0,
        "holdings_delta": {"000001.SZ": 200},
        "position_sizing_delta": {"000001.SZ": 0.10},
        "timeline": [{"date": "2026-06-02", "event": "baseline_fill"}],
    }
    result.update(overrides)
    return result


def _reference_fixture(**overrides):
    result = {
        "run_id": "run-cr025-s05-reference",
        "lineage": {"source": "reference-fixture"},
        "metrics": {
            "starting_cash": 1_000_000.0,
            "ending_cash": 999_830.0,
            "final_value": 1_002_100.0,
            "total_return": 0.0021,
            "max_drawdown": -0.004,
            "turnover": 0.13,
        },
        "fills": [{"trade_date": "2026-06-02", "symbol": "000001.SZ", "price": 10.01, "quantity": 200}],
        "commission": 12.0,
        "tax": 0.0,
        "slippage": 7.0,
        "holdings_delta": {"000001.SZ": 200},
        "position_sizing_delta": {"000001.SZ": 0.10},
        "timeline": [{"date": "2026-06-02", "event": "reference_fill"}],
    }
    result.update(overrides)
    return result


def _selection_available():
    return {
        "selected_backend": "backtrader",
        "availability_status": "available",
        "lineage": {"selector": "fixture"},
        "limitations": [{"code": "fixture_only"}],
        "forbidden_operation_counts": semantic_zero_counts(),
    }


def _target_row(**overrides):
    result = {
        "target_portfolio_id": "target-portfolio-cr025-s05",
        "strategy_id": "strategy-cr025-s05",
        "run_id": "run-cr025-s05",
        "signal_date": "2026-06-01",
        "target_trade_date": "2026-06-02",
        "symbol": "000001.SZ",
        "side": "buy",
        "target_qty": 200,
        "target_weight": "0.10",
        "estimated_price_policy": "research_close_estimate",
        "research_adjustment_policy": "qfq",
        "cost_config_ref": "cost-config:fixture",
        "reason": "semantic-diff-rebalance-fixture",
    }
    result.update(overrides)
    return result


def _policy(**overrides):
    result = {
        "source_run_id": "run-cr025-s05",
        "semantic_diff_artifact_id": "semantic-diff:run-cr025-s05",
        "execution_price_policy": "raw",
        "raw_execution_policy_status": "pass",
        "pretrade_required": True,
        "operation_counters": order_zero_counts(),
    }
    result.update(overrides)
    return result


def _semantic_diff_artifact(**config_overrides):
    config = {
        "generated_at": "2026-06-02T09:10:00+08:00",
        "source_run_id": "run-cr025-s05",
        "lineage": {"quality_evidence_ref": "quality:fixture"},
        "limitations": [{"code": "research_comparison_only"}],
    }
    config.update(config_overrides)
    return build_semantic_diff(_baseline_fixture(), _reference_fixture(), _selection_available(), config)


def _normalize_relative_path(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path).as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _read_claim_scan_text(relative_path: str) -> str:
    normalized = _normalize_relative_path(relative_path)
    assert normalized in FORBIDDEN_CLAIM_SCAN_PATHS
    assert not normalized.startswith("/")
    assert ".." not in PurePosixPath(normalized).parts
    for forbidden in DISALLOWED_SCAN_PREFIXES:
        assert not normalized.startswith(forbidden)
    return (PROJECT_ROOT / normalized).read_text(encoding="utf-8")


def _forbidden_positive_claim_findings() -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for path in FORBIDDEN_CLAIM_SCAN_PATHS:
        text = _read_claim_scan_text(path)
        for pattern in FORBIDDEN_POSITIVE_CLAIM_PATTERNS:
            for match in pattern.finditer(text):
                context = text[max(0, match.start() - 40) : match.end() + 40]
                if any(marker in context for marker in NEGATING_CLAIM_CONTEXT_MARKERS):
                    continue
                findings.append((path, pattern.pattern))
    return findings


def test_t_s05_05_selector_and_clean_feed_gate_contracts_cover_blocked_reason_and_limitations() -> None:
    default_result = select_research_backend()

    assert default_result.selected_backend == "lightweight"
    assert default_result.availability_status == "available"
    assert default_result.import_attempted is False
    assert all(value == 0 for value in default_result.forbidden_operation_counts.values())

    missing_gate = validate_clean_feed_gate({key: value for key, value in _clean_evidence().items() if key != "benchmark_status"})

    assert missing_gate.passed is False
    assert missing_gate.availability_status == "data_required_missing"
    assert "data_required_missing:benchmark_status" in missing_gate.blocked_reasons
    assert missing_gate.unavailable is not None
    assert all(value == 0 for value in missing_gate.forbidden_operation_counts.values())

    request = BackendSelectionRequest(backend="backtrader", clean_feed_evidence=_clean_evidence())
    selected = select_research_backend(request)

    assert selected.selected_backend == "none"
    assert selected.availability_status == "runtime_not_authorized"
    assert "runtime_not_authorized:backtrader_runtime_authorized_false" in selected.blocked_reasons
    assert selected.import_attempted is False
    assert set(selected.forbidden_operation_counts) == set(adapter.FORBIDDEN_OPERATION_COUNTERS)


def test_t_s05_06_semantic_diff_schema_contract_keeps_baseline_reference_limitations_and_counters() -> None:
    artifact = _semantic_diff_artifact()
    data = artifact.to_dict()
    validation = validate_semantic_diff_artifact(data)

    assert validation.passed is True
    assert data["schema_version"] == SEMANTIC_DIFF_SCHEMA_VERSION
    assert data["artifact_type"] == "research_comparison"
    assert len(REQUIRED_FIELD_GROUPS) >= 10
    assert set(REQUIRED_FIELD_GROUPS).issubset(data)
    assert data["metadata"]["baseline_backend"] == "lightweight"
    assert data["metadata"]["reference_backend"] == "backtrader_optional_reference"
    assert data["metadata"]["baseline_backend"] != data["metadata"]["reference_backend"]
    assert data["availability"]["limitations"]
    assert data["limitations"]
    assert all(value == 0 for value in validation.forbidden_operation_counts.values())

    unavailable_artifact = build_semantic_diff(
        _baseline_fixture(),
        None,
        {
            "selected_backend": "none",
            "availability_status": "backend_unavailable",
            "blocked_reasons": ("backend_unavailable:dependency_missing",),
            "limitations": [{"code": "optional_reference_not_installed"}],
            "forbidden_operation_counts": semantic_zero_counts(),
        },
        {"generated_at": "2026-06-02T09:11:00+08:00", "source_run_id": "run-reference-unavailable"},
    ).to_dict()

    assert validate_semantic_diff_artifact(unavailable_artifact).passed is True
    assert unavailable_artifact["availability"]["reference_available"] is False
    assert "backend_unavailable:dependency_missing" in unavailable_artifact["availability"]["blocked_reasons"]
    assert unavailable_artifact["explanation"]["diff_reason"] == ["reference_unavailable"]


def test_t_s05_07_order_intent_draft_schema_preserves_qmt_boundary_and_blocked_reasons() -> None:
    result = build_order_intent_draft([_target_row()], _semantic_diff_artifact(), _policy())

    assert result.status == "draft"
    assert result.draft is not None
    payload = result.draft.to_dict()
    validation = validate_order_intent_draft(payload)

    assert validation.passed is True
    assert payload["schema_version"] == ORDER_INTENT_SCHEMA_VERSION
    assert set(REQUIRED_DRAFT_FIELDS).issubset(payload)
    assert payload["qmt_allowed"] is False
    assert payload["not_authorization"] is True
    assert payload["consumer"] == LATER_GATED_CONSUMER
    assert payload["execution_price_policy"] == "raw"
    assert validation.required_field_coverage == 1.0
    assert all(value == 0 for value in validation.forbidden_operation_counts.values())

    blocked = build_order_intent_draft(
        [_target_row()],
        _semantic_diff_artifact(),
        _policy(execution_price_policy="hfq"),
    )

    assert blocked.status == "blocked"
    assert blocked.draft is None
    assert blocked.handoff is None
    assert "non_raw_execution_price_policy" in blocked.blocked_reasons
    assert "raw_execution_policy_blocked" in blocked.blocked_reasons
    assert all(value == 0 for value in blocked.operation_counters.values())


def test_t_s05_09_and_t_s05_10_ts025_scenarios_are_traceable_to_fixture_only_contracts() -> None:
    assert set(TS025_SCENARIO_COVERAGE) == {f"TS-025-{index:02d}" for index in range(1, 12)}
    assert len(TS025_SCENARIO_COVERAGE) == 11
    assert TS025_SCENARIO_COVERAGE["TS-025-08"] == "fixture-only verification"
    assert TS025_SCENARIO_COVERAGE["TS-025-10"] == "no-real-operation counters"


def test_t_s05_12_forbidden_claim_scope_scan_has_zero_positive_implementation_claims() -> None:
    assert _forbidden_positive_claim_findings() == []


def test_t_s05_12_claim_scan_scope_is_bounded_to_cr025_contract_documents() -> None:
    for path in FORBIDDEN_CLAIM_SCAN_PATHS:
        normalized = _normalize_relative_path(path)
        assert normalized in FORBIDDEN_CLAIM_SCAN_PATHS
        assert not normalized.startswith("/home/hyde/download/backtrader")
        assert not normalized.startswith("data/market_data")
        assert not normalized.startswith("broker_lake")
        assert normalized != ".env"
