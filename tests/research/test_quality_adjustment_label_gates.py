from __future__ import annotations

import ast
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from engine.research_dataset import (
    ResearchDatasetRequest,
    ResearchDatasetStatus,
    build_research_dataset,
    evaluate_research_gates,
)
from market_data.catalog import CatalogEntry
from market_data.contracts import DATASET_INDEX_MEMBERS, DATASET_PRICES, DATASET_TRADE_CALENDAR
from market_data.readers import ReaderResult


TARGET_FILES = (
    Path("engine/research_dataset.py"),
    Path("engine/quality.py"),
)


def test_quality_fail_blocks_research_and_never_claims_available(tmp_path: Path) -> None:
    dataset = build_dataset(
        tmp_path,
        prices=prices_frame(day_count=10),
        price_quality_status="fail",
        end_date="2026-01-10",
        horizon=3,
    )

    assert dataset.status == ResearchDatasetStatus.QUALITY_FAILED.value
    assert dataset.gate_result.status == "fail"
    assert issue_codes(dataset) >= {"quality_failed"}
    assert dataset.metadata["quality"]["quality_status"] == "fail"
    assert dataset.metadata["quality"]["quality_source"] == "catalog_entry"
    assert dataset.allowed_claims == []
    assert dataset.available is False


def test_quality_missing_fails_without_reading_legacy_quality_report(tmp_path: Path) -> None:
    dataset = build_dataset(
        tmp_path,
        prices=prices_frame(day_count=10),
        price_catalog_entry=None,
        end_date="2026-01-07",
        horizon=3,
    )

    assert dataset.status == ResearchDatasetStatus.QUALITY_FAILED.value
    assert "quality_missing" in issue_codes(dataset)
    assert dataset.metadata["quality"]["quality_source"] == "missing"
    assert dataset.available is False


def test_quality_warn_writes_limitation_but_keeps_warning_status(tmp_path: Path) -> None:
    dataset = build_dataset(
        tmp_path,
        prices=prices_frame(day_count=10),
        price_quality_status="warn",
        end_date="2026-01-07",
        horizon=3,
        analysis_mode="exploratory",
    )

    assert dataset.status == ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value
    assert dataset.gate_result.status == "warn"
    assert "quality_warn" in issue_codes(dataset)
    assert dataset.metadata["quality"]["quality_status"] == "warn"
    assert any(limit.get("code") == "quality_warn" for limit in dict_limitations(dataset))


@pytest.mark.parametrize(
    ("case", "expected_code"),
    [
        ("mixed", "adjustment_policy_mixed"),
        ("missing", "adjustment_policy_missing"),
        ("mismatch", "adjustment_policy_mismatch"),
    ],
)
def test_adjustment_policy_mixed_missing_or_mismatch_fails(
    tmp_path: Path,
    case: str,
    expected_code: str,
) -> None:
    prices = {
        "mixed": prices_frame(day_count=10, policies=("qfq", "hfq")),
        "missing": prices_frame(day_count=10, include_adjustment=False),
        "mismatch": prices_frame(day_count=10, policies=("hfq",)),
    }[case]
    dataset = build_dataset(
        tmp_path,
        prices=prices,
        price_catalog_entry=catalog_entry(DATASET_PRICES, adjustment_policy=None),
        end_date="2026-01-07",
        horizon=3,
    )

    assert dataset.status == ResearchDatasetStatus.GATE_FAILED.value
    assert expected_code in issue_codes(dataset)
    assert dataset.metadata["adjustment"]["adjustment_status"] == "failed"
    assert dataset.allowed_claims == []
    assert dataset.available is False


def test_label_window_insufficient_fails_research_with_structured_metadata(tmp_path: Path) -> None:
    dataset = build_dataset(
        tmp_path,
        prices=prices_frame(day_count=10),
        end_date="2026-01-10",
        horizon=3,
        analysis_mode="research",
    )

    assert dataset.status == ResearchDatasetStatus.GATE_FAILED.value
    assert "label_window_insufficient" in issue_codes(dataset)
    label = dataset.metadata["label_window"]
    assert label["label_status"] == "insufficient"
    assert label["label_available_end"] == "2026-01-07"
    assert label["requested_decision_end"] == "2026-01-10"
    assert label["truncated_date_count"] == 3
    assert label["truncated_sample_count"] == 6
    assert dataset.metadata["label_available_end"] == "2026-01-07"
    assert dataset.available is False


def test_label_window_exploratory_truncates_in_memory_samples_and_claims(tmp_path: Path) -> None:
    dataset = build_dataset(
        tmp_path,
        prices=prices_frame(day_count=10),
        end_date="2026-01-10",
        horizon=3,
        analysis_mode="exploratory",
    )

    assert dataset.status == ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value
    assert dataset.gate_result.status == "warn"
    assert "label_window_truncated" in issue_codes(dataset)
    label = dataset.metadata["label_window"]
    assert label["label_status"] == "truncated"
    assert label["label_available_end"] == "2026-01-07"
    assert label["truncated_date_count"] == 3
    assert label["truncated_sample_count"] == 6
    assert max(pd.to_datetime(dataset.prices["trade_date"]).dt.date) == date(2026, 1, 7)
    assert list(dataset.close_df.index)[-1] == date(2026, 1, 7)
    assert dataset.allowed_claims == ["framework_validation", "exploratory_analysis"]
    assert any(limit.get("code") == "label_window_truncated" for limit in dict_limitations(dataset))


def test_evaluate_research_gates_accepts_s03_dataset_contract(tmp_path: Path) -> None:
    base = build_dataset(
        tmp_path,
        prices=prices_frame(day_count=10),
        end_date="2026-01-07",
        horizon=3,
        apply_s04_gates=False,
    )

    evaluated = evaluate_research_gates(base, request(tmp_path, end_date="2026-01-07", horizon=3))

    assert base.status == ResearchDatasetStatus.AVAILABLE.value
    assert evaluated.status == ResearchDatasetStatus.AVAILABLE.value
    assert evaluated.gate_result.status == "pass"
    assert evaluated.metadata["label_window"]["label_status"] == "available"
    assert evaluated.metadata["adjustment"]["policies_seen"] == ["qfq"]


def test_s04_security_boundaries_do_not_touch_old_report_or_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_secret = "CR008_S04_FAKE_TOKEN_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("TUSHARE_TOKEN", fake_secret)
    touched_old_report: list[str] = []
    original_open = Path.open
    original_read_text = Path.read_text

    def guarded_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        if str(self).endswith("reports/data_quality_report.csv"):
            touched_old_report.append(str(self))
            raise AssertionError("old quality report must not be opened")
        return original_open(self, *args, **kwargs)

    def guarded_read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        if str(self).endswith("reports/data_quality_report.csv"):
            touched_old_report.append(str(self))
            raise AssertionError("old quality report must not be read")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    dataset = build_dataset(
        tmp_path,
        prices=prices_frame(day_count=10),
        end_date="2026-01-07",
        horizon=3,
    )

    combined = json.dumps(
        [dataset.metadata, [issue.to_dict() for issue in dataset.issues], dataset.known_limitations],
        ensure_ascii=False,
        default=str,
    )
    assert touched_old_report == []
    assert fake_secret not in combined


def test_s04_forbidden_imports_and_legacy_paths_are_absent() -> None:
    forbidden_modules = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
    }
    for path in TARGET_FILES:
        imports = imported_modules(path)
        assert not any(module == forbidden or module.startswith(forbidden + ".") for module in imports for forbidden in forbidden_modules)
        source = path.read_text(encoding="utf-8")
        assert "reports/data_quality_report.csv" not in source
        assert "TUSHARE_TOKEN" not in source


def build_dataset(
    tmp_path: Path,
    *,
    prices: pd.DataFrame,
    price_quality_status: str = "pass",
    price_catalog_entry: CatalogEntry | None | str = "default",
    end_date: str,
    horizon: int,
    analysis_mode: str = "research",
    apply_s04_gates: bool = True,
) -> Any:
    start_date = "2026-01-01"
    if price_catalog_entry == "default":
        price_entry = catalog_entry(DATASET_PRICES, quality_status=price_quality_status)
    else:
        price_entry = price_catalog_entry
    reader_results = {
        DATASET_PRICES: ReaderResult(status="available", frame=prices, catalog_entry=price_entry),
        DATASET_TRADE_CALENDAR: ReaderResult(
            status="available",
            frame=calendar_frame(day_count=10),
            catalog_entry=catalog_entry(DATASET_TRADE_CALENDAR),
        ),
        DATASET_INDEX_MEMBERS: ReaderResult(
            status="available",
            frame=universe_frame(),
            catalog_entry=catalog_entry(DATASET_INDEX_MEMBERS),
        ),
    }
    reader = make_reader(reader_results)
    return build_research_dataset(
        request(
            tmp_path,
            start_date=start_date,
            end_date=end_date,
            horizon=horizon,
            analysis_mode=analysis_mode,
        ),
        reader=reader,
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
        apply_s04_gates=apply_s04_gates,
    )


def request(
    tmp_path: Path,
    *,
    start_date: str = "2026-01-01",
    end_date: str,
    horizon: int,
    analysis_mode: str = "research",
) -> ResearchDatasetRequest:
    return ResearchDatasetRequest(
        lake_root=tmp_path / "lake",
        start_date=start_date,
        end_date=end_date,
        adjustment_policy="qfq",
        forward_return_horizon=horizon,
        analysis_mode=analysis_mode,
        benchmark_policy="proxy_allowed",
    )


def prices_frame(
    *,
    day_count: int,
    include_adjustment: bool = True,
    policies: tuple[str, ...] = ("qfq",),
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    start = date(2026, 1, 1)
    symbols = ("AAA", "BBB")
    for offset in range(day_count):
        trade_date = start + timedelta(days=offset)
        for symbol_index, symbol in enumerate(symbols):
            row: dict[str, Any] = {
                "trade_date": trade_date.isoformat(),
                "symbol": symbol,
                "close": 10.0 + offset + symbol_index,
                "adjusted_close": 10.0 + offset + symbol_index,
                "source_run_id": "prices-run",
                "lineage_raw_checksum": "prices-checksum",
            }
            if include_adjustment:
                row["adjustment_policy"] = policies[(offset + symbol_index) % len(policies)]
            rows.append(row)
    return pd.DataFrame(rows)


def calendar_frame(*, day_count: int) -> pd.DataFrame:
    start = date(2026, 1, 1)
    return pd.DataFrame(
        {"trade_date": (start + timedelta(days=offset)).isoformat(), "is_open": True}
        for offset in range(day_count)
    )


def universe_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "is_member": True},
            {"symbol": "BBB", "is_member": True},
        ]
    )


def catalog_entry(
    dataset: str,
    *,
    quality_status: str = "pass",
    adjustment_policy: str | None = "qfq",
) -> CatalogEntry:
    coverage: dict[str, Any] = {}
    if adjustment_policy is not None:
        coverage["adjustment_policy"] = adjustment_policy
    return CatalogEntry(
        dataset=dataset,
        start_date="2026-01-01",
        end_date="2026-01-10",
        quality_status=quality_status,
        dataset_status="available",
        latest_manifest_run_id=f"{dataset}-manifest",
        source="fixture",
        source_interface=f"{dataset}.fixture",
        lineage_raw_checksum=f"{dataset}-checksum",
        coverage=coverage,
    )


def make_reader(results: dict[str, ReaderResult]) -> Any:
    def reader(
        dataset: str,
        lake_root: str | Path | None,
        filters: dict[str, Any] | None = None,
        quality_policy: Any = None,
        *,
        required: bool = False,
    ) -> ReaderResult:
        del lake_root, filters, quality_policy, required
        return results[dataset]

    return reader


def issue_codes(dataset: Any) -> set[str]:
    return {issue.code for issue in dataset.issues}


def dict_limitations(dataset: Any) -> list[dict[str, Any]]:
    return [item for item in dataset.known_limitations if isinstance(item, dict)]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules
