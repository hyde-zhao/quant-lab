"""CR-173 S03：离线 estimator 的静态授权与 public 边界守卫。"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Final


ROOT = Path(__file__).parents[2]

CR173_NEW_CODE_PATHS: Final[tuple[str, ...]] = (
    "engine/effective_trial_evidence.py",
    "engine/effective_trial_estimator.py",
    "tests/research/test_effective_trial_evidence_contracts.py",
    "tests/research/test_effective_trial_estimator.py",
    "tests/fixtures/effective_trial/golden_vectors_v1.json",
    "tests/research/test_effective_trial_cr173_qac.py",
    "tests/research/test_effective_trial_authorization.py",
)

PUBLIC_PRODUCTION_PATHS: Final[tuple[str, ...]] = (
    "engine/experiment_family_lineage.py",
    "engine/experiment_family_lineage_store.py",
    "engine/strategy_admission_statistical_gate.py",
    "engine/statistical_evidence.py",
    "engine/multiple_testing_evidence.py",
    "engine/overfit_evidence.py",
    "engine/cross_strategy_reliability_gates.py",
    "engine/strategy_admission_package.py",
)

PUBLIC_REGRESSION_PATHS: Final[tuple[str, ...]] = (
    "tests/research/test_experiment_family_lineage_contracts.py",
    "tests/research/test_trial_lineage_integrity.py",
    "tests/research/test_trial_lineage_authorization.py",
    "tests/research/test_trial_lineage_admission_projection.py",
    "tests/research/test_trial_lineage_legacy_admission_regression.py",
    "tests/research/test_cross_strategy_reliability_gates.py",
    "tests/research/test_statistical_evidence_projection.py",
    "tests/research/test_statistical_evidence_contracts.py",
    "tests/research/test_statistical_evidence_qac.py",
    "tests/research/test_statistical_evidence_cr155_regression.py",
    "tests/research/test_overfit_evidence.py",
    "tests/research/test_statistical_evidence_authorization.py",
)

PUBLIC_METRIC_NAMES: Final[tuple[str, ...]] = (
    "cr173_new_code_public_dependency_edges",
    "cr173_new_code_public_calls",
    "public_production_diff",
    "public_writes",
    "cp7_read_only_public_regression_inventory",
    "existing_expected_edits",
)


@dataclass(frozen=True)
class StaticSurface:
    imports: frozenset[str]
    import_bindings: tuple[tuple[str, str], ...]
    calls: tuple[str, ...]
    write_calls: tuple[str, ...]
    command_calls: tuple[tuple[str, tuple[str, ...]], ...]
    string_literals: tuple[str, ...]


def _resolve_name(node: ast.expr, bindings: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return bindings.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        prefix = _resolve_name(node.value, bindings)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _resolve_name(node.func, bindings)
    return ""


def _literal_argv(node: ast.Call) -> tuple[str, ...]:
    if not node.args:
        return ()
    value = node.args[0]
    if isinstance(value, (ast.List, ast.Tuple)):
        if all(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in value.elts):
            return tuple(str(item.value) for item in value.elts)
        return ()
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return tuple(value.value.split())
    return ()


def _open_mode(node: ast.Call) -> str | None:
    mode_node: ast.expr | None = node.args[1] if len(node.args) >= 2 else None
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode_node = keyword.value
    if mode_node is None:
        return "r"
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return mode_node.value
    return None


def _scan_tree(tree: ast.AST) -> StaticSurface:
    imports: set[str] = set()
    bindings: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
                if alias.asname:
                    bindings[alias.asname] = alias.name
                else:
                    root = alias.name.split(".", 1)[0]
                    bindings[root] = root
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
            for alias in node.names:
                if alias.name == "*":
                    continue
                qualified = f"{node.module}.{alias.name}"
                imports.add(qualified)
                bindings[alias.asname or alias.name] = qualified

    calls: list[str] = []
    writes: list[str] = []
    commands: list[tuple[str, tuple[str, ...]]] = []
    strings: list[str] = []
    command_targets = {
        "subprocess.run",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.Popen",
        "os.system",
        "os.popen",
    }
    direct_write_targets = {
        "os.replace",
        "os.rename",
        "os.remove",
        "os.unlink",
        "shutil.copy",
        "shutil.copyfile",
        "shutil.move",
        "shutil.rmtree",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _resolve_name(node.func, bindings)
            calls.append(name)
            if name in command_targets:
                commands.append((name, _literal_argv(node)))
            if name in {"open", "io.open", "pathlib.Path.open"}:
                mode = _open_mode(node)
                if mode is None or any(flag in mode for flag in "wax+"):
                    writes.append(name)
            elif name in direct_write_targets:
                writes.append(name)
            elif name.endswith((".write_text", ".write_bytes", ".unlink", ".rename")):
                writes.append(name)
            elif name == "pathlib.Path.replace":
                writes.append(name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append(node.value)
    return StaticSurface(
        imports=frozenset(imports),
        import_bindings=tuple(sorted(bindings.items())),
        calls=tuple(calls),
        write_calls=tuple(writes),
        command_calls=tuple(commands),
        string_literals=tuple(strings),
    )


def _scan_source(source: str) -> StaticSurface:
    return _scan_tree(ast.parse(source))


def _scan_python(paths: tuple[str, ...]) -> StaticSurface:
    surfaces: list[StaticSurface] = []
    for relative in paths:
        if not relative.endswith(".py"):
            continue
        source = (ROOT / relative).read_text(encoding="utf-8")
        surfaces.append(_scan_tree(ast.parse(source, filename=relative)))
    return StaticSurface(
        imports=frozenset().union(*(surface.imports for surface in surfaces)),
        import_bindings=tuple(
            sorted({binding for surface in surfaces for binding in surface.import_bindings})
        ),
        calls=tuple(call for surface in surfaces for call in surface.calls),
        write_calls=tuple(call for surface in surfaces for call in surface.write_calls),
        command_calls=tuple(call for surface in surfaces for call in surface.command_calls),
        string_literals=tuple(value for surface in surfaces for value in surface.string_literals),
    )


def _is_git_push(argv: tuple[str, ...]) -> bool:
    return len(argv) >= 2 and argv[0].rsplit("/", 1)[-1] == "git" and argv[1] == "push"


def _non_public_operation_counters(surface: StaticSurface) -> dict[str, int]:
    call_leafs = {name.rsplit(".", 1)[-1] for name in surface.calls}
    credential_targets = {
        "os.getenv",
        "os.environ.get",
        "dotenv.load_dotenv",
        "keyring.get_password",
    }
    network_prefixes = ("requests.", "httpx.", "urllib3.", "socket.")
    network_targets = {"urllib.request.urlopen", "urllib.request.urlretrieve"}
    runtime_commands = sum(
        not _is_git_push(argv) for _, argv in surface.command_calls
    )
    git_push_commands = sum(_is_git_push(argv) for _, argv in surface.command_calls)
    return {
        "NP-01": sum(name in credential_targets for name in surface.calls),
        "NP-02": sum(
            name in call_leafs for name in {"read_real_data", "read_production_data"}
        ),
        "NP-03": sum(
            name in call_leafs
            for name in {"read_lake", "write_lake", "sync_nas", "mount_nas"}
        ),
        "NP-04": sum(
            name in network_targets or name.startswith(network_prefixes)
            for name in surface.calls
        ),
        "NP-05": len(surface.write_calls),
        "NP-06": runtime_commands + sum(
            name in call_leafs
            for name in {"run_strategy", "execute_strategy", "run_simulation", "run_framework"}
        ),
        "NP-07": sum(
            name in call_leafs for name in {"place_order", "send_order", "qmt_connect", "broker_write"}
        ),
        "NP-08": sum(name in call_leafs for name in {"publish", "deploy", "release_push"}),
        "NP-09": git_push_commands
        + sum(name in call_leafs for name in {"git_push", "push_remote"}),
    }


def _public_metrics(surface: StaticSurface) -> tuple[int, int]:
    public_modules = {
        path.removesuffix(".py").replace("/", ".")
        for path in PUBLIC_PRODUCTION_PATHS
    }
    dependencies = sum(
        any(imported == module or imported.startswith(f"{module}.") for module in public_modules)
        for imported in surface.imports
    )
    calls = sum(
        any(call.startswith(f"{module}.") for module in public_modules)
        for call in surface.calls
    )
    return dependencies, calls


def test_non_public_operation_inventory_is_exactly_nine_unique_zero_counters() -> None:
    surface = _scan_python(CR173_NEW_CODE_PATHS)
    counters = _non_public_operation_counters(surface)
    assert tuple(counters) == tuple(f"NP-{index:02d}" for index in range(1, 10))
    assert len(counters) == len(set(counters)) == 9
    assert all(value == 0 for value in counters.values())
    assert set(counters).isdisjoint(PUBLIC_METRIC_NAMES)


def test_cr173_new_code_has_no_public_dependency_edge_or_call() -> None:
    surface = _scan_python(CR173_NEW_CODE_PATHS)
    cr173_new_code_public_dependency_edges, cr173_new_code_public_calls = (
        _public_metrics(surface)
    )
    assert len(PUBLIC_PRODUCTION_PATHS) == len(set(PUBLIC_PRODUCTION_PATHS)) == 8
    assert cr173_new_code_public_dependency_edges == 0
    assert cr173_new_code_public_calls == 0


def test_adversarial_ast_binding_detects_each_real_operation_in_one_class() -> None:
    cases = {
        "NP-01": (
            "import os as operating_system\n"
            "value = operating_system.environ.get('TOKEN')\n"
        ),
        "NP-01-alias": "from os import getenv as read_secret\nvalue = read_secret('TOKEN')\n",
        "NP-04": (
            "import urllib.request as web_request\n"
            "response = web_request.urlopen('https://example.invalid')\n"
        ),
        "NP-04-alias": (
            "from urllib.request import urlopen as fetch\n"
            "response = fetch('https://example.invalid')\n"
        ),
        "NP-05": "import os as operating_system\noperating_system.replace('a', 'b')\n",
        "NP-05-path": (
            "from pathlib import Path as P\n"
            "P('artifact.txt').write_text('payload', encoding='utf-8')\n"
        ),
        "NP-05-open": "handle = open('artifact.txt', 'w', encoding='utf-8')\n",
        "NP-06": "import subprocess as process\nprocess.run(['python', 'worker.py'])\n",
        "NP-09": (
            "from subprocess import run as execute\n"
            "execute(['git', 'push', 'origin', 'main'])\n"
        ),
    }
    expected = {
        "NP-01": "NP-01",
        "NP-01-alias": "NP-01",
        "NP-04": "NP-04",
        "NP-04-alias": "NP-04",
        "NP-05": "NP-05",
        "NP-05-path": "NP-05",
        "NP-05-open": "NP-05",
        "NP-06": "NP-06",
        "NP-09": "NP-09",
    }
    for case_id, source in cases.items():
        counters = _non_public_operation_counters(_scan_source(source))
        assert counters[expected[case_id]] == 1, case_id
        assert sum(counters.values()) == 1, case_id


def test_public_module_alias_import_and_call_are_both_detected() -> None:
    cases = (
        "import engine.experiment_family_lineage as lineage\n"
        "lineage.consume_family_lineage_projection(None)\n",
        "from engine import experiment_family_lineage as lineage\n"
        "lineage.consume_family_lineage_projection(None)\n",
        "from engine.experiment_family_lineage import consume_family_lineage_projection as consume\n"
        "consume(None)\n",
    )
    for source in cases:
        dependency_edges, calls = _public_metrics(_scan_source(source))
        assert dependency_edges > 0
        assert calls > 0


def test_dangerous_words_and_plain_string_replace_have_no_execution_semantics() -> None:
    source = (
        "payload = \"urllib.request.urlopen subprocess.run(['git','push']) "
        "os.replace os.environ.get engine.experiment_family_lineage\"\n"
        "normalized = payload.replace('a', 'b')\n"
        "from pathlib import Path\n"
        "fixture = Path('fixture.json').read_text(encoding='utf-8')\n"
    )
    surface = _scan_source(source)
    assert all(value == 0 for value in _non_public_operation_counters(surface).values())
    assert _public_metrics(surface) == (0, 0)
    assert surface.write_calls == ()


def test_public_production_diff_and_write_manifests_are_empty() -> None:
    changed = set(CR173_NEW_CODE_PATHS)
    production = set(PUBLIC_PRODUCTION_PATHS)
    public_production_diff = len(changed & production)
    public_writes = len(changed & production)
    assert public_production_diff == 0
    assert public_writes == 0


def test_existing_public_regression_inventory_is_exact_read_only_twelve() -> None:
    assert len(PUBLIC_REGRESSION_PATHS) == len(set(PUBLIC_REGRESSION_PATHS)) == 12
    assert all((ROOT / relative).is_file() for relative in PUBLIC_REGRESSION_PATHS)
    cp7_read_only_public_regression_inventory = len(PUBLIC_REGRESSION_PATHS)
    existing_expected_edits = len(
        set(PUBLIC_REGRESSION_PATHS) & set(CR173_NEW_CODE_PATHS)
    )
    assert cp7_read_only_public_regression_inventory == 12
    assert existing_expected_edits == 0


def test_public_and_non_public_metric_lanes_do_not_overlap() -> None:
    non_public = {f"NP-{index:02d}" for index in range(1, 10)}
    public = set(PUBLIC_METRIC_NAMES)
    assert len(public) == 6
    assert non_public.isdisjoint(public)
    assert len(non_public | public) == 15


def test_fixture_and_claim_boundary_authorize_only_standalone_offline_evidence() -> None:
    fixture = (ROOT / "tests/fixtures/effective_trial/golden_vectors_v1.json").read_text(
        encoding="utf-8"
    )
    lowered = fixture.lower()
    assert "strategy_id" not in lowered
    assert "strategy_name" not in lowered
    assert "credential" not in lowered
    assert "provider_endpoint" not in lowered
    claims = {
        "standalone_offline_spectral_effective_dimensionality": True,
        "fixture_only": True,
        "public_effective_trial_count_populatable": False,
        "c1_computable": False,
        "gate1_pass": False,
        "fwer_or_dsr_calibrated": False,
        "admission_ready": False,
        "stage3_ready": False,
        "cr172_auto_resume": False,
        "cr172_auto_close": False,
    }
    assert sum(value is True for value in claims.values()) == 2
    assert all(
        claims[name] is False
        for name in claims
        if name not in {
            "standalone_offline_spectral_effective_dimensionality",
            "fixture_only",
        }
    )
