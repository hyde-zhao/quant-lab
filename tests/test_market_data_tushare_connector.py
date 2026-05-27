import importlib
import json
import sys

from market_data.cli import main
from market_data.connectors.protocol import AdapterConfig, ConnectorRequest
from market_data.connectors.tushare import TushareAdapter
from market_data.contracts import (
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_TRADE_STATUS_DAILY,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout


def run_cli(capsys, *args):
    code = main(list(args))
    captured = capsys.readouterr()
    stdout = json.loads(captured.out) if captured.out else {}
    stderr = json.loads(captured.err) if captured.err else {}
    return code, stdout, stderr


def hs300_request(params=None):
    return ConnectorRequest(
        source=SOURCE_TUSHARE,
        interface=INTERFACE_HS300_INDEX_DAILY,
        params=params
        or {
            "target_dataset": "hs300_index",
            "index_code": "399300.SZ",
            "start_date": "2026-01-02",
            "end_date": "2026-01-03",
        },
        run_id="run-hs300",
        batch_id="b1",
    )


def test_import_tushare_adapter_has_no_network_or_provider_import(monkeypatch):
    def deny_connect(*args, **kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr("socket.socket.connect", deny_connect)
    module = importlib.import_module("market_data.connectors.tushare")
    assert hasattr(module, "TushareAdapter")
    assert "tushare" not in sys.modules


def test_tushare_connector_fail_fast_order_and_no_token_leak(monkeypatch):
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    disabled = TushareAdapter()
    assert disabled.fetch(hs300_request()).error_type == "source_disabled"

    enabled = TushareAdapter(
        AdapterConfig(
            source=SOURCE_TUSHARE,
            enabled=True,
            allow_interfaces=("prices.daily",),
            credential_env_vars=("TUSHARE_TOKEN",),
        )
    )
    assert enabled.fetch(hs300_request()).error_type == "interface_not_allowed"

    allowlisted = TushareAdapter(
        AdapterConfig(
            source=SOURCE_TUSHARE,
            enabled=True,
            allow_interfaces=(INTERFACE_HS300_INDEX_DAILY,),
            credential_env_vars=("TUSHARE_TOKEN",),
        )
    )
    missing = allowlisted.fetch(hs300_request())
    assert missing.error_type == "missing_credential"
    assert "TUSHARE_TOKEN" in missing.error_message

    monkeypatch.setenv("TUSHARE_TOKEN", "secret-value")
    gated = allowlisted.fetch(hs300_request())
    assert gated.error_type == "source_disabled"
    assert "secret-value" not in json.dumps(gated.to_dict())


def test_tushare_provider_is_injected_only_for_explicit_real_execution(monkeypatch):
    calls = []

    class FakeProvider:
        def index_daily(self, **kwargs):
            calls.append(kwargs)
            return [
                {
                    "ts_code": "399300.SZ",
                    "trade_date": "20260102",
                    "close": 4000.0,
                    "pre_close": 3990.0,
                }
            ]

    def provider_factory(env_name):
        assert env_name == "TUSHARE_TOKEN"
        return FakeProvider()

    monkeypatch.setenv("TUSHARE_TOKEN", "secret-value")
    adapter = TushareAdapter(
        AdapterConfig(
            source=SOURCE_TUSHARE,
            enabled=True,
            allow_interfaces=(INTERFACE_HS300_INDEX_DAILY,),
            credential_env_vars=("TUSHARE_TOKEN",),
        ),
        provider_factory=provider_factory,
    )
    result = adapter.fetch(
        hs300_request(
            {
                "target_dataset": "hs300_index",
                "index_code": "399300.SZ",
                "start_date": "2026-01-02",
                "end_date": "2026-01-03",
                "explicit_real_execution": True,
                "offline": False,
            }
        )
    )
    assert not hasattr(result, "error_type")
    assert result.rows[0]["close"] == 4000.0
    assert calls == [
        {"ts_code": "399300.SZ", "start_date": "20260102", "end_date": "20260103"}
    ]


def test_tushare_w3_provider_calls_are_synthesized_with_available_at(monkeypatch):
    calls = []

    class FakeProvider:
        def daily(self, **kwargs):
            calls.append(("daily", kwargs))
            return [{"ts_code": kwargs["ts_code"], "trade_date": "20260102"}]

        def suspend_d(self, **kwargs):
            calls.append(("suspend_d", kwargs))
            return [{"ts_code": kwargs["ts_code"], "trade_date": "20260102", "suspend_type": "S"}]

        def stock_st(self, **kwargs):
            calls.append(("stock_st", kwargs))
            return [{"ts_code": kwargs["ts_code"], "start_date": "20260102", "end_date": "20260103"}]

        def stk_limit(self, **kwargs):
            calls.append(("stk_limit", kwargs))
            return [{"ts_code": kwargs["ts_code"], "trade_date": "20260102", "up_limit": 11, "down_limit": 9}]

    monkeypatch.setenv("TUSHARE_TOKEN", "secret-value")
    adapter = TushareAdapter(
        AdapterConfig(
            source=SOURCE_TUSHARE,
            enabled=True,
            allow_interfaces=(
                INTERFACE_TRADE_STATUS_DAILY,
                INTERFACE_PRICES_LIMIT_DAILY,
                INTERFACE_EVENTS_DISCLOSURE,
            ),
            credential_env_vars=("TUSHARE_TOKEN",),
        ),
        provider_factory=lambda _env_name: FakeProvider(),
    )
    common = {
        "symbols": ["000001.SZ"],
        "start_date": "2026-01-02",
        "end_date": "2026-01-03",
        "explicit_real_execution": True,
        "offline": False,
    }

    trade_status = adapter.fetch(
        ConnectorRequest(SOURCE_TUSHARE, INTERFACE_TRADE_STATUS_DAILY, common, "run-trade-status", "b1")
    )
    prices_limit = adapter.fetch(
        ConnectorRequest(SOURCE_TUSHARE, INTERFACE_PRICES_LIMIT_DAILY, common, "run-prices-limit", "b1")
    )
    events = adapter.fetch(
        ConnectorRequest(SOURCE_TUSHARE, INTERFACE_EVENTS_DISCLOSURE, common, "run-events", "b1")
    )

    assert trade_status.metadata["provider_interface"] == "suspend_d+stock_st+daily"
    assert trade_status.rows[0]["is_suspended"] is True
    assert trade_status.rows[0]["available_at"] == "2026-01-02T09:30:00+08:00"
    assert prices_limit.metadata["provider_interface"] == "stk_limit"
    assert prices_limit.rows[0]["available_at"] == "2026-01-02T08:40:00+08:00"
    assert events.metadata["provider_interface"] == "stock_st"
    assert events.rows[0]["event_type"] == "st_enter"
    assert events.rows[0]["available_at"] == "2026-01-02T09:20:00+08:00"
    assert "secret-value" not in json.dumps([trade_status.metadata, prices_limit.metadata, events.metadata])


def test_hs300_backfill_requires_external_lake_root(capsys, monkeypatch, tmp_path):
    monkeypatch.delenv("MARKET_DATA_LAKE_ROOT", raising=False)
    code, payload, stderr = run_cli(
        capsys,
        "hs300-backfill",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-03",
    )
    assert code == 2
    assert payload == {}
    assert stderr["error_type"] == "lake_root_missing"

    monkeypatch.setenv("MARKET_DATA_LAKE_ROOT", str(tmp_path))
    code, payload, stderr = run_cli(
        capsys,
        "hs300-backfill",
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-03",
        "--run-id",
        "run-hs300",
        "--batch-id",
        "b1",
    )
    assert code == 0
    assert stderr == {}
    assert payload["dataset"] == "hs300_index"
    assert payload["source"] == "tushare"
    assert payload["interface"] == "hs300_index.daily"
    assert payload["index_code"] == "399300.SZ"
    assert payload["lake_root"] == str(tmp_path)
    assert payload["dry_run"] is True
    assert payload["network_calls"] == 0
    assert payload["writes"] == 0
    for field in (
        "dataset",
        "source",
        "interface",
        "index_code",
        "start_date",
        "end_date",
        "lake_root",
        "run_id",
        "resume_policy",
        "dry_run",
        "manifest_path",
        "quality_path",
        "catalog_path",
        "error_enum",
    ):
        assert field in payload
    layout = LakeLayout(tmp_path)
    assert not layout.manifest_path().exists()
    assert not list(tmp_path.rglob("*"))


def test_hs300_real_gate_does_not_write_without_enable_or_token(capsys, tmp_path, monkeypatch):
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    code, _, stderr = run_cli(
        capsys,
        "hs300-backfill",
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-03",
        "--dry-run",
        "false",
    )
    assert code == 2
    assert stderr["error_type"] == "source_disabled"
    assert not list(tmp_path.rglob("*"))

    code, _, stderr = run_cli(
        capsys,
        "hs300-backfill",
        "--lake-root",
        str(tmp_path),
        "--start-date",
        "2026-01-02",
        "--end-date",
        "2026-01-03",
        "--dry-run",
        "false",
        "--enable-real-source",
    )
    assert code == 2
    assert stderr["error_type"] == "missing_credential"
    assert "TUSHARE_TOKEN" in stderr["error_message"]
    assert not list(tmp_path.rglob("*"))
