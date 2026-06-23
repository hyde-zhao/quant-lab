"""CR128 offline strategy runner orchestration."""

from __future__ import annotations

from pathlib import Path

from trading.strategy_runner.adapters import adapt_strategy_payload
from trading.strategy_runner.evidence import EvidenceRedactionError, build_evidence_summary
from trading.strategy_runner.package_loader import PackageLoaderError, load_strategy_package
from trading.strategy_runner.readonly_gateway import ReadonlyGatewayClient
from trading.strategy_runner.result import RunResult, write_run_result
from trading.strategy_runner.run_spec import RunSpec, RunSpecError


def run_strategy_package(spec: RunSpec) -> RunResult:
    """Run one strategy package through the offline runner core."""

    output_validated = False
    try:
        spec.validate()
        output_validated = True
        package = load_strategy_package(spec.package_root)
        adapter_payload = package.to_adapter_payload()
        adapter_result = adapt_strategy_payload(adapter_payload, run_id=spec.run_id)
        readonly_result = (
            ReadonlyGatewayClient().query_positions(run_id=spec.run_id)
            if spec.include_fake_readonly
            else None
        )
        evidence = build_evidence_summary(
            run_id=spec.run_id,
            package_id=package.package_id,
            adapter_type=str(package.manifest.get("adapter_type")),
            adapter_result=adapter_result,
            readonly_result=readonly_result,
        )
        result = RunResult.from_adapter_and_evidence(
            run_id=spec.run_id,
            package_id=package.package_id,
            adapter_result=adapter_result,
            evidence=evidence,
        )
    except (RunSpecError, PackageLoaderError, EvidenceRedactionError, ValueError) as exc:
        result = RunResult.blocked(run_id=spec.run_id, reason=str(exc))
    if output_validated and spec.output_path is not None:
        write_run_result(spec.output_path, result)
    return result


def run_strategy_package_from_path(
    package_root: str | Path,
    *,
    run_id: str,
    output_path: str | Path | None = None,
) -> RunResult:
    return run_strategy_package(
        RunSpec.from_package_root(package_root, run_id=run_id, output_path=output_path)
    )
