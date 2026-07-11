#!/usr/bin/env python3
"""Stable Stage3 entrypoint with the canonical strict lineage CLI parser."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.experiment_family_lineage import ExperimentFamilySpec, LINEAGE_SCHEMA_VERSION
from engine.mature_multifactor_research import (
    DEFAULT_COST_BPS,
    DEFAULT_END,
    DEFAULT_LABEL_HORIZON,
    DEFAULT_LAKE_ROOT,
    DEFAULT_MAX_WEIGHT,
    DEFAULT_MIN_ADV_AMOUNT,
    DEFAULT_PROCESS_EVIDENCE_ROOT,
    DEFAULT_REBALANCE_STEP,
    DEFAULT_RESEARCH_ROOT,
    DEFAULT_START,
    DEFAULT_TOP_N,
    ProducerLineageConfig,
    ProducerLineageError,
    run_stage3_mature_multifactor_research,
)
from scripts.legacy.cr.run_stage3_mature_multifactor_research import parse_factor_weights


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _is_uri(value: str) -> bool:
    parsed = urlsplit(value)
    return bool(parsed.scheme or parsed.netloc)


def parse_producer_lineage_cli_pair(
    *,
    lineage_spec: str | None,
    lineage_root: str | None,
    producer_chain_id: str,
) -> ProducerLineageConfig | None:
    """Strictly map the explicit CLI pair to the sole typed adapter DTO."""

    spec_value = lineage_spec.strip() if isinstance(lineage_spec, str) else ""
    root_value = lineage_root.strip() if isinstance(lineage_root, str) else ""
    if not spec_value and not root_value:
        return None
    if not spec_value or not root_value:
        raise ProducerLineageError("lineage_cli_pair_required")
    if _is_uri(spec_value):
        raise ProducerLineageError("lineage_spec_path_invalid")
    spec_path = Path(spec_value)
    if not spec_path.is_absolute() or not spec_path.is_file() or spec_path.is_symlink():
        raise ProducerLineageError("lineage_spec_path_invalid")
    if _is_uri(root_value):
        raise ProducerLineageError("lineage_root_invalid")
    root_path = Path(root_value)
    if not root_path.is_absolute() or root_path.is_symlink() or (root_path.exists() and not root_path.is_dir()):
        raise ProducerLineageError("lineage_root_invalid")
    try:
        payload = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProducerLineageError("lineage_spec_json_invalid") from error
    if not isinstance(payload, dict):
        raise ProducerLineageError("lineage_spec_json_invalid")
    if type(payload.get("schema_version")) is not int or payload.get("schema_version") != LINEAGE_SCHEMA_VERSION:
        raise ProducerLineageError("schema_version_unsupported")
    required = {
        "schema_version", "family_id", "producer_chain_id", "declared_sequence",
        "objective_ref", "parameter_space_ref",
    }
    if required - payload.keys():
        raise ProducerLineageError("required_field_missing")
    if payload.get("producer_chain_id") != producer_chain_id:
        raise ProducerLineageError("family_identity_mismatch")
    allowed = required | {"run_refs", "experiment_refs", "metadata"}
    if set(payload) - allowed:
        raise ProducerLineageError("required_field_missing", "unknown_field")
    text_fields = ("family_id", "producer_chain_id", "objective_ref", "parameter_space_ref")
    if any(not isinstance(payload.get(field), str) or not str(payload[field]).strip() for field in text_fields):
        raise ProducerLineageError("invalid_identifier")
    if not _IDENTIFIER.fullmatch(str(payload["family_id"])):
        raise ProducerLineageError("invalid_identifier")
    if type(payload.get("declared_sequence")) is not int or payload["declared_sequence"] < 0:
        raise ProducerLineageError("required_field_missing")
    if not isinstance(payload.get("run_refs", []), list) or not isinstance(payload.get("experiment_refs", []), list):
        raise ProducerLineageError("required_field_missing")
    if any(not isinstance(item, str) or not item.strip() for item in payload.get("run_refs", []) + payload.get("experiment_refs", [])):
        raise ProducerLineageError("required_field_missing")
    if not isinstance(payload.get("metadata", {}), dict):
        raise ProducerLineageError("required_field_missing")
    try:
        spec = ExperimentFamilySpec(
            schema_version=payload["schema_version"],
            family_id=payload["family_id"],
            producer_chain_id=payload["producer_chain_id"],
            declared_sequence=payload["declared_sequence"],
            objective_ref=payload["objective_ref"],
            parameter_space_ref=payload["parameter_space_ref"],
            run_refs=tuple(payload.get("run_refs", ())),
            experiment_refs=tuple(payload.get("experiment_refs", ())),
            metadata=payload.get("metadata", {}),
        )
    except (KeyError, TypeError, ValueError) as error:
        text = str(error)
        code = "invalid_identifier" if "non-empty string" in text else "required_field_missing"
        raise ProducerLineageError(code) from error
    return ProducerLineageConfig(spec, root_path, producer_chain_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run mature multifactor strategy research.")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--lake-root", default=str(DEFAULT_LAKE_ROOT))
    parser.add_argument("--research-root", default=str(DEFAULT_RESEARCH_ROOT))
    parser.add_argument("--process-evidence-root", default=str(DEFAULT_PROCESS_EVIDENCE_ROOT))
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--max-weight", type=float, default=DEFAULT_MAX_WEIGHT)
    parser.add_argument("--min-adv-amount", type=float, default=DEFAULT_MIN_ADV_AMOUNT)
    parser.add_argument("--cost-bps", type=float, default=DEFAULT_COST_BPS)
    parser.add_argument("--label-horizon", type=int, default=DEFAULT_LABEL_HORIZON)
    parser.add_argument("--rebalance-step", type=int, default=DEFAULT_REBALANCE_STEP)
    parser.add_argument("--factor-weights", default="")
    parser.add_argument("--score-multiplier", type=float, default=1.0)
    parser.add_argument("--lineage-spec", default=None)
    parser.add_argument("--lineage-root", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lineage_config = parse_producer_lineage_cli_pair(
        lineage_spec=args.lineage_spec,
        lineage_root=args.lineage_root,
        producer_chain_id="public_stage3",
    )
    run_id = args.run_id or f"multifactor-strategy-research-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    result = run_stage3_mature_multifactor_research(
        run_id=run_id, lake_root=Path(args.lake_root), research_root=Path(args.research_root),
        process_evidence_root=Path(args.process_evidence_root), start=args.start, end=args.end,
        top_n=args.top_n, max_weight=args.max_weight, min_adv_amount=args.min_adv_amount,
        cost_bps=args.cost_bps, label_horizon=args.label_horizon, rebalance_step=args.rebalance_step,
        factor_weights=parse_factor_weights(args.factor_weights), score_multiplier=args.score_multiplier,
        lineage_config=lineage_config,
    )
    print(json.dumps({"ok": result.status == "PASS", "status": result.status, "run_id": result.run_id}, sort_keys=True))
    return 0 if result.status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
