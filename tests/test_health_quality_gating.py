from __future__ import annotations

import duckdb


def test_blocked_records_cannot_be_scored(
    health_connection: duckdb.DuckDBPyConnection,
) -> None:
    invalid_count = health_connection.execute(
        """
        select count(*)
        from main.mart_account_health
        where assessment_status = 'blocked_due_to_data_quality'
            and (
                health_score is not null
                or health_band is not null
            )
        """
    ).fetchone()[0]

    assert invalid_count == 0


def test_not_assessable_records_cannot_be_scored(
    health_connection: duckdb.DuckDBPyConnection,
) -> None:
    invalid_count = health_connection.execute(
        """
        select count(*)
        from main.mart_account_health
        where assessment_status = 'not_assessable'
            and (
                health_score is not null
                or health_band is not null
            )
        """
    ).fetchone()[0]

    assert invalid_count == 0


def test_health_output_preserves_account_month_quality_status(
    health_connection: duckdb.DuckDBPyConnection,
) -> None:
    mismatch_count = health_connection.execute(
        """
        select count(*)
        from main.mart_account_health as health
        inner join main.dq_account_month_quality_status as quality_status
            on health.account_id = quality_status.account_id
            and health.account_month = quality_status.account_month
        where health.quality_status <> quality_status.quality_status
        """
    ).fetchone()[0]

    assert mismatch_count == 0
