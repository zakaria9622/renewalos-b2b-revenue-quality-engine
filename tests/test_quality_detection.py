from __future__ import annotations

import duckdb

from renewalos.quality.quality_constants import EXPECTED_INCIDENT_SCENARIOS, QUALITY_STATUSES


def test_quality_detection_coverage_reports_every_incident_scenario(
    quality_connection: duckdb.DuckDBPyConnection,
) -> None:
    rows = quality_connection.execute(
        """
        select scenario_name, detection_status, detected_rule_id
        from main.dq_incident_detection_coverage
        """
    ).fetchall()
    coverage = {
        str(scenario_name): (str(status), rule_id)
        for scenario_name, status, rule_id in rows
    }

    assert set(EXPECTED_INCIDENT_SCENARIOS).issubset(coverage)
    for scenario_name in EXPECTED_INCIDENT_SCENARIOS:
        detection_status, detected_rule_id = coverage[scenario_name]
        assert detection_status == "detected"
        assert detected_rule_id is not None


def test_detected_exceptions_retain_identifiers_and_rule_metadata(
    quality_connection: duckdb.DuckDBPyConnection,
) -> None:
    total_count, missing_metadata_count = quality_connection.execute(
        """
        with exceptions as (
            select * from main.dq_contract_exceptions
            union all
            select * from main.dq_billing_exceptions
            union all
            select * from main.dq_usage_exceptions
            union all
            select * from main.dq_support_exceptions
            union all
            select * from main.dq_identifier_exceptions
        )
        select
            count(*) as total_count,
            sum(
                case
                    when rule_id is null
                        or severity is null
                        or source_domain is null
                        or affected_record_identifier is null
                        or scenario_name is null
                        then 1
                    else 0
                end
            ) as missing_metadata_count
        from exceptions
        """
    ).fetchone()

    assert total_count > 0
    assert missing_metadata_count == 0


def test_account_month_quality_status_assignment_is_documented(
    quality_connection: duckdb.DuckDBPyConnection,
) -> None:
    rows = quality_connection.execute(
        """
        select quality_status, count(*)
        from main.dq_account_month_quality_status
        group by quality_status
        """
    ).fetchall()
    status_counts = {str(status): int(count) for status, count in rows}

    assert set(status_counts).issubset(set(QUALITY_STATUSES))
    assert status_counts.get("blocked", 0) > 0
    assert status_counts.get("warning", 0) > 0
    assert status_counts.get("eligible_with_caveat", 0) > 0

    missing_reason_count = quality_connection.execute(
        """
        select count(*)
        from main.dq_account_month_quality_status
        where quality_status_reason is null
            or quality_status_reason = ''
        """
    ).fetchone()[0]
    assert missing_reason_count == 0
