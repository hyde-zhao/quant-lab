"""CR-041 本地 paper simulation CLI。

该入口只接受本地文件输入，默认写 NAS 研究报告目录；不提供
provider fetch、lake write、catalog publish、broker 或 simulation/live 参数。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.research_paths import research_report_path

try:
    from engine.paper_simulation import run_paper_simulation
except ImportError as exc:  # pragma: no cover - 并行 worker 可能尚未落 engine。
    run_paper_simulation = None  # type: ignore[assignment]
    _ENGINE_IMPORT_ERROR = exc
else:
    _ENGINE_IMPORT_ERROR = None


DEFAULT_OUTPUT_ROOT = research_report_path("paper_simulation")
SECTION_ARTIFACTS = {
    "order_intents": "order_intents.json",
    "fills": "fills.json",
    "positions": "positions.json",
    "cash_ledger": "cash_ledger.json",
    "equity_curve": "equity_curve.json",
    "reconciliation": "reconciliation.json",
    "forbidden_operation_counters": "forbidden_operation_counters.json",
    "run_manifest": "run_manifest.json",
}
FORBIDDEN_OPERATION_NAMES = (
    "provider_fetch",
    "lake_write",
    "catalog_publish",
    "broker",
    "simulation_live",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="运行 CR-041 API-less 本地 paper simulation，并写出 JSON 报告 artifacts。",
    )
    parser.add_argument(
        "--strategy-package",
        "--admission-package",
        dest="strategy_package",
        required=True,
        help="本地策略准入包 JSON 文件路径；--admission-package 为 LLD 兼容别名。",
    )
    parser.add_argument(
        "--target-portfolio",
        required=True,
        help="本地目标组合文件路径。",
    )
    parser.add_argument(
        "--market-data",
        required=True,
        help="本地行情数据文件路径。",
    )
    parser.add_argument(
        "--initial-cash",
        type=float,
        required=True,
        help="初始现金金额，必须为正数。",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="可复跑 run id；使用 --output-root 时会作为子目录名。",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="最终 artifacts 输出目录。优先级高于 --output-root。",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="输出根目录；未指定 --output-dir 时写入 <output-root>/<run-id>。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖目标输出目录中的同名 artifact 文件。",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        result = run_from_args(args)
    except SystemExit:
        raise
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2

    print(json.dumps({"ok": True, **result}, ensure_ascii=False, sort_keys=True))
    return 0


def run_from_args(args: argparse.Namespace) -> dict[str, Any]:
    strategy_package = _existing_file(args.strategy_package, "--strategy-package")
    target_portfolio = _existing_file(args.target_portfolio, "--target-portfolio")
    market_data = _existing_file(args.market_data, "--market-data")
    initial_cash = _positive_finite_number(args.initial_cash, "--initial-cash")
    run_id = args.run_id.strip() or "paper-simulation-run"
    output_dir = _resolve_output_dir(args.output_dir, args.output_root, run_id)
    _prepare_output_dir(output_dir, overwrite=args.overwrite)

    config = build_engine_config(
        strategy_package=strategy_package,
        target_portfolio=target_portfolio,
        market_data=market_data,
        initial_cash=initial_cash,
        run_id=run_id,
        output_dir=output_dir,
    )
    result = call_engine(config)
    artifacts = write_paper_simulation_artifacts(result, output_dir=output_dir, overwrite=True)
    return {
        "run_id": run_id,
        "output_dir": str(output_dir),
        "artifacts": {key: str(path) for key, path in artifacts.items()},
    }


def build_engine_config(
    *,
    strategy_package: Path,
    target_portfolio: Path,
    market_data: Path,
    initial_cash: float,
    run_id: str,
    output_dir: Path,
) -> dict[str, Any]:
    input_paths = {
        "strategy_package": strategy_package,
        "admission_package": strategy_package,
        "target_portfolio": target_portfolio,
        "market_data": market_data,
    }
    return {
        "run_id": run_id,
        "strategy_package_path": str(strategy_package),
        "admission_package_path": str(strategy_package),
        "target_portfolio_path": str(target_portfolio),
        "market_data_path": str(market_data),
        "initial_cash": initial_cash,
        "output_dir": str(output_dir),
        "inputs": {key: str(path) for key, path in input_paths.items()},
        "input_hashes": {key: _sha256_file(path) for key, path in input_paths.items()},
        "offline_only": True,
        "not_authorization": True,
        "forbidden_operations": {
            "provider_fetch": False,
            "lake_write": False,
            "catalog_publish": False,
            "broker": False,
            "simulation_live": False,
        },
    }


def call_engine(config: Mapping[str, Any]) -> Mapping[str, Any]:
    if run_paper_simulation is None:
        raise RuntimeError(f"engine.paper_simulation.run_paper_simulation 不可用：{_ENGINE_IMPORT_ERROR}")
    result = run_paper_simulation(dict(config))
    return _as_mapping(result, "run_paper_simulation result")


def write_paper_simulation_artifacts(
    result: Mapping[str, Any] | Any,
    *,
    output_dir: Path,
    overwrite: bool = False,
) -> dict[str, Path]:
    result_mapping = _as_mapping(result, "paper simulation result")
    _prepare_output_dir(output_dir, overwrite=overwrite)
    _assert_forbidden_counters_zero(result_mapping)

    artifacts: dict[str, Path] = {}
    summary_payload = result_mapping.get("summary", result_mapping)
    artifacts["paper_simulation_summary"] = _write_json(
        output_dir / "paper_simulation_summary.json",
        summary_payload,
    )
    artifacts["paper_simulation_report"] = _write_json(
        output_dir / "PAPER-SIMULATION-REPORT.json",
        result_mapping,
    )

    for key, filename in SECTION_ARTIFACTS.items():
        if key in result_mapping:
            artifacts[key] = _write_json(output_dir / filename, result_mapping[key])

    artifacts["artifact_index"] = _write_json(
        output_dir / "paper_simulation_artifacts.json",
        {
            "artifact_paths": {key: str(path) for key, path in artifacts.items()},
            "not_authorization": True,
            "forbidden_operation_names": list(FORBIDDEN_OPERATION_NAMES),
        },
    )
    return artifacts


def _existing_file(raw_path: str, option_name: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"{option_name} 必须指向已存在的本地文件：{path}")
    return path


def _positive_finite_number(value: float, option_name: str) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{option_name} 必须为正数：{value}")
    return value


def _resolve_output_dir(raw_output_dir: str, raw_output_root: str, run_id: str) -> Path:
    if raw_output_dir:
        return Path(raw_output_dir).expanduser()
    return Path(raw_output_root).expanduser() / run_id


def _prepare_output_dir(output_dir: Path, *, overwrite: bool) -> None:
    if output_dir.exists() and not output_dir.is_dir():
        raise FileExistsError(f"输出路径已存在且不是目录：{output_dir}")
    if output_dir.exists() and not overwrite and any(output_dir.iterdir()):
        raise FileExistsError(f"输出目录已存在且非空；如需覆盖同名 artifact，请显式传入 --overwrite：{output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        mapped = to_dict()
        if isinstance(mapped, Mapping):
            return mapped
    raise TypeError(f"{label} 必须是 JSON-safe mapping 或提供 to_dict() mapping")


def _assert_forbidden_counters_zero(result: Mapping[str, Any]) -> None:
    counters = result.get("forbidden_operation_counters")
    if counters is None:
        counters = result.get("forbidden_operation_counts")
    if counters is None:
        counters = result.get("operation_counts")
    if counters is None:
        return
    counter_mapping = _as_mapping(counters, "forbidden operation counters")
    non_zero = {
        key: value
        for key, value in counter_mapping.items()
        if isinstance(value, (int, float)) and value != 0
    }
    if non_zero:
        raise RuntimeError(f"检测到禁止操作计数非 0，已拒绝写出 artifacts：{non_zero}")


def _write_json(path: Path, payload: Any) -> Path:
    json_text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=isinstance(payload, Mapping))
    path.write_text(json_text + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
