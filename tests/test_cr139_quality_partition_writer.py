from __future__ import annotations

import json

import pytest

from market_data.contracts import DATASET_PRICES
from market_data.lake_layout import LakeLayout
from market_data.quality_writer import (
    QUALITY_WRITE_MODE_PROBE,
    QUALITY_WRITE_MODE_SMOKE,
    QualityWriteRequest,
    quality_partition_path,
    write_partitioned_quality_report,
)


def test_s38_official_quality_report_uses_dataset_date_partition(tmp_path) -> None:
    layout = LakeLayout(tmp_path)
    request = QualityWriteRequest(
        dataset=DATASET_PRICES,
        run_id="run-cr139-s38",
        as_of_date="20260102",
        payload={"quality_status": "pass"},
    )

    result = write_partitioned_quality_report(layout, request)

    assert result.path.relative_to(tmp_path).as_posix() == "quality/prices/2026-01-02/run-cr139-s38-quality.json"
    assert result.scratch is False
    assert result.operation_counters["catalog_write"] == 0
    assert result.operation_counters["manifest_write"] == 0
    payload = json.loads(result.path.read_text(encoding="utf-8"))
    assert payload["payload"]["quality_status"] == "pass"


@pytest.mark.parametrize("mode", [QUALITY_WRITE_MODE_SMOKE, QUALITY_WRITE_MODE_PROBE])
def test_s38_smoke_probe_quality_reports_are_isolated_to_scratch(tmp_path, mode: str) -> None:
    layout = LakeLayout(tmp_path)
    request = QualityWriteRequest(
        dataset=DATASET_PRICES,
        run_id="run-cr139-s38-smoke",
        as_of_date="2026-01-02",
        payload={"quality_status": "pass"},
        mode=mode,
    )

    result = write_partitioned_quality_report(layout, request)

    assert result.scratch is True
    assert result.path.relative_to(tmp_path).as_posix() == (
        "quality/_scratch/run-cr139-s38-smoke/prices-2026-01-02-quality.json"
    )
    assert not (tmp_path / "quality" / DATASET_PRICES / "2026-01-02").exists()


def test_s38_quality_partition_path_rejects_unsafe_segments(tmp_path) -> None:
    with pytest.raises(ValueError, match="unsafe_quality_path_segment: dataset"):
        quality_partition_path(
            tmp_path,
            QualityWriteRequest(
                dataset="../prices",
                run_id="run-cr139-s38",
                as_of_date="2026-01-02",
                payload={},
            ),
        )
