"""Run Stage 3 mature multifactor research from the canonical data lake."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    run_stage3_mature_multifactor_research,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Stage 3 mature multifactor research.")
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
    parser.add_argument("--factor-weights", default="", help="Comma separated factor_id=weight overrides for composite_score.")
    parser.add_argument("--score-multiplier", type=float, default=1.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = args.run_id or f"stage3-mature-mf-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    result = run_stage3_mature_multifactor_research(
        run_id=run_id,
        lake_root=Path(args.lake_root),
        research_root=Path(args.research_root),
        process_evidence_root=Path(args.process_evidence_root),
        start=args.start,
        end=args.end,
        top_n=args.top_n,
        max_weight=args.max_weight,
        min_adv_amount=args.min_adv_amount,
        cost_bps=args.cost_bps,
        label_horizon=args.label_horizon,
        rebalance_step=args.rebalance_step,
        factor_weights=parse_factor_weights(args.factor_weights),
        score_multiplier=args.score_multiplier,
    )
    print(
        json.dumps(
            {
                "ok": result.status == "PASS",
                "status": result.status,
                "package_status": result.package_status,
                "run_id": result.run_id,
                "metrics_summary": dict(result.metrics_summary),
                "artifacts": result.artifacts.to_dict(),
                "operation_counts": dict(result.operation_counts),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.status == "PASS" else 2


def parse_factor_weights(value: str) -> dict[str, float]:
    if not value.strip():
        return {}
    weights: dict[str, float] = {}
    for item in value.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(f"invalid factor weight item: {item}")
        factor_id, weight = item.split("=", 1)
        weights[factor_id.strip()] = float(weight)
    return weights


if __name__ == "__main__":
    raise SystemExit(main())
