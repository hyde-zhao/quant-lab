"""市场数据源 exact registry。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .contracts import (
    DATASET_ADJ_FACTOR,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_EVENTS,
    DATASET_PRICES_LIMIT,
    DATASET_PRICES,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    INTERFACE_TRADE_CALENDAR_DAILY,
    SOURCE_AKSHARE,
    SOURCE_FAKE,
    SOURCE_JQDATA,
    SOURCE_STATUS_DISABLED,
    SOURCE_STATUS_RESOLVED,
    SOURCE_STATUS_UNRESOLVED,
    SOURCE_TICKFLOW,
    SOURCE_TUSHARE,
)


class SourceRegistryError(ValueError):
    """source 或 interface 不满足 exact registry 契约。"""

    def __init__(
        self,
        message: str,
        *,
        source: str,
        interface: str | None = None,
        error_type: str,
        source_status: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.source = source
        self.interface = interface
        self.error_type = error_type
        self.source_status = source_status
        self.retryable = retryable

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "interface": self.interface,
            "error_type": self.error_type,
            "source_status": self.source_status,
            "retryable": self.retryable,
            "error_message": str(self),
        }


@dataclass(frozen=True, slots=True)
class InterfaceSpec:
    name: str
    target_dataset: str
    provider_method: str | None = None
    category: str = "market"
    pit_required: bool = False
    adjustment_required: bool = False


@dataclass(frozen=True, slots=True)
class SourceSpec:
    name: str
    status: str
    interfaces: tuple[InterfaceSpec, ...]
    credential_env_vars: tuple[str, ...] = ()

    @property
    def interface_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.interfaces)


SOURCE_REGISTRY: dict[str, SourceSpec] = {
    SOURCE_FAKE: SourceSpec(
        name=SOURCE_FAKE,
        status=SOURCE_STATUS_RESOLVED,
        interfaces=(
            InterfaceSpec(INTERFACE_PRICES_DAILY, DATASET_PRICES),
            InterfaceSpec(INTERFACE_INDEX_MEMBERS_SNAPSHOT, DATASET_INDEX_MEMBERS),
            InterfaceSpec(INTERFACE_INDEX_WEIGHTS_SNAPSHOT, DATASET_INDEX_WEIGHTS),
            InterfaceSpec(INTERFACE_STOCK_BASIC_SNAPSHOT, DATASET_STOCK_BASIC),
            InterfaceSpec(INTERFACE_TRADE_CALENDAR_DAILY, DATASET_TRADE_CALENDAR, "trade_cal", "calendar"),
        ),
    ),
    SOURCE_AKSHARE: SourceSpec(
        name=SOURCE_AKSHARE,
        status=SOURCE_STATUS_DISABLED,
        interfaces=(InterfaceSpec(INTERFACE_PRICES_DAILY, DATASET_PRICES),),
    ),
    SOURCE_TUSHARE: SourceSpec(
        name=SOURCE_TUSHARE,
        status=SOURCE_STATUS_DISABLED,
        interfaces=(
            InterfaceSpec(INTERFACE_PRICES_DAILY, DATASET_PRICES, "daily", "market", adjustment_required=True),
            InterfaceSpec(INTERFACE_PRICES_ADJ_FACTOR, DATASET_ADJ_FACTOR, "adj_factor", "market", adjustment_required=True),
            InterfaceSpec(INTERFACE_HS300_INDEX_DAILY, DATASET_HS300_INDEX, "index_daily", "benchmark"),
            InterfaceSpec(INTERFACE_TRADE_CALENDAR_DAILY, DATASET_TRADE_CALENDAR, "trade_cal", "calendar"),
            InterfaceSpec(INTERFACE_INDEX_MEMBERS_SNAPSHOT, DATASET_INDEX_MEMBERS, "index_weight", "non_market", pit_required=True),
            InterfaceSpec(INTERFACE_INDEX_WEIGHTS_SNAPSHOT, DATASET_INDEX_WEIGHTS, "index_weight", "non_market", pit_required=True),
            InterfaceSpec(INTERFACE_STOCK_BASIC_SNAPSHOT, DATASET_STOCK_BASIC, "stock_basic", "non_market", pit_required=True),
            InterfaceSpec(INTERFACE_TRADE_STATUS_DAILY, DATASET_TRADE_STATUS, "suspend_d+stock_st+daily", "market"),
            InterfaceSpec(INTERFACE_PRICES_LIMIT_DAILY, DATASET_PRICES_LIMIT, "stk_limit", "market"),
            InterfaceSpec(INTERFACE_EVENTS_DISCLOSURE, DATASET_EVENTS, "stock_st", "events"),
        ),
        credential_env_vars=("TUSHARE_TOKEN",),
    ),
    SOURCE_JQDATA: SourceSpec(
        name=SOURCE_JQDATA,
        status=SOURCE_STATUS_DISABLED,
        interfaces=(
            InterfaceSpec(
                INTERFACE_INDEX_MEMBERS_SNAPSHOT,
                DATASET_INDEX_MEMBERS,
                "get_index_stocks",
                "non_market",
                pit_required=True,
            ),
            InterfaceSpec(
                INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                DATASET_INDEX_WEIGHTS,
                "get_index_weights",
                "non_market",
                pit_required=True,
            ),
            InterfaceSpec(
                INTERFACE_STOCK_BASIC_SNAPSHOT,
                DATASET_STOCK_BASIC,
                "get_all_securities",
                "non_market",
                pit_required=True,
            ),
            InterfaceSpec(
                INTERFACE_TRADE_STATUS_DAILY,
                DATASET_TRADE_STATUS,
                "get_price+get_extras",
                "market",
            ),
            InterfaceSpec(
                INTERFACE_PRICES_LIMIT_DAILY,
                DATASET_PRICES_LIMIT,
                "get_price",
                "market",
            ),
            InterfaceSpec(
                INTERFACE_EVENTS_DISCLOSURE,
                DATASET_EVENTS,
                "get_extras",
                "events",
            ),
        ),
        credential_env_vars=("JQDATA_USERNAME", "JQDATA_PASSWORD"),
    ),
    SOURCE_TICKFLOW: SourceSpec(
        name=SOURCE_TICKFLOW,
        status=SOURCE_STATUS_UNRESOLVED,
        interfaces=(),
        credential_env_vars=("TICKFLOW_TOKEN", "TICKFLOW_ENDPOINT"),
    ),
}


def _config_for_source(config: object, source: str) -> Mapping[str, object] | None:
    if config is None:
        return None
    sources = getattr(config, "sources", None)
    if isinstance(sources, Mapping):
        value = sources.get(source)
        if isinstance(value, Mapping):
            return value
        if value is not None:
            return {
                "enabled": getattr(value, "enabled", False),
                "allow_interfaces": getattr(value, "allow_interfaces", ()),
            }
    return None


def resolve_source(source: str, config: object = None) -> SourceSpec:
    spec = SOURCE_REGISTRY.get(source)
    if spec is None:
        raise SourceRegistryError(
            f"未知数据源: {source}",
            source=source,
            error_type="source_unresolved",
            source_status=SOURCE_STATUS_UNRESOLVED,
        )
    if spec.status == SOURCE_STATUS_RESOLVED:
        return spec
    source_config = _config_for_source(config, source)
    enabled = bool(source_config and source_config.get("enabled"))
    if spec.status == SOURCE_STATUS_UNRESOLVED:
        raise SourceRegistryError(
            f"数据源接口未确认: {source}",
            source=source,
            error_type="source_unresolved",
            source_status=spec.status,
        )
    if not enabled:
        raise SourceRegistryError(
            f"数据源未启用: {source}",
            source=source,
            error_type="source_disabled",
            source_status=spec.status,
        )
    return spec


def resolve_interface(
    source: str,
    interface: str,
    config: object = None,
) -> InterfaceSpec:
    spec = resolve_source(source, config=config)
    source_config = _config_for_source(config, source)
    configured_allow = tuple(source_config.get("allow_interfaces", ()) if source_config else ())
    if configured_allow and interface not in configured_allow:
        raise SourceRegistryError(
            f"接口未在数据源 allowlist 中: {source}.{interface}",
            source=source,
            interface=interface,
            error_type="interface_not_allowed",
            source_status=spec.status,
        )
    for item in spec.interfaces:
        if item.name == interface:
            return item
    raise SourceRegistryError(
        f"接口未在数据源 allowlist 中: {source}.{interface}",
        source=source,
        interface=interface,
        error_type="interface_not_allowed",
        source_status=spec.status,
    )


__all__ = [
    "InterfaceSpec",
    "SourceSpec",
    "SOURCE_REGISTRY",
    "SourceRegistryError",
    "resolve_source",
    "resolve_interface",
]
