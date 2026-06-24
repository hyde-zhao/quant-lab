"""CR128 offline strategy runner orchestration."""

from __future__ import annotations

from pathlib import Path

from trading.strategy_runner.adapters import adapt_strategy_payload
from trading.strategy_runner.artifact_bundle import write_run_artifact_bundle
from trading.strategy_runner.evidence import EvidenceRedactionError, build_evidence_summary
from trading.strategy_runner.evidence_index import write_run_evidence_index
from trading.strategy_runner.package_loader import PackageLoaderError, load_strategy_package
from trading.strategy_runner.readonly_gateway import ReadonlyGatewayClient
from trading.strategy_runner.run_registry import append_run_registry_from_result
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
    if output_validated and result.passed and spec.evidence_index_output_path is not None:
        write_run_evidence_index(
            spec.evidence_index_output_path,
            result,
            run_result_path=spec.output_path,
        )
    if output_validated and result.passed and spec.bundle_output_path is not None:
        write_run_artifact_bundle(spec.bundle_output_path, spec=spec, result=result)
    if output_validated and spec.run_registry_output_path is not None:
        append_run_registry_from_result(
            spec.run_registry_output_path,
            result,
            bundle_dir=spec.bundle_output_path if result.passed else None,
        )
    return result


def run_strategy_package_from_path(
    package_root: str | Path,
    *,
    run_id: str,
    output_path: str | Path | None = None,
    evidence_index_output_path: str | Path | None = None,
    bundle_output_path: str | Path | None = None,
    run_registry_output_path: str | Path | None = None,
) -> RunResult:
    return run_strategy_package(
        RunSpec.from_package_root(
            package_root,
            run_id=run_id,
            output_path=output_path,
            evidence_index_output_path=evidence_index_output_path,
            bundle_output_path=bundle_output_path,
            run_registry_output_path=run_registry_output_path,
        )
    )


def run_strategy_package_from_spec_file(spec_path: str | Path) -> RunResult:
    return run_strategy_package(RunSpec.from_file(spec_path))
