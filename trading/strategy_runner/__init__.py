"""CR091 package-driven strategy runner offline contracts."""

from trading.strategy_runner.adapters import (
    AdapterRegistry,
    AdapterResult,
    LegacyStrategyResultAdapter,
    MultifactorAdmissionAdapter,
    StrategyAdapter,
    StrategyPackageAdapter,
    adapt_strategy_payload,
    zero_cr091_operation_counters,
)
from trading.strategy_runner.artifact_bundle import (
    RunArtifactBundle,
    inspect_run_artifact_bundle,
    replay_run_artifact_bundle,
    validate_run_artifact_bundle,
    write_run_artifact_bundle,
)
from trading.strategy_runner.cache import ActivePackagePointer, resolve_active_package
from trading.strategy_runner.evidence import EvidenceSummary, build_evidence_summary, write_evidence_summary
from trading.strategy_runner.evidence_index import RunEvidenceIndex, write_run_evidence_index
from trading.strategy_runner.package_exchange import (
    ExchangeOperationResult,
    PackageExchangeError,
    check_exchange,
    create_fake_exchange_root,
    fake_publish_package,
    fake_pull_package,
    validate_package,
)
from trading.strategy_runner.package_loader import StrategyPackage, load_strategy_package
from trading.strategy_runner.readonly_gateway import (
    FakeReadonlyQmtTransport,
    ReadonlyGatewayClient,
    ReadonlyGatewayResult,
    ReadonlyGatewayRuntimeConfig,
)
from trading.strategy_runner.run_registry import (
    RunRegistryEntry,
    append_run_registry_entry,
    append_run_registry_from_bundle,
    append_run_registry_from_result,
    inspect_run_registry_entry,
    read_run_registry,
)
from trading.strategy_runner.result import RunResult, write_run_result
from trading.strategy_runner.run_spec import RunSpec, RunSpecError
from trading.strategy_runner.runner import run_strategy_package, run_strategy_package_from_path, run_strategy_package_from_spec_file
from trading.strategy_runner.simulation_activation import (
    FunctionSimulationGateway,
    SimulationActivationRequest,
    SimulationActivationResult,
    SimulationGateway,
    activate_simulation_orders,
    blocked_simulation_gateway,
)
from trading.strategy_runner.target_portfolio import TargetPortfolioSnapshot

__all__ = (
    "ActivePackagePointer",
    "AdapterRegistry",
    "AdapterResult",
    "EvidenceSummary",
    "ExchangeOperationResult",
    "FakeReadonlyQmtTransport",
    "LegacyStrategyResultAdapter",
    "MultifactorAdmissionAdapter",
    "ReadonlyGatewayClient",
    "ReadonlyGatewayResult",
    "ReadonlyGatewayRuntimeConfig",
    "RunResult",
    "RunEvidenceIndex",
    "RunArtifactBundle",
    "RunRegistryEntry",
    "RunSpec",
    "RunSpecError",
    "SimulationActivationRequest",
    "SimulationActivationResult",
    "SimulationGateway",
    "PackageExchangeError",
    "StrategyAdapter",
    "StrategyPackage",
    "StrategyPackageAdapter",
    "TargetPortfolioSnapshot",
    "adapt_strategy_payload",
    "build_evidence_summary",
    "check_exchange",
    "create_fake_exchange_root",
    "fake_publish_package",
    "fake_pull_package",
    "load_strategy_package",
    "resolve_active_package",
    "run_strategy_package",
    "run_strategy_package_from_path",
    "run_strategy_package_from_spec_file",
    "FunctionSimulationGateway",
    "activate_simulation_orders",
    "append_run_registry_entry",
    "append_run_registry_from_bundle",
    "append_run_registry_from_result",
    "inspect_run_artifact_bundle",
    "inspect_run_registry_entry",
    "read_run_registry",
    "replay_run_artifact_bundle",
    "validate_run_artifact_bundle",
    "validate_package",
    "write_evidence_summary",
    "write_run_artifact_bundle",
    "write_run_evidence_index",
    "write_run_result",
    "blocked_simulation_gateway",
    "zero_cr091_operation_counters",
)
