import pandas as pd

from market_data.contracts import CANONICAL_EVENTS_COLUMNS
from market_data.normalization import repair_events_schema


def test_events_schema_repair_fills_available_at_and_lineage_fields():
    frame = pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "event_type": "disclosure",
                "event_date": "2026-01-02",
            }
        ]
    )

    result = repair_events_schema(
        frame,
        source="tushare",
        source_interface="events_disclosure",
        source_run_id="cr139-w2-events-tushare-20260102-canonical",
        lineage_raw_checksum="sha256:abc",
    )

    assert list(result.frame.columns) == list(CANONICAL_EVENTS_COLUMNS)
    assert result.frame.loc[0, "available_at"] == "2026-01-02T09:20:00+08:00"
    assert result.frame.loc[0, "source_run_id"] == "cr139-w2-events-tushare-20260102-canonical"
    assert "available_at" in result.repaired_fields
