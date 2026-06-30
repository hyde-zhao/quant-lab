import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from market_data.catalog import CatalogStore
from market_data.cli import (
    JQDataRunSpec,
    build_jqdata_plan,
    cmd_jqdata_acquire,
    cmd_publish,
    cmd_read,
    cmd_replay,
    cmd_revalidate,
    cmd_validate,
)
from market_data.connectors.jqdata import JQDataAdapter
from market_data.connectors.protocol import AdapterConfig, ConnectorRequest
from market_data.contracts import (
    DATASET_EVENTS,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_STATUS,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
    PIT_STATUS_AVAILABLE,
    READINESS_STATUS_AVAILABLE,
    SOURCE_JQDATA,
    SOURCE_VALUES,
)
from market_data.lake_layout import LakeLayout
from market_data.normalization import normalize_run
from market_data.source_registry import SourceRegistryError, resolve_interface
from market_data.storage import read_manifest_records


def _fixed_clock() -> datetime:
    return datetime(2025, 2, 11, 8, 0, tzinfo=timezone.utc)


def _adapter_config() -> AdapterConfig:
    return AdapterConfig(
        source=SOURCE_JQDATA,
        enabled=True,
        allow_interfaces=(INTERFACE_INDEX_MEMBERS_SNAPSHOT,),
        credential_env_vars=("JQDATA_USERNAME", "JQDATA_PASSWORD"),
    )


def _request(params: dict | None = None) -> ConnectorRequest:
    return ConnectorRequest(
        source=SOURCE_JQDATA,
        interface=INTERFACE_INDEX_MEMBERS_SNAPSHOT,
        params={
            "target_dataset": DATASET_INDEX_MEMBERS,
            "index_code": "399300.SZ",
            "start_date": "2025-02-11",
            "end_date": "2025-02-11",
            "explicit_real_execution": True,
            "offline": False,
            **(params or {}),
        },
        run_id="run-jqdata-test",
        batch_id="b1",
    )


def _validate_args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        lake_root=tmp_path,
        dataset=DATASET_INDEX_MEMBERS,
        symbols="000001.SZ,600000.SH",
        index_code="399300.SZ",
        exchange="SSE",
        start_date="2025-02-11",
        end_date="2025-02-11",
        run_id="run-jqdata-test",
        open_trade_dates=None,
        decision_time="2025-02-11T09:00:00+00:00",
        prices_missing_rate_pass=0.0,
        prices_missing_rate_warn=0.02,
        prices_missing_rate_fail=0.05,
    )


def test_jqdata_contract_registry_is_index_members_only() -> None:
    assert SOURCE_JQDATA in SOURCE_VALUES

    class Config:
        sources = {
            SOURCE_JQDATA: {
                "enabled": True,
                "allow_interfaces": (
                    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
                    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                    INTERFACE_STOCK_BASIC_SNAPSHOT,
                    INTERFACE_TRADE_STATUS_DAILY,
                    INTERFACE_PRICES_LIMIT_DAILY,
                    INTERFACE_EVENTS_DISCLOSURE,
                ),
            }
        }

    spec = resolve_interface(SOURCE_JQDATA, INTERFACE_INDEX_MEMBERS_SNAPSHOT, Config)
    assert spec.target_dataset == DATASET_INDEX_MEMBERS
    assert spec.provider_method == "get_index_stocks"
    assert spec.pit_required is True
    assert resolve_interface(SOURCE_JQDATA, INTERFACE_INDEX_WEIGHTS_SNAPSHOT, Config).target_dataset == DATASET_INDEX_WEIGHTS
    assert resolve_interface(SOURCE_JQDATA, INTERFACE_STOCK_BASIC_SNAPSHOT, Config).target_dataset == DATASET_STOCK_BASIC
    assert resolve_interface(SOURCE_JQDATA, INTERFACE_TRADE_STATUS_DAILY, Config).target_dataset == DATASET_TRADE_STATUS
    assert resolve_interface(SOURCE_JQDATA, INTERFACE_PRICES_LIMIT_DAILY, Config).target_dataset == DATASET_PRICES_LIMIT
    assert resolve_interface(SOURCE_JQDATA, INTERFACE_EVENTS_DISCLOSURE, Config).target_dataset == DATASET_EVENTS

    with pytest.raises(SourceRegistryError):
        resolve_interface(SOURCE_JQDATA, "index_weight", Config)

    plan = build_jqdata_plan(
        JQDataRunSpec(
            dataset=DATASET_INDEX_MEMBERS,
            start_date="2025-02-11",
            end_date="2025-02-11",
            lake_root="/tmp/jqdata-plan-test",
        )
    )
    assert plan["source"] == SOURCE_JQDATA
    assert plan["provider_interface"] == "get_index_stocks"
    assert plan["network_calls"] == 0
    assert plan["writes"] == 0
    assert plan["old_data_operations"] == {
        "read": 0,
        "list": 0,
        "migrate": 0,
        "copy": 0,
        "compare": 0,
        "delete": 0,
    }
    assert "/tmp/jqdata-plan-test" not in json.dumps(plan, ensure_ascii=False)

    with pytest.raises(Exception, match="不支持"):
        build_jqdata_plan(
            JQDataRunSpec(
                dataset=DATASET_PRICES,
                start_date="2025-02-11",
                end_date="2025-02-11",
                lake_root="/tmp/jqdata-plan-test",
            )
        )


def test_jqdata_adapter_fail_fast_gates_do_not_call_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def provider_factory(username_env: str, password_env: str) -> object:
        calls.append((username_env, password_env))
        raise AssertionError("provider must not be called")

    disabled = JQDataAdapter(provider_factory=provider_factory)
    assert disabled.fetch(_request()).error_type == "source_disabled"
    assert calls == []

    monkeypatch.delenv("JQDATA_USERNAME", raising=False)
    monkeypatch.delenv("JQDATA_PASSWORD", raising=False)
    missing = JQDataAdapter(_adapter_config(), provider_factory=provider_factory)
    assert missing.fetch(_request()).error_type == "missing_credential"
    assert calls == []

    monkeypatch.setenv("JQDATA_USERNAME", "fixture-user")
    monkeypatch.setenv("JQDATA_PASSWORD", "fixture-pass")
    adapter = JQDataAdapter(_adapter_config(), provider_factory=provider_factory)
    assert adapter.fetch(_request({"offline": True})).error_type == "source_disabled"
    assert adapter.fetch(_request({"explicit_real_execution": False})).error_type == "source_disabled"

    not_allowed = JQDataAdapter(
        AdapterConfig(
            source=SOURCE_JQDATA,
            enabled=True,
            allow_interfaces=(),
            credential_env_vars=("JQDATA_USERNAME", "JQDATA_PASSWORD"),
        ),
        provider_factory=provider_factory,
    )
    assert not_allowed.fetch(_request()).error_type == "interface_not_allowed"
    assert calls == []


def test_jqdata_adapter_maps_codes_and_sanitizes_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    provider_calls: list[tuple[str, str | None]] = []

    class FakeProvider:
        def get_index_stocks(self, index_symbol: str, date: str | None = None):
            provider_calls.append((index_symbol, date))
            return ["000001.XSHE", {"code": "600000.XSHG"}]

    monkeypatch.setenv("JQDATA_USERNAME", "fixture-user")
    monkeypatch.setenv("JQDATA_PASSWORD", "fixture-pass")
    adapter = JQDataAdapter(
        _adapter_config(),
        provider_factory=lambda username_env, password_env: FakeProvider(),
        clock=_fixed_clock,
    )
    result = adapter.fetch(_request())
    assert result.metadata["provider_interface"] == "get_index_stocks"
    assert result.metadata["provider_network_calls"] == 1
    assert provider_calls == [("000300.XSHG", "2025-02-11")]
    assert [row["con_code"] for row in result.rows] == ["000001.SZ", "600000.SH"]
    assert {row["index_code"] for row in result.rows} == {"399300.SZ"}
    assert {row["is_pit_universe"] for row in result.rows} == {True}
    assert {row["pit_status"] for row in result.rows} == {PIT_STATUS_AVAILABLE}
    assert {row["readiness_status"] for row in result.rows} == {READINESS_STATUS_AVAILABLE}

    class PermissionProvider:
        def get_index_stocks(self, index_symbol: str, date: str | None = None):
            raise RuntimeError("permission denied for fixture-user fixture-pass")

    blocked = JQDataAdapter(
        _adapter_config(),
        provider_factory=lambda username_env, password_env: PermissionProvider(),
    ).fetch(_request())
    payload = json.dumps(blocked.to_dict(), ensure_ascii=False)
    assert blocked.error_type == "permission_denied"
    assert "fixture-user" not in payload
    assert "fixture-pass" not in payload


def test_jqdata_adapter_maps_pit_and_w3_interfaces(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeProvider:
        def get_index_weights(self, index_symbol: str, date: str | None = None):
            assert index_symbol == "000300.XSHG"
            return pd.DataFrame(
                [{"code": "000001.XSHE", "date": "2025-01-27", "weight": 0.12}]
            )

        def get_all_securities(self, types=None, date: str | None = None):
            assert types in (["stock"], "stock")
            return pd.DataFrame(
                [
                    {
                        "code": "000001.XSHE",
                        "display_name": "Ping An Bank",
                        "start_date": "1991-04-03",
                        "end_date": "2200-01-01",
                        "type": "stock",
                    }
                ]
            )

        def get_price(self, security, **kwargs):
            assert security == ["000001.XSHE"]
            fields = set(kwargs["fields"])
            row = {"time": "2025-02-11", "code": "000001.XSHE"}
            if "paused" in fields:
                row["paused"] = 0
            if "high_limit" in fields:
                row["high_limit"] = 11.0
            if "low_limit" in fields:
                row["low_limit"] = 9.0
            return pd.DataFrame([row])

        def get_extras(self, info, security_list, start_date=None, end_date=None, df=True):
            assert info == "is_st"
            assert security_list == ["000001.XSHE"]
            return pd.DataFrame(
                {"000001.XSHE": [False, True]},
                index=pd.to_datetime(["2025-02-11", "2025-02-12"]),
            )

    monkeypatch.setenv("JQDATA_USERNAME", "fixture-user")
    monkeypatch.setenv("JQDATA_PASSWORD", "fixture-pass")
    adapter = JQDataAdapter(
        AdapterConfig(
            source=SOURCE_JQDATA,
            enabled=True,
            allow_interfaces=(
                INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
                INTERFACE_STOCK_BASIC_SNAPSHOT,
                INTERFACE_TRADE_STATUS_DAILY,
                INTERFACE_PRICES_LIMIT_DAILY,
                INTERFACE_EVENTS_DISCLOSURE,
            ),
            credential_env_vars=("JQDATA_USERNAME", "JQDATA_PASSWORD"),
        ),
        provider_factory=lambda username_env, password_env: FakeProvider(),
    )

    common = {
        "index_code": "399300.SZ",
        "start_date": "2025-02-11",
        "end_date": "2025-02-12",
        "symbols": ["000001.SZ"],
        "explicit_real_execution": True,
        "offline": False,
    }
    weights = adapter.fetch(
        ConnectorRequest(
            SOURCE_JQDATA,
            INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
            {"target_dataset": DATASET_INDEX_WEIGHTS, **common},
            "run-weights",
            "b1",
        )
    )
    assert weights.metadata["provider_interface"] == "get_index_weights"
    assert weights.rows[0]["trade_date"] == "2025-02-11"
    assert weights.rows[0]["effective_date"] == "2025-01-27"
    assert weights.rows[0]["pit_status"] == PIT_STATUS_AVAILABLE
    assert weights.rows[0]["readiness_status"] == READINESS_STATUS_AVAILABLE

    stock_basic = adapter.fetch(
        ConnectorRequest(
            SOURCE_JQDATA,
            INTERFACE_STOCK_BASIC_SNAPSHOT,
            {"target_dataset": DATASET_STOCK_BASIC, **common},
            "run-stock-basic",
            "b1",
        )
    )
    assert stock_basic.metadata["provider_interface"] == "get_all_securities"
    assert stock_basic.rows[0]["symbol"] == "000001.SZ"
    assert stock_basic.rows[0]["pit_status"] == PIT_STATUS_AVAILABLE

    trade_status = adapter.fetch(
        ConnectorRequest(
            SOURCE_JQDATA,
            INTERFACE_TRADE_STATUS_DAILY,
            {"target_dataset": DATASET_TRADE_STATUS, **common},
            "run-trade-status",
            "b1",
        )
    )
    assert trade_status.metadata["provider_interface"] == "get_price+get_extras"
    assert trade_status.rows[0]["is_tradable"] is True
    assert trade_status.rows[0]["available_at"].endswith("16:00:00+08:00")

    prices_limit = adapter.fetch(
        ConnectorRequest(
            SOURCE_JQDATA,
            INTERFACE_PRICES_LIMIT_DAILY,
            {"target_dataset": DATASET_PRICES_LIMIT, **common},
            "run-prices-limit",
            "b1",
        )
    )
    assert prices_limit.metadata["provider_interface"] == "get_price"
    assert prices_limit.rows[0]["limit_up"] == 11.0

    events = adapter.fetch(
        ConnectorRequest(
            SOURCE_JQDATA,
            INTERFACE_EVENTS_DISCLOSURE,
            {"target_dataset": DATASET_EVENTS, **common},
            "run-events",
            "b1",
        )
    )
    assert events.metadata["provider_interface"] == "get_extras"
    assert events.rows == [
        {
            "symbol": "000001.SZ",
            "event_type": "st_enter",
            "event_date": "2025-02-12",
            "available_at": "2025-02-12T16:00:00+08:00",
            "available_at_rule": "daily_close_fact",
            "payload": '{"is_st": true, "source_event": "is_st"}',
        }
    ]


def test_jqdata_acquire_fake_provider_writes_pit_index_members_lake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProvider:
        def get_index_stocks(self, index_symbol: str, date: str | None = None):
            assert index_symbol == "000300.XSHG"
            assert date == "2025-02-11"
            return ["000001.XSHE", "600000.XSHG"]

    monkeypatch.setenv("JQDATA_USERNAME", "fixture-user")
    monkeypatch.setenv("JQDATA_PASSWORD", "fixture-pass")
    acquired = cmd_jqdata_acquire(
        argparse.Namespace(
            lake_root=tmp_path,
            dataset=DATASET_INDEX_MEMBERS,
            index_code="399300.SZ",
            start_date="2025-02-11",
            end_date="2025-02-11",
            credential_env_username="JQDATA_USERNAME",
            credential_env_password="JQDATA_PASSWORD",
            run_id="run-jqdata-test",
            batch_id="b1",
            dry_run="false",
            enable_real_source=True,
            provider_factory=lambda username_env, password_env: FakeProvider(),
            clock=_fixed_clock,
            json=True,
        )
    )

    assert acquired["network_calls"] == 1
    assert acquired["writes"] == 1
    assert acquired["results"][0]["status"] == "success"

    layout = LakeLayout(tmp_path)
    manifest = read_manifest_records(layout)
    assert len(manifest) == 1
    manifest_text = json.dumps(manifest, ensure_ascii=False)
    assert "fixture-user" not in manifest_text
    assert "fixture-pass" not in manifest_text
    assert "credential" not in json.dumps(manifest[0]["params"], ensure_ascii=False)
    assert manifest[0]["source"] == SOURCE_JQDATA
    assert manifest[0]["interface"] == INTERFACE_INDEX_MEMBERS_SNAPSHOT
    assert manifest[0]["raw_row_count"] == 2

    normalized = normalize_run(
        layout.manifest_path(),
        tmp_path,
        dataset=DATASET_INDEX_MEMBERS,
        run_id="run-jqdata-test",
    )
    assert normalized.row_count == 2
    frame = pd.read_parquet(normalized.canonical_paths[0])
    assert frame["con_code"].tolist() == ["000001.SZ", "600000.SH"]
    assert set(frame["is_pit_universe"]) == {True}
    assert set(frame["pit_status"]) == {PIT_STATUS_AVAILABLE}
    assert set(frame["readiness_status"]) == {READINESS_STATUS_AVAILABLE}
    assert set(frame["source"]) == {SOURCE_JQDATA}

    validated = cmd_validate(_validate_args(tmp_path))
    assert validated["quality_status"] == "pass"
    entry = CatalogStore(tmp_path).get(DATASET_INDEX_MEMBERS)
    assert entry.pit_status == PIT_STATUS_AVAILABLE
    assert entry.readiness_status == READINESS_STATUS_AVAILABLE
    assert entry.published is False

    published = cmd_publish(
        argparse.Namespace(lake_root=tmp_path, dataset=DATASET_INDEX_MEMBERS, allow_warn=False)
    )
    assert published["publish_status"] == "published"
    assert published["pit_status"] == PIT_STATUS_AVAILABLE

    revalidated = cmd_revalidate(_validate_args(tmp_path))
    assert revalidated["network_calls"] == 0
    assert CatalogStore(tmp_path).get(DATASET_INDEX_MEMBERS).published is True

    read = cmd_read(
        argparse.Namespace(
            lake_root=tmp_path,
            dataset=DATASET_INDEX_MEMBERS,
            start_date="2025-02-11",
            end_date="2025-02-11",
            symbols=None,
            index_code="399300.SZ",
            exchange="SSE",
            columns=None,
            limit=5,
            allow_warn=False,
        )
    )
    assert read["row_count"] == 2

    replay = cmd_replay(
        argparse.Namespace(
            lake_root=tmp_path,
            dataset=DATASET_INDEX_MEMBERS,
            start_date="2025-02-11",
            end_date="2025-02-11",
            index_code="399300.SZ",
            run_id="run-jqdata-test",
            batch_id="b1",
        )
    )
    assert replay["network_calls"] == 0
    assert replay["writes"] == 0
    assert replay["auto_execute"] is False


def test_jqdata_pit_fake_provider_writes_weights_and_stock_basic_lake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProvider:
        def get_index_weights(self, index_symbol: str, date: str | None = None):
            assert index_symbol == "000300.XSHG"
            return pd.DataFrame(
                [{"code": "000001.XSHE", "date": "2025-01-27", "weight": 0.12}]
            )

        def get_all_securities(self, types=None, date: str | None = None):
            assert types in (["stock"], "stock")
            return pd.DataFrame(
                [
                    {
                        "code": "000001.XSHE",
                        "display_name": "Ping An Bank",
                        "start_date": "1991-04-03",
                        "end_date": "2200-01-01",
                        "type": "stock",
                    }
                ]
            )

    monkeypatch.setenv("JQDATA_USERNAME", "fixture-user")
    monkeypatch.setenv("JQDATA_PASSWORD", "fixture-pass")

    for dataset in (DATASET_INDEX_WEIGHTS, DATASET_STOCK_BASIC):
        run_id = f"run-{dataset}"
        acquired = cmd_jqdata_acquire(
            argparse.Namespace(
                lake_root=tmp_path,
                dataset=dataset,
                interface=None,
                index_code="399300.SZ",
                symbols=None,
                start_date="2025-02-11",
                end_date="2025-02-11",
                credential_env_username="JQDATA_USERNAME",
                credential_env_password="JQDATA_PASSWORD",
                run_id=run_id,
                batch_id="b1",
                dry_run="false",
                enable_real_source=True,
                provider_factory=lambda username_env, password_env: FakeProvider(),
                clock=_fixed_clock,
                json=True,
            )
        )
        assert acquired["network_calls"] == 1
        assert acquired["writes"] == 1

        layout = LakeLayout(tmp_path)
        normalized = normalize_run(layout.manifest_path(), tmp_path, dataset=dataset, run_id=run_id)
        assert normalized.row_count == 1
        frame = pd.read_parquet(normalized.canonical_paths[0])
        assert set(frame["pit_status"]) == {PIT_STATUS_AVAILABLE}
        assert set(frame["readiness_status"]) == {READINESS_STATUS_AVAILABLE}

        validate_args = argparse.Namespace(
            lake_root=tmp_path,
            dataset=dataset,
            symbols=None,
            index_code="399300.SZ",
            exchange="SSE",
            start_date="2025-02-11",
            end_date="2025-02-11",
            run_id=run_id,
            open_trade_dates=None,
            decision_time="2025-02-11T23:00:00+08:00",
            prices_missing_rate_pass=0.0,
            prices_missing_rate_warn=0.02,
            prices_missing_rate_fail=0.05,
        )
        validated = cmd_validate(validate_args)
        assert validated["quality_status"] == "pass"
        assert CatalogStore(tmp_path).get(dataset).pit_status == PIT_STATUS_AVAILABLE

        published = cmd_publish(argparse.Namespace(lake_root=tmp_path, dataset=dataset, allow_warn=False))
        assert published["publish_status"] == "published"
        assert published["pit_status"] == PIT_STATUS_AVAILABLE

        read = cmd_read(
            argparse.Namespace(
                lake_root=tmp_path,
                dataset=dataset,
                start_date="2025-02-11",
                end_date="2025-02-11",
                symbols="000001.SZ",
                index_code="399300.SZ",
                exchange="SSE",
                columns=None,
                limit=5,
                allow_warn=False,
            )
        )
        assert read["row_count"] == 1

        revalidated = cmd_revalidate(validate_args)
        assert revalidated["network_calls"] == 0
        assert CatalogStore(tmp_path).get(dataset).published is True

        replay = cmd_replay(
            argparse.Namespace(
                lake_root=tmp_path,
                dataset=dataset,
                start_date="2025-02-11",
                end_date="2025-02-11",
                index_code="399300.SZ",
                run_id=run_id,
                batch_id="b1",
            )
        )
        assert replay["network_calls"] == 0
        assert replay["writes"] == 0
        assert replay["auto_execute"] is False


def test_jqdata_w3_fake_provider_writes_normalizes_validates_and_replays(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProvider:
        def get_price(self, security, **kwargs):
            assert security == ["000001.XSHE"]
            fields = set(kwargs["fields"])
            rows = []
            for day, paused, up, down in (
                ("2025-02-11", 0, 11.0, 9.0),
                ("2025-02-12", 1, 10.5, 8.5),
            ):
                row = {"time": day, "code": "000001.XSHE"}
                if "paused" in fields:
                    row["paused"] = paused
                if "high_limit" in fields:
                    row["high_limit"] = up
                if "low_limit" in fields:
                    row["low_limit"] = down
                rows.append(row)
            return pd.DataFrame(rows)

        def get_extras(self, info, security_list, start_date=None, end_date=None, df=True):
            assert info == "is_st"
            return pd.DataFrame(
                {"000001.XSHE": [False, True]},
                index=pd.to_datetime(["2025-02-11", "2025-02-12"]),
            )

    monkeypatch.setenv("JQDATA_USERNAME", "fixture-user")
    monkeypatch.setenv("JQDATA_PASSWORD", "fixture-pass")
    provider_factory = lambda username_env, password_env: FakeProvider()

    for dataset in (DATASET_TRADE_STATUS, DATASET_PRICES_LIMIT, DATASET_EVENTS):
        run_id = f"run-{dataset}"
        acquired = cmd_jqdata_acquire(
            argparse.Namespace(
                lake_root=tmp_path,
                dataset=dataset,
                interface=None,
                index_code="399300.SZ",
                symbols="000001.SZ",
                start_date="2025-02-11",
                end_date="2025-02-12",
                credential_env_username="JQDATA_USERNAME",
                credential_env_password="JQDATA_PASSWORD",
                run_id=run_id,
                batch_id="b1",
                dry_run="false",
                enable_real_source=True,
                provider_factory=provider_factory,
                clock=_fixed_clock,
                json=True,
            )
        )
        assert acquired["writes"] == 1
        assert acquired["results"][0]["status"] == "success"

        layout = LakeLayout(tmp_path)
        normalized = normalize_run(layout.manifest_path(), tmp_path, dataset=dataset, run_id=run_id)
        assert normalized.row_count == (1 if dataset == DATASET_EVENTS else 2)
        validate_args = argparse.Namespace(
            lake_root=tmp_path,
            dataset=dataset,
            symbols="000001.SZ" if dataset != DATASET_EVENTS else None,
            index_code="399300.SZ",
            exchange="SSE",
            start_date="2025-02-11",
            end_date="2025-02-12",
            run_id=run_id,
            open_trade_dates=None,
            decision_time=None,
            prices_missing_rate_pass=0.0,
            prices_missing_rate_warn=0.02,
            prices_missing_rate_fail=0.05,
        )
        validated = cmd_validate(validate_args)
        assert validated["quality_status"] == "pass"

        published = cmd_publish(argparse.Namespace(lake_root=tmp_path, dataset=dataset, allow_warn=False))
        assert published["publish_status"] == "published"
        assert published["readiness_status"] == READINESS_STATUS_AVAILABLE

        read = cmd_read(
            argparse.Namespace(
                lake_root=tmp_path,
                dataset=dataset,
                start_date="2025-02-11",
                end_date="2025-02-12",
                symbols="000001.SZ",
                index_code="399300.SZ",
                exchange="SSE",
                columns=None,
                limit=5,
                allow_warn=False,
            )
        )
        assert read["row_count"] == (1 if dataset == DATASET_EVENTS else 2)

        revalidated = cmd_revalidate(validate_args)
        assert revalidated["network_calls"] == 0
        assert CatalogStore(tmp_path).get(dataset).published is True

        replay = cmd_replay(
            argparse.Namespace(
                lake_root=tmp_path,
                dataset=dataset,
                start_date="2025-02-11",
                end_date="2025-02-12",
                index_code="399300.SZ",
                run_id=run_id,
                batch_id="b1",
            )
        )
        assert replay["network_calls"] == 0
        assert replay["writes"] == 0
        assert replay["auto_execute"] is False
