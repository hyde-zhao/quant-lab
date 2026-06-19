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
from trading.strategy_runner.cache import ActivePackagePointer, resolve_active_package
from trading.strategy_runner.evidence import EvidenceSummary, build_evidence_summary, write_evidence_summary
from trading.strategy_runner.package_loader import StrategyPackage, load_strategy_package
from trading.strategy_runner.readonly_gateway import (
    FakeReadonlyQmtTransport,
    ReadonlyGatewayClient,
    ReadonlyGatewayResult,
    ReadonlyGatewayRuntimeConfig,
)
from trading.strategy_runner.target_portfolio import TargetPortfolioSnapshot

__all__ = (
    "ActivePackagePointer",
    "AdapterRegistry",
    "AdapterResult",
    "EvidenceSummary",
    "FakeReadonlyQmtTransport",
    "LegacyStrategyResultAdapter",
    "MultifactorAdmissionAdapter",
    "ReadonlyGatewayClient",
    "ReadonlyGatewayResult",
    "ReadonlyGatewayRuntimeConfig",
    "StrategyAdapter",
    "StrategyPackage",
    "StrategyPackageAdapter",
    "TargetPortfolioSnapshot",
    "adapt_strategy_payload",
    "build_evidence_summary",
    "load_strategy_package",
    "resolve_active_package",
    "write_evidence_summary",
    "zero_cr091_operation_counters",
)
