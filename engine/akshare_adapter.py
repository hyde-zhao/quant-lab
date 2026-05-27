"""AKShare 调用边界与 fake adapter 兼容协议。

真实 AKShare 导入只允许发生在本文件内。测试应注入 fake adapter，不需要也不应
调用真实网络接口。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Protocol, runtime_checkable


_INTERFACE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(slots=True)
class AdapterError:
    error_type: str
    error_message: str
    retryable: bool = True
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "retryable": self.retryable,
            "details": self.details,
        }


@dataclass(slots=True)
class AdapterResult:
    data: Any
    success_items: list[Any] = field(default_factory=list)
    failed_items: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return True

    @property
    def partial_success(self) -> bool:
        return bool(self.failed_items)


@runtime_checkable
class AdapterProtocol(Protocol):
    def fetch(self, interface: str, params: dict[str, Any]) -> AdapterResult | AdapterError:
        """获取接口原始响应。"""


class AkshareAdapter:
    """显式数据准备流程使用的 AKShare adapter。"""

    def __init__(
        self,
        allowed_interfaces: set[str] | tuple[str, ...] | list[str] | None = None,
        interface_mapping: dict[str, str] | None = None,
    ) -> None:
        self.allowed_interfaces = set(allowed_interfaces or ())
        self.interface_mapping = dict(interface_mapping or {})

    def fetch(self, interface: str, params: dict[str, Any]) -> AdapterResult | AdapterError:
        """调用 AKShare 接口并返回结构化结果。"""

        validation_error = self._validate_interface(interface)
        if validation_error is not None:
            return validation_error

        akshare_name = self.interface_mapping.get(interface, interface)
        try:
            import akshare as ak  # noqa: PLC0415
        except Exception as exc:  # pragma: no cover - 依赖缺失只在真实 adapter 路径触发
            return AdapterError(
                error_type="AkshareImportError",
                error_message=str(exc),
                retryable=False,
            )

        func = getattr(ak, akshare_name, None)
        if func is None or not callable(func):
            return AdapterError(
                error_type="AkshareInterfaceNotFound",
                error_message=f"AKShare 接口不存在或不可调用: {akshare_name}",
                retryable=False,
            )

        try:
            data = func(**dict(params))
        except Exception as exc:  # pragma: no cover - 真实网络路径不作为单测默认入口
            return AdapterError(
                error_type=type(exc).__name__,
                error_message=str(exc),
                retryable=True,
            )
        return AdapterResult(data=data)

    def _validate_interface(self, interface: str) -> AdapterError | None:
        if not isinstance(interface, str) or not interface:
            return AdapterError(
                error_type="InvalidInterfaceName",
                error_message="AKShare interface 必须是非空字符串",
                retryable=False,
            )
        if not _INTERFACE_RE.match(interface):
            return AdapterError(
                error_type="InvalidInterfaceName",
                error_message=f"AKShare interface 含非法字符: {interface}",
                retryable=False,
            )
        if self.allowed_interfaces and interface not in self.allowed_interfaces:
            return AdapterError(
                error_type="InterfaceNotAllowed",
                error_message=f"AKShare interface 未在允许列表中: {interface}",
                retryable=False,
            )
        mapped = self.interface_mapping.get(interface, interface)
        if not _INTERFACE_RE.match(mapped):
            return AdapterError(
                error_type="InvalidInterfaceName",
                error_message=f"AKShare 映射接口含非法字符: {mapped}",
                retryable=False,
            )
        return None


__all__ = (
    "AdapterError",
    "AdapterProtocol",
    "AdapterResult",
    "AkshareAdapter",
)
