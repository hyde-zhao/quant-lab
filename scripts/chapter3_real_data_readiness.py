"""CR-034 第三章真实数据 readiness 报告入口。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.chapter3_real_data_readiness import (
    CHAPTER3_END_DATE,
    CHAPTER3_START_DATE,
    build_chapter3_readiness_report,
    write_readiness_report,
)
from engine.research_paths import research_run_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成第三章真实数据 readiness 报告")
    parser.add_argument("--lake-root", default=os.environ.get("MARKET_DATA_LAKE_ROOT", ""))
    parser.add_argument("--start-date", default=CHAPTER3_START_DATE)
    parser.add_argument("--end-date", default=CHAPTER3_END_DATE)
    parser.add_argument(
        "--output-dir",
        default=str(research_run_path("chapter3_real_data_readiness")),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.lake_root:
        raise SystemExit("缺少 --lake-root 或 MARKET_DATA_LAKE_ROOT")
    report = build_chapter3_readiness_report(
        args.lake_root,
        target_start=args.start_date,
        target_end=args.end_date,
    )
    json_path, md_path = write_readiness_report(report, Path(args.output_dir))
    print(
        json.dumps(
            {
                "ok": True,
                "status": report.status,
                "json_path": str(json_path),
                "markdown_path": str(md_path),
                "catalog_current_pointer_publish": report.operation_counts.get("catalog_current_pointer_publish", 0),
                "qmt_operation": report.operation_counts.get("qmt_operation", 0),
                "simulation_or_live_run": report.operation_counts.get("simulation_or_live_run", 0),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
