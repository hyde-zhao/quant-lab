from argparse import Namespace
import json

from market_data.cli import cmd_published_asof_replay
from market_data.replay import (
    PUBLISHED_ASOF_NOT_PUBLISHED,
    PUBLISHED_ASOF_READY,
    PUBLISHED_ASOF_SNAPSHOT_MISSING,
    PublishedAsOfReplayRequest,
    build_published_asof_replay,
)


def _pointer(**overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "dataset": "prices",
        "published": True,
        "status": "published",
        "as_of_trade_date": "2026-01-02",
        "published_path": "published://prices/20260102",
        "manifest_ref": "manifest://prices/20260102",
    }
    payload.update(overrides)
    return payload


def test_s35_published_asof_replay_selects_exact_published_snapshot() -> None:
    result = build_published_asof_replay(
        PublishedAsOfReplayRequest(dataset="prices", as_of_trade_date="2026-01-02"),
        [_pointer(), _pointer(dataset="events")],
    )

    assert result.status == PUBLISHED_ASOF_READY
    assert result.ready is True
    assert result.published_path == "published://prices/20260102"
    assert result.manifest_ref == "manifest://prices/20260102"
    assert result.provider_fetches == 0
    assert result.lake_writes == 0
    assert result.catalog_writes == 0
    assert result.manifest_writes == 0
    assert result.current_pointer_changes == 0


def test_s35_published_asof_replay_blocks_candidate_snapshot() -> None:
    result = build_published_asof_replay(
        {"dataset": "prices", "as_of_trade_date": "2026-01-02"},
        [_pointer(published=False, status="candidate_unpublished")],
    )

    assert result.ready is False
    assert result.error_codes == (PUBLISHED_ASOF_NOT_PUBLISHED,)
    assert result.provider_fetches == 0


def test_s35_published_asof_replay_blocks_missing_asof_without_provider_backfill() -> None:
    result = build_published_asof_replay(
        PublishedAsOfReplayRequest(dataset="prices", as_of_trade_date="2026-01-03"),
        [_pointer()],
    )

    assert result.ready is False
    assert result.error_codes == (PUBLISHED_ASOF_SNAPSHOT_MISSING,)
    assert result.details[0]["provider_backfill"] == "forbidden"
    assert result.provider_fetches == 0
    assert result.credential_reads == 0


def test_s35_cli_wrapper_uses_explicit_pointer_json_without_lake_scan() -> None:
    payload = cmd_published_asof_replay(
        Namespace(
            dataset="prices",
            as_of_trade_date="2026-01-02",
            run_id="replay-run",
            batch_id="replay-batch",
            pointer_json=json.dumps([_pointer()]),
        )
    )

    assert payload["ok"] is True
    assert payload["command"] == "published-asof-replay"
    assert payload["status"] == PUBLISHED_ASOF_READY
    assert payload["provider_fetches"] == 0
    assert payload["lake_writes"] == 0
