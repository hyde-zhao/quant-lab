"""本地数据 source/interface 精确注册表。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


UNRESOLVED = "UNRESOLVED"


class SourceRegistryError(ValueError):
    """source/interface 未解析或不匹配。"""


@dataclass(frozen=True, slots=True)
class SourceInterfaceSpec:
    dataset: str
    source: str
    interface: str
    enabled_path: str
    resolved: bool = True


SOURCE_INTERFACE_REGISTRY: dict[str, SourceInterfaceSpec] = {
    "prices": SourceInterfaceSpec(
        dataset="prices",
        source="akshare",
        interface="stock_zh_a_hist",
        enabled_path="prices",
    ),
    "trade_calendar": SourceInterfaceSpec(
        dataset="trade_calendar",
        source="akshare",
        interface="tool_trade_date_hist_sina",
        enabled_path="trade_calendar",
    ),
    "index_members_fixed": SourceInterfaceSpec(
        dataset="index_members",
        source="akshare",
        interface="index_stock_cons",
        enabled_path="fixed_universe",
    ),
    "index_members_pit": SourceInterfaceSpec(
        dataset="index_members",
        source="tushare",
        interface="index_weight",
        enabled_path="pit_universe",
    ),
    "trade_status": SourceInterfaceSpec(
        dataset="trade_status",
        source="tushare",
        interface="suspend_d+stock_st+daily",
        enabled_path="trade_status",
    ),
    "prices_limit": SourceInterfaceSpec(
        dataset="prices_limit",
        source="tushare",
        interface="stk_limit",
        enabled_path="limit_prices",
    ),
    "events": SourceInterfaceSpec(
        dataset="events",
        source="tushare",
        interface="stock_st",
        enabled_path="events",
    ),
}


def require_resolved_registry_key(key: str) -> SourceInterfaceSpec:
    """返回已解析注册项；未解析时 fail fast。"""

    spec = SOURCE_INTERFACE_REGISTRY.get(key)
    if spec is None:
        raise SourceRegistryError(f"未知 source/interface registry key: {key}")
    if not spec.resolved or spec.source == UNRESOLVED or spec.interface == UNRESOLVED:
        raise SourceRegistryError(
            f"source/interface 未解析: key={key}, source={spec.source}, "
            f"interface={spec.interface}, enabled_path={spec.enabled_path}"
        )
    return spec


def validate_exact_source_interface(
    source: str,
    interface: str,
    params: dict[str, Any] | None = None,
) -> None:
    """按显式注册表校验 source/interface，禁止模糊匹配。"""

    key = registry_key_for_request(source, interface, params or {})
    if key:
        spec = require_resolved_registry_key(key)
        if source != spec.source or interface != spec.interface:
            raise SourceRegistryError(
                f"source/interface 不匹配: expected={spec.source}/{spec.interface}, "
                f"actual={source}/{interface}"
            )


def registry_key_for_request(
    source: str,
    interface: str,
    params: dict[str, Any],
) -> str:
    """从请求推导注册项；未知组合直接失败，避免隐式模糊路由。"""

    target_dataset = str(params.get("target_dataset") or "")
    if target_dataset == "index_members":
        if bool(params.get("is_pit_universe") or params.get("pit_universe")):
            return "index_members_pit"
        return "index_members_fixed"
    if target_dataset in {"trade_status", "prices_limit", "events"}:
        return target_dataset

    exact_pairs = {
        ("akshare", "stock_zh_a_hist"): "prices",
        ("akshare", "tool_trade_date_hist_sina"): "trade_calendar",
        ("akshare", "index_stock_cons"): "index_members_fixed",
        ("tushare", "index_weight"): "index_members_pit",
        ("tushare", "suspend_d+stock_st+daily"): "trade_status",
        ("tushare", "stk_limit"): "prices_limit",
        ("tushare", "stock_st"): "events",
        (UNRESOLVED, UNRESOLVED): str(params.get("registry_key") or ""),
    }
    key = exact_pairs.get((source, interface), "")
    if key:
        return key
    raise SourceRegistryError(f"未注册 source/interface: source={source}, interface={interface}")


__all__ = (
    "SOURCE_INTERFACE_REGISTRY",
    "SourceInterfaceSpec",
    "SourceRegistryError",
    "UNRESOLVED",
    "registry_key_for_request",
    "require_resolved_registry_key",
    "validate_exact_source_interface",
)
