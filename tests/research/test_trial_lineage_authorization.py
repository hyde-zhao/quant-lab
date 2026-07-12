from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import socket
import subprocess
from typing import Callable, Iterator, Mapping
from urllib import request as urllib_request

import pytest

from engine.experiment_family_lineage import (
    AttemptState,
    DeclareTrial,
    ExperimentFamilySpec,
    ExperimentTrial,
    FinalizeTrial,
    FinishAttempt,
    RequestSeal,
    StartAttempt,
    TrialAttempt,
    TrialState,
    derive_stable_trial_id,
    project_family_evidence,
)
from engine.experiment_family_lineage_store import LocalFamilyLineageRecorder
from engine.mature_multifactor_research import PRODUCER_LINEAGE_MAPPING_INVENTORY
from engine.strategy_admission_package import attach_family_lineage_to_admission_package
from engine.strategy_admission_statistical_gate import ValidationBoundFamilyEvidence


FORBIDDEN_OPERATION_CATEGORIES = (
    "lake_read",
    "lake_write",
    "nas",
    "provider_or_network",
    "credential_or_secret",
    "research_runtime",
    "simulation",
    "paper",
    "live",
    "broker_or_trading",
    "external_registry_store_catalog",
    "git_remote_or_publish",
    "historical_backfill_or_reconstruction",
)
FORBIDDEN_OPERATION_KEYS = frozenset(FORBIDDEN_OPERATION_CATEGORIES)
BOUNDARY_INSTALLATION_MANIFEST = {
    "lake_read": {"target": "pathlib.Path.open", "predicate": "marker path + read mode"},
    "lake_write": {"target": "pathlib.Path.open", "predicate": "marker path + write mode"},
    "nas": {"target": "os.scandir", "predicate": "marker NAS path"},
    "provider_or_network": {"target": "socket.create_connection", "predicate": "marker provider host"},
    "credential_or_secret": {"target": "os.getenv", "predicate": "marker credential key"},
    "research_runtime": {"target": "subprocess.Popen", "predicate": "marker research command"},
    "simulation": {"target": "subprocess.run", "predicate": "marker simulation command"},
    "paper": {"target": "subprocess.call", "predicate": "marker paper command"},
    "live": {"target": "subprocess.check_call", "predicate": "marker live command"},
    "broker_or_trading": {"target": "socket.socket", "predicate": "marker broker family"},
    "external_registry_store_catalog": {"target": "urllib.request.urlopen", "predicate": "marker external URL"},
    "git_remote_or_publish": {"target": "subprocess.check_output", "predicate": "marker git command"},
    "historical_backfill_or_reconstruction": {"target": "pathlib.Path.glob", "predicate": "marker backfill path"},
}
MARKERS = {
    "lake_read": "__CR163_LAKE_READ__",
    "lake_write": "__CR163_LAKE_WRITE__",
    "nas": "__CR163_NAS__",
    "provider_or_network": "__CR163_PROVIDER__",
    "credential_or_secret": "__CR163_CREDENTIAL__",
    "research_runtime": "__CR163_RESEARCH__",
    "simulation": "__CR163_SIMULATION__",
    "paper": "__CR163_PAPER__",
    "live": "__CR163_LIVE__",
    "broker_or_trading": "__CR163_BROKER__",
    "external_registry_store_catalog": "cr163-marker://external-registry",
    "git_remote_or_publish": "__CR163_GIT_REMOTE__",
    "historical_backfill_or_reconstruction": "__CR163_BACKFILL__",
}


class ForbiddenOperationAttempt(AssertionError):
    pass


def validate_authorization_evidence(evidence: Mapping[str, object]) -> dict[str, int]:
    keys = set(evidence)
    if keys != FORBIDDEN_OPERATION_KEYS:
        missing = sorted(FORBIDDEN_OPERATION_KEYS - keys)
        unknown = sorted(keys - FORBIDDEN_OPERATION_KEYS)
        raise AssertionError(f"authorization_schema_mismatch:missing={missing}:unknown={unknown}")
    validated: dict[str, int] = {}
    for category in FORBIDDEN_OPERATION_CATEGORIES:
        value = evidence[category]
        if type(value) is not int or value < 0:
            raise AssertionError(f"authorization_counter_invalid:{category}:{value!r}")
        validated[category] = value
    return validated


def assert_forbidden_operations_zero(evidence: Mapping[str, object]) -> None:
    validated = validate_authorization_evidence(evidence)
    nonzero = {name: value for name, value in validated.items() if value != 0}
    if nonzero:
        raise AssertionError(f"authorization_violation:{nonzero}")


class DenyByDefaultSentinels:
    def __init__(self) -> None:
        self._counts = {category: 0 for category in FORBIDDEN_OPERATION_CATEGORIES}
        self.hooks = {category: self._make_hook(category) for category in FORBIDDEN_OPERATION_CATEGORIES}
        self.active = False

    def _make_hook(self, category: str) -> Callable[..., None]:
        def deny(*_args: object, **_kwargs: object) -> None:
            self._counts[category] += 1
            raise ForbiddenOperationAttempt(f"forbidden_operation_attempt:{category}")

        return deny

    def _guard(
        self, category: str, original: Callable[..., object], predicate: Callable[..., bool]
    ) -> Callable[..., object]:
        def guarded(*args: object, **kwargs: object) -> object:
            if predicate(*args, **kwargs):
                self.hooks[category]()
            return original(*args, **kwargs)

        return guarded

    @contextmanager
    def installed(self, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
        assert set(self.hooks) == FORBIDDEN_OPERATION_KEYS
        assert set(BOUNDARY_INSTALLATION_MANIFEST) == FORBIDDEN_OPERATION_KEYS
        original_path_open = Path.open
        original_path_glob = Path.glob
        original_scandir = os.scandir
        original_create_connection = socket.create_connection
        original_socket = socket.socket
        original_getenv = os.getenv
        original_popen = subprocess.Popen
        original_run = subprocess.run
        original_call = subprocess.call
        original_check_call = subprocess.check_call
        original_check_output = subprocess.check_output
        original_urlopen = urllib_request.urlopen

        def guarded_path_open(path: Path, mode: str = "r", *args: object, **kwargs: object) -> object:
            path_text = os.fspath(path)
            if MARKERS["lake_read"] in path_text and not any(flag in mode for flag in "wax+"):
                self.hooks["lake_read"]()
            if MARKERS["lake_write"] in path_text and any(flag in mode for flag in "wax+"):
                self.hooks["lake_write"]()
            return original_path_open(path, mode, *args, **kwargs)

        self.active = True
        monkeypatch.setattr(Path, "open", guarded_path_open)
        monkeypatch.setattr(Path, "glob", self._guard(
            "historical_backfill_or_reconstruction", original_path_glob,
            lambda path, *_args, **_kwargs: MARKERS["historical_backfill_or_reconstruction"] in os.fspath(path),
        ))
        monkeypatch.setattr(os, "scandir", self._guard(
            "nas", original_scandir,
            lambda path=".", *_args, **_kwargs: MARKERS["nas"] in os.fspath(path),
        ))
        monkeypatch.setattr(socket, "create_connection", self._guard(
            "provider_or_network", original_create_connection,
            lambda address, *_args, **_kwargs: MARKERS["provider_or_network"] in str(address[0]),
        ))
        monkeypatch.setattr(socket, "socket", self._guard(
            "broker_or_trading", original_socket,
            lambda family=socket.AF_INET, *_args, **_kwargs: family == MARKERS["broker_or_trading"],
        ))
        monkeypatch.setattr(os, "getenv", self._guard(
            "credential_or_secret", original_getenv,
            lambda key, *_args, **_kwargs: key == MARKERS["credential_or_secret"],
        ))
        monkeypatch.setattr(subprocess, "Popen", self._guard(
            "research_runtime", original_popen,
            lambda command, *_args, **_kwargs: MARKERS["research_runtime"] in str(command),
        ))
        monkeypatch.setattr(subprocess, "run", self._guard(
            "simulation", original_run,
            lambda command, *_args, **_kwargs: MARKERS["simulation"] in str(command),
        ))
        monkeypatch.setattr(subprocess, "call", self._guard(
            "paper", original_call,
            lambda command, *_args, **_kwargs: MARKERS["paper"] in str(command),
        ))
        monkeypatch.setattr(subprocess, "check_call", self._guard(
            "live", original_check_call,
            lambda command, *_args, **_kwargs: MARKERS["live"] in str(command),
        ))
        monkeypatch.setattr(subprocess, "check_output", self._guard(
            "git_remote_or_publish", original_check_output,
            lambda command, *_args, **_kwargs: MARKERS["git_remote_or_publish"] in str(command),
        ))
        monkeypatch.setattr(urllib_request, "urlopen", self._guard(
            "external_registry_store_catalog", original_urlopen,
            lambda url, *_args, **_kwargs: MARKERS["external_registry_store_catalog"] in str(url),
        ))
        try:
            yield
        finally:
            self.active = False

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


def _invoke_installed_marker(category: str) -> None:
    marker = MARKERS[category]
    if category == "lake_read":
        Path(marker).open("r")
    elif category == "lake_write":
        Path(marker).open("w")
    elif category == "nas":
        os.scandir(marker)
    elif category == "provider_or_network":
        socket.create_connection((marker, 1))
    elif category == "credential_or_secret":
        os.getenv(marker)
    elif category == "research_runtime":
        subprocess.Popen([marker])
    elif category == "simulation":
        subprocess.run([marker])
    elif category == "paper":
        subprocess.call([marker])
    elif category == "live":
        subprocess.check_call([marker])
    elif category == "broker_or_trading":
        socket.socket(marker)  # type: ignore[arg-type]
    elif category == "external_registry_store_catalog":
        urllib_request.urlopen(marker)
    elif category == "git_remote_or_publish":
        subprocess.check_output([marker])
    else:
        Path(marker).glob("*")


def _exercise_synthetic_public_path(tmp_path: Path, sentinels: DenyByDefaultSentinels) -> None:
    assert sentinels.active
    family_id = "authorization-family"
    spec = ExperimentFamilySpec(
        1, family_id, "public_stage3", 0,
        "objective:synthetic", "space:synthetic", metadata={"fixture": True},
    )
    parameters = {"lookback": 20}
    trial_id = derive_stable_trial_id(family_id, parameters, 7)
    trial = ExperimentTrial(family_id, trial_id, parameters, 7, 1)
    attempt = TrialAttempt(family_id, trial_id, "attempt-1", 1)
    recorder, declaration = LocalFamilyLineageRecorder.open(tmp_path, spec)
    assert declaration.accepted
    commands = (
        DeclareTrial("event-1", family_id, 1, trial=trial),
        StartAttempt("event-2", family_id, 2, attempt=attempt),
        FinishAttempt(
            "event-3", family_id, 3, attempt_id=attempt.attempt_id,
            state=AttemptState.FAILED, terminal_reason="synthetic",
        ),
        FinalizeTrial(
            "event-4", family_id, 4, trial_id=trial_id,
            state=TrialState.FAILED, terminal_reason="synthetic",
        ),
        RequestSeal("event-5", family_id, 5, manifest_version=1),
    )
    for command in commands:
        assert recorder.submit(command).accepted
    sealed = recorder.seal(1)
    projection = project_family_evidence(sealed.manifest, sealed.validation)
    package = attach_family_lineage_to_admission_package(
        {
            "admission_status": "blocked", "evidence_refs": (),
            "blocked_reasons": (), "limitations": (), "not_authorized_counters": {},
            "not_qmt_authorization": True, "not_simulation_authorization": True,
            "not_live_authorization": True, "not_broker_order": True,
        },
        ValidationBoundFamilyEvidence(sealed.manifest, sealed.validation),
    )
    assert set(PRODUCER_LINEAGE_MAPPING_INVENTORY) == {
        "CPI-CR163-001", "CPI-CR163-002", "CPI-CR163-003", "CPI-CR163-004"
    }
    assert package["admission_status"] == "blocked"
    assert package["family_lineage_projection"]["raw_trial_count"] == 1
    recorder.close()


def test_synthetic_s01_s05_public_path_runs_under_thirteen_zero_sentinels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinels = DenyByDefaultSentinels()
    with sentinels.installed(monkeypatch):
        _exercise_synthetic_public_path(tmp_path, sentinels)
    observed = sentinels.snapshot()
    assert len(observed) == 13
    assert set(BOUNDARY_INSTALLATION_MANIFEST) == set(observed)
    assert all(set(item) == {"target", "predicate"} for item in BOUNDARY_INSTALLATION_MANIFEST.values())
    assert_forbidden_operations_zero(observed)


@pytest.mark.parametrize("category", FORBIDDEN_OPERATION_CATEGORIES)
def test_each_installed_concrete_boundary_blocks_marker_before_original(
    category: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinels = DenyByDefaultSentinels()
    original_marker_reached = False

    def safe_original(*_args: object, **_kwargs: object) -> None:
        nonlocal original_marker_reached
        original_marker_reached = True

    target = BOUNDARY_INSTALLATION_MANIFEST[category]["target"]
    if target == "pathlib.Path.open":
        monkeypatch.setattr(Path, "open", safe_original)
    elif target == "pathlib.Path.glob":
        monkeypatch.setattr(Path, "glob", safe_original)
    elif target == "os.scandir":
        monkeypatch.setattr(os, "scandir", safe_original)
    elif target == "socket.create_connection":
        monkeypatch.setattr(socket, "create_connection", safe_original)
    elif target == "socket.socket":
        monkeypatch.setattr(socket, "socket", safe_original)
    elif target == "os.getenv":
        monkeypatch.setattr(os, "getenv", safe_original)
    elif target.startswith("subprocess."):
        monkeypatch.setattr(subprocess, target.split(".", 1)[1], safe_original)
    else:
        monkeypatch.setattr(urllib_request, "urlopen", safe_original)

    with sentinels.installed(monkeypatch):
        with pytest.raises(ForbiddenOperationAttempt, match=category):
            _invoke_installed_marker(category)
    assert original_marker_reached is False
    assert sentinels.snapshot()[category] == 1
    with pytest.raises(AssertionError, match="authorization_violation"):
        assert_forbidden_operations_zero(sentinels.snapshot())


@pytest.mark.parametrize(
    "mutation,reason",
    (
        ("missing", "authorization_schema_mismatch"),
        ("unknown", "authorization_schema_mismatch"),
        ("boolean", "authorization_counter_invalid"),
        ("negative", "authorization_counter_invalid"),
        ("nonzero", "authorization_violation"),
    ),
)
def test_authorization_evidence_schema_and_values_fail_closed(mutation: str, reason: str) -> None:
    evidence: dict[str, object] = {category: 0 for category in FORBIDDEN_OPERATION_CATEGORIES}
    if mutation == "missing":
        evidence.pop("lake_read")
    elif mutation == "unknown":
        evidence["unknown_operation"] = 0
    elif mutation == "boolean":
        evidence["paper"] = False
    elif mutation == "negative":
        evidence["nas"] = -1
    else:
        evidence["historical_backfill_or_reconstruction"] = 1
    with pytest.raises(AssertionError, match=reason):
        assert_forbidden_operations_zero(evidence)
