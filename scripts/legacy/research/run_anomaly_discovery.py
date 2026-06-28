#!/usr/bin/env python3
"""Run controlled automatic anomaly discovery from local research artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.anomaly_discovery import run_anomaly_discovery, write_anomaly_discovery_outputs


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run controlled anomaly discovery.")
    parser.add_argument("--feature-panel", required=True, help="Parquet file with trade_date, symbol, forward_return and candidate fields.")
    parser.add_argument("--model-returns", required=True, help="Parquet file with trade_date, model_id, model_return.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sample-id", default="research")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--min-cross-section", type=int, default=30)
    parser.add_argument("--quantiles", type=int, default=5)
    parser.add_argument("--multiple-testing-alpha", type=float, default=0.05)
    args = parser.parse_args(argv)

    import pandas as pd

    feature_panel = pd.read_parquet(args.feature_panel)
    model_returns = pd.read_parquet(args.model_returns)
    result = run_anomaly_discovery(
        feature_panel,
        model_returns,
        run_id=args.run_id,
        sample_id=args.sample_id,
        min_cross_section=args.min_cross_section,
        quantiles=args.quantiles,
        multiple_testing_alpha=args.multiple_testing_alpha,
    )
    paths = write_anomaly_discovery_outputs(result, args.output_dir)
    print(paths["run_report"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
