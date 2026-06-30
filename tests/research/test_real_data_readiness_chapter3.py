from engine.research_data_readiness import (
    BLOCKED,
    MISSING,
    PASS,
    PASS_WITH_LIMITATIONS,
    DatasetRunCoverage,
    evaluate_dataset_readiness,
    evaluate_financial_pit_readiness,
    evaluate_hfq_readiness,
    render_readiness_markdown,
)


def test_dataset_readiness_passes_when_aggregate_window_covers_target() -> None:
    result = evaluate_dataset_readiness(
        (
            DatasetRunCoverage(
                dataset="prices",
                run_id="run-2015",
                path="/lake/prices/2015",
                row_count=10,
                start_date="2015-01-01",
                end_date="2019-12-31",
            ),
            DatasetRunCoverage(
                dataset="prices",
                run_id="run-2000",
                path="/lake/prices/2000",
                row_count=10,
                start_date="2000-01-01",
                end_date="2014-12-31",
            ),
        ),
        dataset="prices",
        target_start="2000-01-01",
        target_end="2019-12-31",
    )

    assert result.status == PASS
    assert result.aggregate_start == "2000-01-01"
    assert result.aggregate_end == "2019-12-31"
    assert result.row_count == 20


def test_dataset_readiness_blocks_when_target_window_is_not_covered() -> None:
    result = evaluate_dataset_readiness(
        (
            DatasetRunCoverage(
                dataset="prices",
                run_id="run-2015",
                path="/lake/prices/2015",
                row_count=10,
                start_date="2015-01-01",
                end_date="2019-12-31",
            ),
        ),
        dataset="prices",
        target_start="2000-01-01",
        target_end="2019-12-31",
    )

    assert result.status == BLOCKED
    assert result.missing_reason == "target_window_not_covered"


def test_dataset_readiness_marks_missing_dataset() -> None:
    result = evaluate_dataset_readiness(
        (),
        dataset="financial_pit",
        target_start="2000-01-01",
        target_end="2019-12-31",
    )

    assert result.status == MISSING
    assert result.missing_reason == "canonical_dataset_missing"


def test_hfq_readiness_requires_independent_view_or_full_raw_factor_coverage() -> None:
    prices = evaluate_dataset_readiness(
        (
            DatasetRunCoverage(
                dataset="prices",
                run_id="run-full",
                path="/lake/prices",
                row_count=10,
                start_date="2000-01-01",
                end_date="2019-12-31",
            ),
        ),
        dataset="prices",
        target_start="2000-01-01",
        target_end="2019-12-31",
    )
    adj_factor = evaluate_dataset_readiness(
        (
            DatasetRunCoverage(
                dataset="adj_factor",
                run_id="run-full",
                path="/lake/adj_factor",
                row_count=10,
                start_date="2000-01-01",
                end_date="2019-12-31",
            ),
        ),
        dataset="adj_factor",
        target_start="2000-01-01",
        target_end="2019-12-31",
    )

    status, reason = evaluate_hfq_readiness(
        {"prices", "adj_factor"},
        (prices, adj_factor),
        target_start="2000-01-01",
        target_end="2019-12-31",
    )

    assert status == PASS_WITH_LIMITATIONS
    assert "派生" in reason


def test_financial_pit_readiness_blocks_when_no_financial_dataset() -> None:
    status, reason = evaluate_financial_pit_readiness({"prices", "adj_factor"})

    assert status == BLOCKED
    assert "财务 PIT" in reason


def test_financial_pit_readiness_limited_when_candidate_dataset_exists() -> None:
    status, reason = evaluate_financial_pit_readiness({"prices", "income", "balancesheet"})

    assert status == PASS_WITH_LIMITATIONS
    assert "income" in reason


def test_financial_pit_readiness_passes_with_audited_pit_columns_and_coverage() -> None:
    status, reason = evaluate_financial_pit_readiness(
        {"financial_pit"},
        runs=(
            DatasetRunCoverage(
                dataset="financial_pit",
                run_id="run-audited",
                path="/lake/financial_pit",
                row_count=10,
                columns=(
                    "symbol",
                    "report_period",
                    "ann_date",
                    "available_at",
                    "update_flag",
                    "revision_as_of",
                    "revision_sequence",
                    "pit_policy",
                ),
                start_date="2000-01-08",
                end_date="2019-12-31",
            ),
        ),
        target_start="2000-01-01",
        target_end="2019-12-31",
    )

    assert status == PASS
    assert "PIT 审计字段" in reason


def test_render_markdown_includes_forbidden_operation_counts() -> None:
    prices = evaluate_dataset_readiness(
        (),
        dataset="prices",
        target_start="2000-01-01",
        target_end="2019-12-31",
    )

    from engine.research_data_readiness import Chapter3ReadinessReport

    markdown = render_readiness_markdown(
        Chapter3ReadinessReport(
            lake_root="/lake",
            target_start="2000-01-01",
            target_end="2019-12-31",
            status=BLOCKED,
            datasets=(prices,),
            hfq_status=BLOCKED,
            hfq_reason="missing",
            financial_pit_status=BLOCKED,
            financial_pit_reason="missing",
            operation_counts={"catalog_current_pointer_publish": 0, "qmt_operation": 0},
        )
    )

    assert "catalog_current_pointer_publish" in markdown
    assert "`qmt_operation` | 0" in markdown
