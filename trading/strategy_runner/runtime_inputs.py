"""交易窗口私有 runtime 输入构建。

本模块只负责在授权窗口内把离线 fixture 包映射为私有 runtime 输入；
调用方必须把输出写到私有 runtime 目录，不得写入仓库 `process/`。
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping


RUNTIME_INPUTS_SCHEMA_VERSION = "runner-multifactor-runtime-inputs-v1"
RUNTIME_OVERLAY_SCHEMA_VERSION = "runner-multifactor-runtime-overlay-v1"


@dataclass(frozen=True, slots=True)
class RuntimeInputs:
    spec: dict[str, object]
    admission_package: dict[str, object]
    symbol_count: int
    schema_version: str = RUNTIME_INPUTS_SCHEMA_VERSION

    def to_summary(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.spec.get("run_id", ""),
            "authorization_ref": self.spec.get("authorization_ref", ""),
            "expected_runtime_profile": self.spec.get("expected_runtime_profile", ""),
            "symbol_count": self.symbol_count,
            "current_position_count": len(_mapping(self.spec.get("current_positions"))),
            "risk_position_count": len(
                _mapping(_mapping(self.spec.get("risk_snapshot")).get("positions_available"))
            ),
            "raw_symbols_printed": False,
        }


def build_runtime_inputs(
    *,
    base_spec: Mapping[str, object],
    admission_package: Mapping[str, object],
    overlay: Mapping[str, object],
    readonly_evidence_ref: str,
    run_id: str,
    authorization_ref: str,
    expected_runtime_profile: str,
) -> RuntimeInputs:
    """把 formal fixture 输入和私有 overlay 合成为交易窗口 runtime 输入。"""

    symbol_map = _symbol_map(overlay)
    if not symbol_map:
        raise ValueError("symbol_map_missing")
    if not run_id:
        raise ValueError("run_id_missing")
    if not authorization_ref:
        raise ValueError("authorization_ref_missing")
    if not expected_runtime_profile:
        raise ValueError("expected_runtime_profile_missing")

    runtime_admission = _remap_admission(admission_package, symbol_map)
    runtime_spec = _remap_spec(base_spec, symbol_map)
    runtime_spec.update(
        {
            "run_id": run_id,
            "authorization_ref": authorization_ref,
            "expected_runtime_profile": expected_runtime_profile,
            "runtime_positions_summary_ref": readonly_evidence_ref,
        }
    )
    if "current_positions" in overlay:
        runtime_spec["current_positions"] = _mapping(overlay["current_positions"])
    if "risk_snapshot" in overlay:
        runtime_spec["risk_snapshot"] = _mapping(overlay["risk_snapshot"])
    if "risk_profile" in overlay:
        runtime_spec["risk_profile"] = _mapping(overlay["risk_profile"])
    if "capital_base" in overlay:
        runtime_spec["capital_base"] = overlay["capital_base"]
    if "max_turnover_notional" in overlay:
        runtime_spec["max_turnover_notional"] = overlay["max_turnover_notional"]

    runtime_spec["strategy_admission_package"] = runtime_admission
    runtime_spec["stability_evidence_refs"] = _stability_evidence_refs(
        overlay,
        readonly_evidence_ref,
    )

    _validate_no_non_runtime_symbols(runtime_spec, runtime_admission)
    return RuntimeInputs(
        spec=dict(runtime_spec),
        admission_package=dict(runtime_admission),
        symbol_count=len(set(symbol_map.values())),
    )


def write_runtime_inputs(
    inputs: RuntimeInputs,
    *,
    output_dir: str | Path,
    run_id: str,
) -> tuple[Path, Path]:
    """写入私有 runtime spec 与 admission package。"""

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    spec_path = target_dir / f"{run_id}-runtime-spec.json"
    admission_path = target_dir / f"{run_id}-runtime-admission-package.json"
    spec_path.write_text(
        json.dumps(inputs.spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    admission_path.write_text(
        json.dumps(inputs.admission_package, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return spec_path, admission_path


def _remap_admission(
    admission_package: Mapping[str, object],
    symbol_map: Mapping[str, str],
) -> dict[str, object]:
    payload = deepcopy(dict(admission_package))
    for candidate in _sequence(payload.get("strategy_candidates")):
        if not isinstance(candidate, dict):
            continue
        candidate["target_symbols"] = [
            _map_symbol(str(symbol), symbol_map)
            for symbol in _sequence(candidate.get("target_symbols"))
        ]
    for row in _sequence(payload.get("strategy_scores")):
        if isinstance(row, dict) and "symbol" in row:
            row["symbol"] = _map_symbol(str(row["symbol"]), symbol_map)
    refs = _mapping(payload.get("input_refs"))
    refs["runtime_symbol_overlay"] = "private-runtime-overlay"
    payload["input_refs"] = refs
    payload["not_authorization"] = True
    payload["not_qmt_authorization"] = True
    payload["not_simulation_authorization"] = True
    payload["not_live_authorization"] = True
    payload["not_broker_order"] = True
    return payload


def _remap_spec(
    base_spec: Mapping[str, object],
    symbol_map: Mapping[str, str],
) -> dict[str, object]:
    spec = deepcopy(dict(base_spec))
    if "signal_rows" in spec:
        spec["signal_rows"] = [
            _remap_symbol_row(row, symbol_map) for row in _sequence(spec.get("signal_rows"))
        ]
    spec["current_positions"] = _remap_symbol_mapping(
        _mapping(spec.get("current_positions")), symbol_map
    )
    risk = _mapping(spec.get("risk_snapshot"))
    risk["positions_available"] = _remap_symbol_mapping(
        _mapping(risk.get("positions_available")), symbol_map
    )
    risk["t1_sellable"] = _remap_symbol_mapping(_mapping(risk.get("t1_sellable")), symbol_map)
    risk["raw_price_refs"] = _remap_symbol_mapping(
        _mapping(risk.get("raw_price_refs")), symbol_map
    )
    spec["risk_snapshot"] = risk
    return spec


def _remap_symbol_row(row: object, symbol_map: Mapping[str, str]) -> dict[str, object]:
    payload = dict(row) if isinstance(row, Mapping) else {}
    if "symbol" in payload:
        payload["symbol"] = _map_symbol(str(payload["symbol"]), symbol_map)
    return payload


def _remap_symbol_mapping(
    values: Mapping[str, object],
    symbol_map: Mapping[str, str],
) -> dict[str, object]:
    return {_map_symbol(str(key), symbol_map): value for key, value in values.items()}


def _map_symbol(symbol: str, symbol_map: Mapping[str, str]) -> str:
    mapped = symbol_map.get(symbol, symbol)
    if _is_non_runtime_symbol(mapped):
        raise ValueError("runtime_symbol_unmapped:" + symbol)
    return mapped


def _symbol_map(overlay: Mapping[str, object]) -> dict[str, str]:
    raw = _mapping(overlay.get("symbol_map"))
    return {str(key): str(value) for key, value in raw.items() if str(key) and str(value)}


def _stability_evidence_refs(
    overlay: Mapping[str, object],
    readonly_evidence_ref: str,
) -> list[str]:
    del readonly_evidence_ref
    refs = [
        str(item)
        for item in _sequence(overlay.get("stability_evidence_refs"))
        if str(item)
    ]
    return refs


def _validate_no_non_runtime_symbols(
    spec: Mapping[str, object],
    admission_package: Mapping[str, object],
) -> None:
    symbols: list[str] = []
    symbols.extend(str(key) for key in _mapping(spec.get("current_positions")))
    risk = _mapping(spec.get("risk_snapshot"))
    symbols.extend(str(key) for key in _mapping(risk.get("positions_available")))
    symbols.extend(str(key) for key in _mapping(risk.get("t1_sellable")))
    symbols.extend(str(key) for key in _mapping(risk.get("raw_price_refs")))
    for row in _sequence(spec.get("signal_rows")):
        if isinstance(row, Mapping):
            symbols.append(str(row.get("symbol") or ""))
    for candidate in _sequence(admission_package.get("strategy_candidates")):
        if isinstance(candidate, Mapping):
            symbols.extend(str(item) for item in _sequence(candidate.get("target_symbols")))
    for row in _sequence(admission_package.get("strategy_scores")):
        if isinstance(row, Mapping):
            symbols.append(str(row.get("symbol") or ""))
    blocked = sorted({symbol for symbol in symbols if _is_non_runtime_symbol(symbol)})
    if blocked:
        raise ValueError("runtime_symbol_contract_invalid:" + ",".join(blocked))


def _is_non_runtime_symbol(symbol: str) -> bool:
    normalized = symbol.strip()
    upper = normalized.upper()
    lower = normalized.lower()
    return (
        upper.startswith("INSTRUMENT_")
        or "FIXTURE" in upper
        or lower.startswith(("instrument:", "symbol:", "fixture:"))
    )


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []
