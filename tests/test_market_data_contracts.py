from pathlib import Path

import pytest

import market_data
from market_data import contracts
from market_data.config import DEFAULT_CONFIG
from market_data.lake_layout import LakeLayout, MarketDataPathError, ensure_parent_dirs_for_write
from market_data.source_registry import SourceRegistryError, resolve_interface, resolve_source


def test_market_data_import_is_lightweight():
    assert market_data.__version__
    assert contracts.SCHEMA_VERSION == "1.0"


def test_contract_fields_and_batch_a_scope():
    assert set(contracts.CANONICAL_PRICES_REQUIRED_COLUMNS) >= {
        "trade_date",
        "symbol",
        "close",
        "source",
        "source_run_id",
    }
    assert len(contracts.MANIFEST_REQUIRED_FIELDS) >= 20
    for field in (
        "idempotency_key",
        "params_hash",
        "raw_checksum",
        "raw_row_count",
        "canonical_path",
    ):
        assert field in contracts.MANIFEST_REQUIRED_FIELDS
    assert "source_unresolved" in contracts.CONNECTOR_ERROR_TYPES
    assert contracts.DATASET_INDEX_MEMBERS == "index_members"
    assert contracts.DATASET_TRADE_CALENDAR == "trade_calendar"


def test_lake_layout_paths_use_custom_root(tmp_path):
    layout = LakeLayout(tmp_path)
    assert layout.raw_root == tmp_path / "raw"
    assert layout.manifest_path() == tmp_path / "manifest" / "market_data_manifest.jsonl"
    assert layout.canonical_dataset_root("prices") == tmp_path / "canonical" / "prices" / "1.0"
    assert layout.raw_batch_path("fake", "prices.daily", "2026-01-02", "b1") == (
        tmp_path / "raw" / "fake" / "prices.daily" / "20260102" / "b1.jsonl"
    )
    assert layout.raw_run_batch_path("fake", "prices.daily", "2026-01-02", "run-1", "b1") == (
        tmp_path / "raw" / "fake" / "prices.daily" / "20260102" / "run_id=run-1" / "b1.jsonl"
    )


def test_parent_path_file_occupation_fails(tmp_path):
    occupied = tmp_path / "raw"
    occupied.write_text("file", encoding="utf-8")
    with pytest.raises(MarketDataPathError, match="安装路径被非目录占用"):
        ensure_parent_dirs_for_write(occupied / "fake" / "x.jsonl")


def test_source_registry_exact_and_fail_fast():
    fake = resolve_source("fake")
    assert fake.status == "resolved"
    assert resolve_interface("fake", "prices.daily").target_dataset == "prices"

    with pytest.raises(SourceRegistryError):
        resolve_source("Fake")

    with pytest.raises(SourceRegistryError) as tickflow_error:
        resolve_source("tickflow")
    assert tickflow_error.value.error_type == "source_unresolved"
    assert tickflow_error.value.source_status == "unresolved"

    with pytest.raises(SourceRegistryError) as akshare_error:
        resolve_source("akshare")
    assert akshare_error.value.error_type == "source_disabled"


def test_default_config_is_offline_and_safe():
    assert DEFAULT_CONFIG.offline is True
    assert DEFAULT_CONFIG.default_source == "fake"
    assert DEFAULT_CONFIG.sources["fake"].enabled is True
    assert DEFAULT_CONFIG.sources["tushare"].credential_env_vars == ("TUSHARE_TOKEN",)


def test_market_data_does_not_import_engine_family():
    market_data_root = Path("market_data")
    text = "\n".join(path.read_text(encoding="utf-8") for path in market_data_root.rglob("*.py"))
    assert "import engine" not in text
    assert "from engine" not in text
    assert "import experiments" not in text
    assert "from experiments" not in text
    assert "import reports" not in text
    assert "from reports" not in text
