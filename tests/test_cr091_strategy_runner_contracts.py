from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from trading.strategy_runner import (
    ReadonlyGatewayResult,
    ReadonlyGatewayClient,
    adapt_strategy_payload,
    build_evidence_summary,
    load_strategy_package,
    resolve_active_package,
)
from trading.strategy_runner.adapters import zero_cr091_operation_counters
from trading.strategy_runner.cache import StrategyCacheError
from trading.strategy_runner.evidence import EvidenceRedactionError, assert_redacted
from trading.strategy_runner.package_loader import PackageLoaderError


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "cr091_strategy_runner"
PACKAGE_ROOT = FIXTURE_ROOT / "cr091_strategy_package"


def load_json(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def test_multifactor_adapter_outputs_target_portfolio_and_order_intents() -> None:
    payload = load_json("cr091_multifactor_admission_package_pass.json")

    result = adapt_strategy_payload(payload, run_id="cr091-test-mf")

    assert result.passed
    assert result.not_authorization is True
    assert result.target_portfolio is not None
    assert result.target_portfolio.not_authorization is True
    assert result.target_portfolio.target_symbols == ("FIXTURE_A", "FIXTURE_B")
    assert len(result.order_intents) == 2
    for intent in result.order_intents:
        assert intent.passed
        assert intent.draft is not None
        assert intent.draft.qmt_allowed is False
        assert intent.draft.not_authorization is True


def test_legacy_strategy_adapter_outputs_equal_weight_contract() -> None:
    payload = load_json("cr091_legacy_strategy_result_momentum.json")

    result = adapt_strategy_payload(payload, run_id="cr091-test-legacy")

    assert result.passed
    assert result.target_portfolio is not None
    assert result.target_portfolio.strategy_id == "momentum"
    assert sum(result.target_portfolio.target_weights.values()) == pytest.approx(1.0)
    assert len(result.order_intents) == 3


def test_legacy_strategy_adapter_fail_closed_for_empty_targets() -> None:
    payload = load_json("cr091_legacy_strategy_result_momentum.json")
    payload["target_symbols"] = []

    result = adapt_strategy_payload(payload, run_id="cr091-test-empty")

    assert result.status == "blocked"
    assert "blocked_empty_targets" in result.blocked_reasons


def test_package_manifest_checksum_and_active_pointer_contracts() -> None:
    package = load_strategy_package(PACKAGE_ROOT)
    active = resolve_active_package(PACKAGE_ROOT / "cache", PACKAGE_ROOT / "cache" / "active.json")

    assert package.package_id == "strategy-package-cr091-fixture-0.1.0"
    assert active.package_id == package.package_id
    adapter_payload = package.to_adapter_payload()
    assert adapter_payload["manifest_checksum_verified"] is True
    assert adapter_payload["runtime_authorized"] is False
    assert adapter_payload["nas_operation_authorized"] is False
    assert adapter_payload["credential_read_authorized"] is False
    assert adapter_payload["account_query_authorized"] is False
    assert adapter_payload["trade_write_authorized"] is False


def test_package_loader_requires_payload_checksum(tmp_path: Path) -> None:
    package_copy = tmp_path / "package"
    package_copy.mkdir()
    manifest = yaml.safe_load((PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    manifest["checksums"] = {
        "cache/active.json": manifest["checksums"]["cache/active.json"],
    }
    (package_copy / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (package_copy / "payload").mkdir()
    (package_copy / "payload" / "admission.json").write_text(
        (PACKAGE_ROOT / "payload" / "admission.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (package_copy / "cache").mkdir()
    (package_copy / "cache" / "active.json").write_text(
        (PACKAGE_ROOT / "cache" / "active.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(PackageLoaderError, match="checksum_missing"):
        load_strategy_package(package_copy)


def test_package_loader_fail_closed_on_bad_checksum(tmp_path: Path) -> None:
    package_copy = tmp_path / "package"
    package_copy.mkdir()
    for child in ("manifest.yaml",):
        (package_copy / child).write_text((PACKAGE_ROOT / child).read_text(encoding="utf-8"), encoding="utf-8")
    (package_copy / "payload").mkdir()
    (package_copy / "payload" / "admission.json").write_text("{}", encoding="utf-8")

    with pytest.raises(PackageLoaderError, match="blocked_checksum_mismatch"):
        load_strategy_package(package_copy)


def test_active_pointer_fail_closed_when_not_immutable(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    package = cache / "pkg"
    package.mkdir(parents=True)
    pointer = cache / "active.json"
    pointer.write_text(
        json.dumps({"package_id": "pkg", "package_path": "pkg", "not_authorization": True}),
        encoding="utf-8",
    )

    with pytest.raises(StrategyCacheError, match="blocked_cache_package_not_immutable"):
        resolve_active_package(cache, pointer)


def test_strategy_package_adapter_dispatches_loaded_payload() -> None:
    package = load_strategy_package(PACKAGE_ROOT)

    result = adapt_strategy_payload(package.to_adapter_payload(), run_id="cr091-test-package")

    assert result.passed
    assert result.target_portfolio is not None
    assert result.target_portfolio.strategy_id == "strategy_package_alpha"
    assert len(result.order_intents) == 2


def test_strategy_package_adapter_requires_all_authorization_flags_false() -> None:
    package = load_strategy_package(PACKAGE_ROOT)
    payload = package.to_adapter_payload()
    payload["account_query_authorized"] = True

    result = adapt_strategy_payload(payload, run_id="cr091-test-package-flags")

    assert result.status == "blocked"
    assert "blocked_manifest_flags_nonfalse" in result.blocked_reasons


def test_readonly_fake_gateway_allows_only_listed_endpoints() -> None:
    client = ReadonlyGatewayClient()

    assert client.health(run_id="cr091-test-gateway").passed
    assert client.capabilities(run_id="cr091-test-gateway").passed
    positions = client.query_positions(run_id="cr091-test-gateway")
    assert positions.passed
    assert positions.payload["raw_payload_emitted"] is False

    blocked = client.call("submit_order", run_id="cr091-test-gateway")
    assert blocked.status == "blocked"
    assert blocked.reason_code == "blocked_scope_denied"


def test_evidence_redacts_sensitive_material_and_counts_forbidden_operations() -> None:
    payload = load_json("cr091_multifactor_admission_package_pass.json")
    adapter_result = adapt_strategy_payload(payload, run_id="cr091-test-evidence")
    readonly = ReadonlyGatewayClient().query_positions(run_id="cr091-test-evidence")

    evidence = build_evidence_summary(
        run_id="cr091-test-evidence",
        package_id="fixture-package",
        adapter_type="multifactor_admission",
        adapter_result=adapter_result,
        readonly_result=readonly,
    )

    assert evidence.status == "pass"
    assert evidence.forbidden_operation_counters == zero_cr091_operation_counters()
    assert evidence.redaction_assurance["token_emitted"] is False
    assert evidence.redaction_assurance["raw_positions_emitted"] is False
    assert evidence.not_authorization is True


def test_evidence_blocks_readonly_forbidden_counter_or_blocked_status() -> None:
    payload = load_json("cr091_multifactor_admission_package_pass.json")
    adapter_result = adapt_strategy_payload(payload, run_id="cr091-test-evidence-block")
    readonly = ReadonlyGatewayResult(
        endpoint="query_positions",
        status="ok",
        payload={"redaction_status": "pass", "raw_payload_emitted": False},
        operation_counters={"gateway_socket_open": 1},
    )

    evidence = build_evidence_summary(
        run_id="cr091-test-evidence-block",
        package_id="fixture-package",
        adapter_type="multifactor_admission",
        adapter_result=adapter_result,
        readonly_result=readonly,
    )

    assert evidence.status == "blocked"
    assert evidence.forbidden_operation_counters["gateway_socket_open"] == 1


def test_evidence_redaction_blocks_sensitive_payload() -> None:
    with pytest.raises(EvidenceRedactionError):
        assert_redacted({"token": "fixture-token-value", "not_authorization": True})
