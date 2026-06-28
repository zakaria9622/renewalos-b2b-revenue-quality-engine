from __future__ import annotations

import duckdb

from renewalos.health.health_constants import (
    ASSESSMENT_STATUSES,
    HEALTH_BAND_THRESHOLDS,
    HEALTH_BANDS,
    HEALTH_COMPONENTS,
    TOTAL_HEALTH_SCORE,
)


def test_scoring_thresholds_and_allowed_bands_are_documented() -> None:
    component_names = {component.component_name for component in HEALTH_COMPONENTS}

    assert component_names == {
        "revenue",
        "renewal",
        "usage",
        "support",
        "customer_success",
    }
    assert TOTAL_HEALTH_SCORE == 100
    assert set(HEALTH_BANDS) == {"critical", "at_risk", "monitor", "stable"}
    assert set(ASSESSMENT_STATUSES) == {
        "blocked_due_to_data_quality",
        "not_assessable",
        "eligible_with_caveat",
        "eligible",
    }

    for component in HEALTH_COMPONENTS:
        assert component.max_score > 0
        assert component.rationale
        assert component.source_lineage
        assert component.simulated_assumption
        assert component.thresholds

    assert HEALTH_BAND_THRESHOLDS[-1].score == TOTAL_HEALTH_SCORE


def test_explanation_records_exist_for_scored_account_months(
    health_connection: duckdb.DuckDBPyConnection,
) -> None:
    missing_explanation_count = health_connection.execute(
        """
        with required_components(component_name) as (
            values
                ('revenue'),
                ('renewal'),
                ('usage'),
                ('support'),
                ('customer_success')
        ),
        scored_rows as (
            select account_id, account_month
            from main.mart_account_health
            where health_score is not null
        )
        select count(*)
        from scored_rows
        cross join required_components
        left join main.mart_account_health_explanations as explanations
            on scored_rows.account_id = explanations.account_id
            and scored_rows.account_month = explanations.account_month
            and required_components.component_name = explanations.component_name
        where explanations.component_name is null
        """
    ).fetchone()[0]

    assert missing_explanation_count == 0


def test_health_coverage_contains_all_expected_assessment_statuses(
    health_connection: duckdb.DuckDBPyConnection,
) -> None:
    rows = health_connection.execute(
        """
        select distinct assessment_status
        from main.mart_account_health_coverage
        """
    ).fetchall()
    observed_statuses = {str(row[0]) for row in rows}

    assert set(ASSESSMENT_STATUSES).issubset(observed_statuses)
