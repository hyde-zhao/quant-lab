"""CR015-S01 的 QMT foundation 环境边界合同。

本模块刻意保持离线：只暴露枚举和 dataclass 合同，用于描述研究节点或
交易节点是否可使用 mock/shadow 接口；不得探测本地进程、凭据或 broker SDK。
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping


class NodeRole(str, Enum):
    """当前节点的执行角色。"""

    RESEARCH = "research"
    TRADING = "trading"


class AdapterMode(str, Enum):
    """QMT foundation 合同识别的 adapter 模式。"""

    SHADOW = "shadow"
    DRY_RUN = "dry_run"
    MOCK = "mock"
    SIMULATION = "simulation"
    LIVE_READONLY = "live_readonly"
    SMALL_LIVE = "small_live"


class EnvironmentStatus(str, Enum):
    """环境边界离线评估返回的状态。"""

    UNSUPPORTED = "unsupported"
    RESEARCH_ONLY = "research_only"
    TRADING_NODE_REQUIRED = "trading_node_required"
    MOCK_READY = "mock_ready"
    BLOCKED = "blocked"


class EnvironmentCapability(str, Enum):
    """不触达真实 broker 进程时可暴露的能力。"""

    RESEARCH_PAYLOAD = "research_payload"
    SIGNED_FILE_DROP = "signed_file_drop"
    MOCK_ADAPTER = "mock_adapter"
    TRADING_NODE_REQUIRED = "trading_node_required"
    REAL_QMT_FORBIDDEN = "real_qmt_forbidden"


class EnvironmentErrorCode(str, Enum):
    """环境边界的结构化错误码。"""

    UNSUPPORTED_NODE_ROLE = "unsupported_node_role"
    UNSUPPORTED_ADAPTER_MODE = "unsupported_adapter_mode"
    MODE_NOT_AUTHORIZED = "mode_not_authorized"
    REAL_QMT_BLOCKED = "real_qmt_blocked"
    CREDENTIAL_ACCESS_BLOCKED = "credential_access_blocked"


CR015_ALLOWED_ADAPTER_MODES = frozenset(
    {
        AdapterMode.SHADOW,
        AdapterMode.DRY_RUN,
        AdapterMode.MOCK,
    }
)

REAL_QMT_ADAPTER_MODES = frozenset(
    {
        AdapterMode.SIMULATION,
        AdapterMode.LIVE_READONLY,
        AdapterMode.SMALL_LIVE,
    }
)

QMT_FORBIDDEN_OPERATION_COUNTERS: Mapping[str, int] = {
    "real_qmt_process_invocation": 0,
    "qmt_api_call": 0,
    "real_order": 0,
    "real_cancel": 0,
    "account_query": 0,
    "account_write": 0,
    "credential_read": 0,
    "dependency_change": 0,
    "real_broker_lake_write": 0,
}

FORBIDDEN_BROKER_MODULES = frozenset(
    {
        "xtquant",
        "xtquant.xttrader",
        "xtquant.xtdata",
        "xttrader",
        "xtdata",
    }
)

FORBIDDEN_BROKER_CALLS = frozenset(
    {
        "XtQuantTrader",
        "connect",
        "order_stock",
        "order_stock_async",
        "cancel_order_stock",
        "query_stock_asset",
        "query_stock_orders",
        "query_stock_trades",
        "query_stock_positions",
    }
)

SENSITIVE_PATH_NAMES = frozenset({".env", ".env.local", ".env.production"})


@dataclass(frozen=True)
class ForbiddenOperationCounters:
    """CR015-S01 必须保持为 0 的禁止操作计数。"""

    real_qmt_process_invocation: int = 0
    qmt_api_call: int = 0
    real_order: int = 0
    real_cancel: int = 0
    account_query: int = 0
    account_write: int = 0
    credential_read: int = 0
    dependency_change: int = 0
    real_broker_lake_write: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "real_qmt_process_invocation": self.real_qmt_process_invocation,
            "qmt_api_call": self.qmt_api_call,
            "real_order": self.real_order,
            "real_cancel": self.real_cancel,
            "account_query": self.account_query,
            "account_write": self.account_write,
            "credential_read": self.credential_read,
            "dependency_change": self.dependency_change,
            "real_broker_lake_write": self.real_broker_lake_write,
        }


@dataclass(frozen=True)
class EnvironmentProbeResult:
    """环境边界离线评估结果。"""

    node_role: NodeRole | None
    adapter_mode: AdapterMode | None
    status: EnvironmentStatus
    capabilities: tuple[EnvironmentCapability, ...]
    error_code: EnvironmentErrorCode | None = None
    reason: str = ""
    counters: Mapping[str, int] = field(
        default_factory=lambda: ForbiddenOperationCounters().to_dict()
    )


@dataclass(frozen=True)
class ForbiddenImportViolation:
    """一条禁止 broker import 或直接调用发现。"""

    path: str
    line: int
    kind: str
    symbol: str


@dataclass(frozen=True)
class ForbiddenImportScanResult:
    """直接 broker 访问边界的静态扫描结果。"""

    passed: bool
    checked_paths: tuple[str, ...]
    violations: tuple[ForbiddenImportViolation, ...]
    counters: Mapping[str, int] = field(
        default_factory=lambda: ForbiddenOperationCounters().to_dict()
    )

    @property
    def violation_count(self) -> int:
        return len(self.violations)


def evaluate_environment_boundary(
    node_role: NodeRole | str,
    adapter_mode: AdapterMode | str,
    *,
    qmt_available: bool = False,
) -> EnvironmentProbeResult:
    """在不探测真实 QMT 进程的前提下评估 CR015-S01 边界。"""

    role = _coerce_node_role(node_role)
    mode = _coerce_adapter_mode(adapter_mode)
    counters = ForbiddenOperationCounters().to_dict()

    if role is None:
        return EnvironmentProbeResult(
            node_role=None,
            adapter_mode=mode,
            status=EnvironmentStatus.UNSUPPORTED,
            capabilities=(EnvironmentCapability.REAL_QMT_FORBIDDEN,),
            error_code=EnvironmentErrorCode.UNSUPPORTED_NODE_ROLE,
            reason="unsupported node_role",
            counters=counters,
        )

    if mode is None:
        return EnvironmentProbeResult(
            node_role=role,
            adapter_mode=None,
            status=EnvironmentStatus.UNSUPPORTED,
            capabilities=(EnvironmentCapability.REAL_QMT_FORBIDDEN,),
            error_code=EnvironmentErrorCode.UNSUPPORTED_ADAPTER_MODE,
            reason="unsupported adapter_mode",
            counters=counters,
        )

    if mode in REAL_QMT_ADAPTER_MODES:
        if role is NodeRole.RESEARCH:
            status = EnvironmentStatus.TRADING_NODE_REQUIRED
            reason = "research node cannot use simulation or live adapter modes"
        else:
            status = EnvironmentStatus.BLOCKED
            reason = "CR015-S01 does not authorize real QMT adapter modes"
        return EnvironmentProbeResult(
            node_role=role,
            adapter_mode=mode,
            status=status,
            capabilities=(
                EnvironmentCapability.TRADING_NODE_REQUIRED,
                EnvironmentCapability.REAL_QMT_FORBIDDEN,
            ),
            error_code=(
                EnvironmentErrorCode.REAL_QMT_BLOCKED
                if qmt_available
                else EnvironmentErrorCode.MODE_NOT_AUTHORIZED
            ),
            reason=reason,
            counters=counters,
        )

    if mode not in CR015_ALLOWED_ADAPTER_MODES:
        return EnvironmentProbeResult(
            node_role=role,
            adapter_mode=mode,
            status=EnvironmentStatus.BLOCKED,
            capabilities=(EnvironmentCapability.REAL_QMT_FORBIDDEN,),
            error_code=EnvironmentErrorCode.MODE_NOT_AUTHORIZED,
            reason="adapter mode is not authorized by CR015-S01",
            counters=counters,
        )

    if role is NodeRole.RESEARCH:
        return EnvironmentProbeResult(
            node_role=role,
            adapter_mode=mode,
            status=EnvironmentStatus.RESEARCH_ONLY,
            capabilities=(
                EnvironmentCapability.RESEARCH_PAYLOAD,
                EnvironmentCapability.SIGNED_FILE_DROP,
            ),
            reason="research node may build signed payloads only",
            counters=counters,
        )

    return EnvironmentProbeResult(
        node_role=role,
        adapter_mode=mode,
        status=EnvironmentStatus.MOCK_READY,
        capabilities=(
            EnvironmentCapability.SIGNED_FILE_DROP,
            EnvironmentCapability.MOCK_ADAPTER,
        ),
        reason="trading node may consume mock/shadow file-drop contracts",
        counters=counters,
    )


def assert_no_real_qmt_operations(
    counters: Mapping[str, int] | ForbiddenOperationCounters | None = None,
) -> bool:
    """仅当所有禁止操作计数均为 0 时返回 true。"""

    if counters is None:
        current = ForbiddenOperationCounters().to_dict()
    elif isinstance(counters, ForbiddenOperationCounters):
        current = counters.to_dict()
    else:
        current = dict(counters)
    return all(value == 0 for value in current.values())


def scan_forbidden_broker_imports(paths: Iterable[str | Path]) -> ForbiddenImportScanResult:
    """扫描源码中的直接 broker import 或直接 broker 调用。

    看起来像凭据的路径会在读取内容前被拒绝，因此该 helper 可用于不触碰
    secret 的离线 guardrail。
    """

    checked_paths: list[str] = []
    violations: list[ForbiddenImportViolation] = []

    for raw_path in paths:
        path = Path(raw_path)
        path_label = str(path)
        checked_paths.append(path_label)

        if path.name in SENSITIVE_PATH_NAMES:
            violations.append(
                ForbiddenImportViolation(
                    path=path_label,
                    line=0,
                    kind="credential_path_rejected",
                    symbol=path.name,
                )
            )
            continue

        if not path.exists() or not path.is_file():
            continue

        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source, filename=path_label)
        except SyntaxError as exc:
            violations.append(
                ForbiddenImportViolation(
                    path=path_label,
                    line=exc.lineno or 0,
                    kind="parse_error",
                    symbol="syntax_error",
                )
            )
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden_module(alias.name):
                        violations.append(
                            ForbiddenImportViolation(
                                path=path_label,
                                line=node.lineno,
                                kind="import",
                                symbol=alias.name,
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imported_names = [alias.name for alias in node.names]
                if _is_forbidden_module(module):
                    violations.append(
                        ForbiddenImportViolation(
                            path=path_label,
                            line=node.lineno,
                            kind="from_import",
                            symbol=module,
                            )
                        )
                    continue
                for imported_name in imported_names:
                    full_name = f"{module}.{imported_name}" if module else imported_name
                    if _is_forbidden_module(imported_name) or _is_forbidden_module(full_name):
                        violations.append(
                            ForbiddenImportViolation(
                                path=path_label,
                                line=node.lineno,
                                kind="from_import",
                                symbol=full_name,
                            )
                        )
            elif isinstance(node, ast.Call):
                call_name = _call_name(node)
                if call_name in FORBIDDEN_BROKER_CALLS:
                    violations.append(
                        ForbiddenImportViolation(
                            path=path_label,
                            line=node.lineno,
                            kind="direct_call",
                            symbol=call_name,
                        )
                    )

    return ForbiddenImportScanResult(
        passed=not violations,
        checked_paths=tuple(checked_paths),
        violations=tuple(violations),
        counters=ForbiddenOperationCounters().to_dict(),
    )


def _coerce_node_role(value: NodeRole | str) -> NodeRole | None:
    try:
        return value if isinstance(value, NodeRole) else NodeRole(str(value))
    except ValueError:
        return None


def _coerce_adapter_mode(value: AdapterMode | str) -> AdapterMode | None:
    try:
        return value if isinstance(value, AdapterMode) else AdapterMode(str(value))
    except ValueError:
        return None


def _is_forbidden_module(module_name: str) -> bool:
    return any(
        module_name == forbidden or module_name.startswith(f"{forbidden}.")
        for forbidden in FORBIDDEN_BROKER_MODULES
    )


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""
