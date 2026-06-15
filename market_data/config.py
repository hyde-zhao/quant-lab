"""market_data offline 默认配置。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import (
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_TRADE_CALENDAR_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    SOURCE_AKSHARE,
    SOURCE_FAKE,
    SOURCE_JQDATA,
    SOURCE_TICKFLOW,
    SOURCE_TUSHARE,
)


class MarketDataConfigError(ValueError):
    """market_data 配置不满足安全边界。"""


@dataclass(frozen=True, slots=True)
class RuntimePolicyDefaults:
    max_retries: int = 2
    throttle_seconds: float = 0.0
    backoff_base_seconds: float = 0.0
    backoff_max_seconds: float = 60.0
    circuit_breaker_failure_threshold: int = 3
    circuit_breaker_skipped_status: str = "circuit_open"


@dataclass(frozen=True, slots=True)
class SourceConfig:
    enabled: bool = False
    allow_interfaces: tuple[str, ...] = ()
    credential_env_vars: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MarketDataConfig:
    lake_root: str | None = None
    lake_root_env_var: str = "MARKET_DATA_LAKE_ROOT"
    offline: bool = True
    default_source: str = SOURCE_FAKE
    runtime: RuntimePolicyDefaults = field(default_factory=RuntimePolicyDefaults)
    sources: dict[str, SourceConfig] = field(
        default_factory=lambda: {
            SOURCE_FAKE: SourceConfig(
                enabled=True,
                allow_interfaces=(INTERFACE_PRICES_DAILY,),
            ),
            SOURCE_AKSHARE: SourceConfig(enabled=False),
            SOURCE_TUSHARE: SourceConfig(
                enabled=False,
                allow_interfaces=(
                    INTERFACE_PRICES_DAILY,
                    INTERFACE_PRICES_ADJ_FACTOR,
                    INTERFACE_HS300_INDEX_DAILY,
                    INTERFACE_TRADE_CALENDAR_DAILY,
                    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
                    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                    INTERFACE_STOCK_BASIC_SNAPSHOT,
                    INTERFACE_TRADE_STATUS_DAILY,
                    INTERFACE_PRICES_LIMIT_DAILY,
                    INTERFACE_EVENTS_DISCLOSURE,
                ),
                credential_env_vars=("TUSHARE_TOKEN",),
            ),
            SOURCE_JQDATA: SourceConfig(
                enabled=False,
                allow_interfaces=(
                    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
                    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                    INTERFACE_STOCK_BASIC_SNAPSHOT,
                    INTERFACE_TRADE_STATUS_DAILY,
                    INTERFACE_PRICES_LIMIT_DAILY,
                    INTERFACE_EVENTS_DISCLOSURE,
                ),
                credential_env_vars=("JQDATA_USERNAME", "JQDATA_PASSWORD"),
            ),
            SOURCE_TICKFLOW: SourceConfig(
                enabled=False,
                credential_env_vars=("TICKFLOW_TOKEN", "TICKFLOW_ENDPOINT"),
            ),
        }
    )


DEFAULT_CONFIG = MarketDataConfig()


def validate_real_source_config(config: MarketDataConfig) -> None:
    if not config.offline and config.default_source == SOURCE_FAKE:
        raise MarketDataConfigError("offline=false 时必须显式指定真实 source")
    for source, source_config in config.sources.items():
        if source == SOURCE_FAKE or not source_config.enabled:
            continue
        if not source_config.allow_interfaces:
            raise MarketDataConfigError(f"真实 source 缺少接口 allowlist: {source}")


__all__ = [
    "MarketDataConfig",
    "MarketDataConfigError",
    "RuntimePolicyDefaults",
    "SourceConfig",
    "DEFAULT_CONFIG",
    "validate_real_source_config",
]
