from __future__ import annotations

from argparse import Namespace
import ast
import inspect
from pathlib import Path

import pandas as pd

from engine.experiment_lake_input_contract import (
    EXPERIMENT_REQUIRED_DATASETS,
    add_experiment_lake_args,
    load_experiment_lake_frames,
)
from experiments.run_experiment_15_factor_framework import parse_args as parse_experiment_15_args
from experiments.run_experiment_15_factor_framework import run_factor_framework
from experiments.run_experiment_16_momentum_factor import parse_args as parse_experiment_16_args
from experiments.run_experiment_16_momentum_factor import run_momentum_factor_validation
from experiments.run_experiment_17_21_factor_suite import parse_args as parse_experiment_17_21_args
from experiments.run_experiment_17_21_factor_suite import run_factor_suite
from experiments.run_experiment_23_29_ml_factor_suite import parse_args as parse_stage4_args
from experiments.run_experiment_23_29_ml_factor_suite import run_stage4_suite
from market_data.contracts import DATASET_INDEX_MEMBERS
from market_data.readers import ReaderResult
from market_data.readers import read_panel_as_of


def test_target_entry_functions_do_not_call_local_parquet_bypass() -> None:
    for function in (run_factor_framework, run_momentum_factor_validation, run_factor_suite, run_stage4_suite):
        tree = ast.parse(inspect.getsource(function))
        calls = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert "load_local_frames" not in calls


def test_parsers_no_longer_define_data_dir() -> None:
    assert "--data-dir" not in _parser_options(parse_experiment_15_args)
    assert "--data-dir" not in _parser_options(parse_experiment_16_args)
    assert "--data-dir" not in _parser_options(parse_experiment_17_21_args)
    assert "--data-dir" not in _parser_options(parse_stage4_args)


def test_lake_input_contract_calls_pit_reader_for_required_datasets(tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def reader(dataset: str, lake_root: str | Path, **kwargs: object) -> ReaderResult:
        calls.append({"dataset": dataset, "lake_root": lake_root, **kwargs})
        return ReaderResult(status="available", frame=_frame_for(dataset))

    result = load_experiment_lake_frames(
        Namespace(
            lake_root=tmp_path / "lake",
            as_of="2024-02-01T16:00:00+08:00",
            start_date="2024-01-01",
            end_date="2024-01-31",
            symbols=("AAA",),
            quality_policy="require_pass",
        ),
        reader=reader,
    )

    assert tuple(call["dataset"] for call in calls) == EXPERIMENT_REQUIRED_DATASETS
    assert {call["as_of"] for call in calls} == {"2024-02-01T16:00:00+08:00"}
    assert set(result.frames) == {"prices", "index_members", "trade_calendar"}
    assert calls[0]["keys"] == ("trade_date", "symbol")
    assert calls[1]["keys"] == ("trade_date", "index_code", "con_code")
    assert all(value == 0 for value in result.permission_counters.values())
    assert result.source_lineage["input_mode"] == "read_panel_as_of"


def test_lake_input_contract_normalises_canonical_index_members_con_code(tmp_path: Path) -> None:
    def reader(dataset: str, lake_root: str | Path, **kwargs: object) -> ReaderResult:
        if dataset == "index_members":
            return ReaderResult(
                status="available",
                frame=pd.DataFrame(
                    [
                        {
                            "trade_date": "2024-01-02",
                            "con_code": "AAA",
                            "index_code": "UNIT",
                            "is_member": True,
                            "available_at": "2024-01-02T16:00:00+08:00",
                        }
                    ]
                ),
            )
        return ReaderResult(status="available", frame=_frame_for(dataset))

    result = load_experiment_lake_frames(
        Namespace(lake_root=tmp_path / "lake", as_of="2024-02-01T16:00:00+08:00"),
        reader=reader,
    )

    assert result.frames["index_members"]["symbol"].tolist() == ["AAA"]


def test_index_members_pit_reader_preserves_multi_index_membership_rows() -> None:
    result = read_panel_as_of(
        DATASET_INDEX_MEMBERS,
        as_of="2024-01-02T16:30:00+08:00",
        keys=("trade_date", "index_code", "con_code"),
        reader=lambda *args, **kwargs: ReaderResult(
            status="available",
            frame=pd.DataFrame(
                [
                    {
                        "trade_date": "2024-01-02",
                        "index_code": "HS300",
                        "con_code": "AAA",
                        "is_member": False,
                        "available_at": "2024-01-02T16:20:00+08:00",
                    },
                    {
                        "trade_date": "2024-01-02",
                        "index_code": "ZZ500",
                        "con_code": "AAA",
                        "is_member": True,
                        "available_at": "2024-01-02T16:00:00+08:00",
                    },
                ]
            ),
        ),
    )

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame[["index_code", "con_code", "is_member"]].to_dict("records") == [
        {"index_code": "HS300", "con_code": "AAA", "is_member": False},
        {"index_code": "ZZ500", "con_code": "AAA", "is_member": True},
    ]


def test_fixture_frames_are_explicit_test_only_input(tmp_path: Path) -> None:
    frames = {
        "prices": _frame_for("prices"),
        "index_members": _frame_for("index_members"),
        "trade_calendar": _frame_for("trade_calendar"),
    }
    result = load_experiment_lake_frames(
        Namespace(lake_root=tmp_path / "lake", as_of="2024-02-01T16:00:00+08:00", fixture_frames=frames)
    )

    assert result.dataset_status == {dataset: "fixture" for dataset in EXPERIMENT_REQUIRED_DATASETS}
    assert result.source_lineage["reader_contract"] == "read_panel_as_of"
    assert all(value == 0 for value in result.permission_counters.values())


def _parser_options(parser_fn) -> set[str]:
    tree = ast.parse(inspect.getsource(parser_fn))
    return {
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    }


def _frame_for(dataset: str) -> pd.DataFrame:
    if dataset == "prices":
        return pd.DataFrame(
            [
                {
                    "trade_date": "2024-01-02",
                    "symbol": "AAA",
                    "close": 10.0,
                    "available_at": "2024-01-02T16:00:00+08:00",
                    "volume": 1000.0,
                    "amount": 10000.0,
                    "adjustment_policy": "qfq",
                    "is_suspended": False,
                }
            ]
        )
    if dataset == "index_members":
        return pd.DataFrame(
            [
                {
                    "trade_date": "2024-01-02",
                    "symbol": "AAA",
                    "index_code": "UNIT",
                    "is_member": True,
                    "available_at": "2024-01-02T16:00:00+08:00",
                }
            ]
        )
    return pd.DataFrame([{"trade_date": "2024-01-02", "is_open": True, "available_at": "2024-01-02T16:00:00+08:00"}])
