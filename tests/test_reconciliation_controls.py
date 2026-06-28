from __future__ import annotations

import duckdb


def test_reconciliation_gaps_remain_observable(
    quality_connection: duckdb.DuckDBPyConnection,
) -> None:
    nonzero_gap_count, gap_status_count = quality_connection.execute(
        """
        select
            count(*) filter (
                where reconciliation_gap_amount is not null
                    and abs(reconciliation_gap_amount) > 0.01
            ) as nonzero_gap_count,
            count(*) filter (
                where reconciliation_status = 'gap_observed'
            ) as gap_status_count
        from main.mart_revenue_reconciliation_diagnostics
        """
    ).fetchone()

    assert nonzero_gap_count > 0
    assert gap_status_count > 0


def test_kpi_gate_blocks_or_caveats_revenue_metrics(
    quality_connection: duckdb.DuckDBPyConnection,
) -> None:
    rows = quality_connection.execute(
        """
        select revenue_metric_gate_status, count(*)
        from main.mart_kpi_trust_status
        group by revenue_metric_gate_status
        """
    ).fetchall()
    status_counts = {str(status): int(count) for status, count in rows}

    assert set(status_counts).issubset({"blocked", "eligible_with_caveat", "not_assessable"})
    assert status_counts.get("blocked", 0) > 0
    assert status_counts.get("not_assessable", 0) > 0

    approved_count = quality_connection.execute(
        """
        select count(*)
        from main.mart_kpi_trust_status
        where is_management_kpi_reporting_approved
        """
    ).fetchone()[0]
    assert approved_count == 0
