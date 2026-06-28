"""Read-only data access for the RenewalOS Streamlit Control Tower."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb

from renewalos.app.validation import (
    AppDataError,
    load_priority_export_records,
    validate_priority_export_records,
    validate_warehouse_ready,
)
from renewalos.prioritization.config import (
    ASSUMPTION_DETAILS,
    DEFAULT_PRIORITIZATION_SCENARIO,
)
from renewalos.warehouse.load_raw import WAREHOUSE_DB_PATH


def query_dataframe(
    query: str,
    parameters: Sequence[object] | None = None,
    database_path: Path = WAREHOUSE_DB_PATH,
) -> Any:
    """Run a read-only query against the built local DuckDB warehouse."""

    validate_warehouse_ready(database_path=database_path)
    try:
        with duckdb.connect(str(database_path.resolve()), read_only=True) as connection:
            cursor = connection.execute(query, list(parameters or ()))
            columns = [str(column[0]) for column in cursor.description]
            rows = cursor.fetchall()
    except duckdb.Error as error:
        raise AppDataError(f"Warehouse query failed: {error}") from error
    return _pandas().DataFrame.from_records(rows, columns=columns)


def load_kpi_trust_status_counts(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            revenue_metric_gate_status as gate_status,
            is_management_kpi_reporting_approved,
            count(*) as account_month_count
        from main.mart_kpi_trust_status
        group by revenue_metric_gate_status, is_management_kpi_reporting_approved
        order by account_month_count desc, gate_status
        """,
        database_path=database_path,
    )


def load_account_month_quality_counts(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            quality_status,
            count(*) as account_month_count,
            sum(critical_exception_count) as critical_exception_count,
            sum(warning_exception_count) as warning_exception_count
        from main.dq_account_month_quality_status
        group by quality_status
        order by account_month_count desc, quality_status
        """,
        database_path=database_path,
    )


def load_quality_rule_summary(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        with all_exceptions as (
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
            source_domain,
            severity,
            rule_id,
            count(*) as exception_count,
            count(distinct account_id) as affected_account_count
        from all_exceptions
        group by source_domain, severity, rule_id
        order by
            case severity when 'critical' then 1 when 'warning' then 2 else 3 end,
            exception_count desc,
            rule_id
        """,
        database_path=database_path,
    )


def load_incident_detection_coverage(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            incident_id,
            scenario_name,
            affected_domain,
            registered_severity,
            detected_rule_id,
            detection_status,
            expected_business_impact,
            unmatched_explanation
        from main.dq_incident_detection_coverage
        order by incident_id
        """,
        database_path=database_path,
    )


def load_reconciliation_status_counts(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            reconciliation_status,
            quality_status,
            count(*) as account_month_count
        from main.mart_revenue_reconciliation_diagnostics
        group by reconciliation_status, quality_status
        order by account_month_count desc, reconciliation_status
        """,
        database_path=database_path,
    )


def load_reconciliation_gap_summary(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            count(*) as account_month_count,
            count(*) filter (
                where reconciliation_gap_amount is not null
                    and reconciliation_gap_amount <> 0
            ) as nonzero_gap_count,
            sum(abs(coalesce(reconciliation_gap_amount, 0))) as absolute_gap_amount,
            max(abs(coalesce(reconciliation_gap_amount, 0))) as largest_absolute_gap_amount
        from main.mart_revenue_reconciliation_diagnostics
        """,
        database_path=database_path,
    )


def load_reconciliation_details(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            account_id,
            account_month,
            reconciliation_status,
            quality_status,
            opening_balance_amount,
            supported_revenue_movement_amount,
            expected_closing_balance_amount,
            observed_closing_balance_amount,
            reconciliation_gap_amount,
            critical_exception_count,
            warning_exception_count,
            quality_blocker,
            reconciliation_explanation,
            is_kpi_eligible,
            diagnostic_note
        from main.mart_revenue_reconciliation_diagnostics
        order by account_month desc, account_id
        """,
        database_path=database_path,
    )


def load_health_coverage(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            assessment_status,
            reason_category,
            reason_count,
            total_observable_account_months,
            blocked_account_months,
            not_assessable_account_months,
            eligible_with_caveat_account_months,
            eligible_account_months,
            is_predictive_model_output,
            is_automated_recommendation
        from main.mart_account_health_coverage
        order by assessment_status, reason_category
        """,
        database_path=database_path,
    )


def load_health_band_distribution(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            health_band,
            count(*) as account_month_count
        from main.mart_account_health
        where assessment_status in ('eligible', 'eligible_with_caveat')
            and health_band is not null
        group by health_band
        order by
            case health_band
                when 'critical' then 1
                when 'at_risk' then 2
                when 'monitor' then 3
                when 'stable' then 4
                else 5
            end
        """,
        database_path=database_path,
    )


def load_account_health_details(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            account_id,
            account_month,
            assessment_status,
            assessment_reason_category,
            quality_status,
            health_score,
            health_band,
            revenue_exposure_amount,
            renewal_urgency,
            usage_concern,
            support_concern,
            customer_success_engagement_concern,
            revenue_or_billing_status_concern,
            reconciliation_status,
            explanation_summary,
            is_predictive_model_output,
            is_automated_recommendation
        from main.mart_account_health
        order by account_month desc, account_id
        """,
        database_path=database_path,
    )


def load_health_explanations(
    account_id: str,
    account_month: object,
    database_path: Path = WAREHOUSE_DB_PATH,
) -> Any:
    return query_dataframe(
        """
        select
            component_name,
            component_value,
            impact_direction,
            severity,
            plain_language_explanation,
            source_lineage_reference,
            synthetic_data_label
        from main.mart_account_health_explanations
        where account_id = ?
            and account_month = cast(? as date)
        order by
            case severity when 'high' then 1 when 'medium' then 2 when 'low' then 3 else 4 end,
            component_name
        """,
        parameters=[account_id, str(account_month)],
        database_path=database_path,
    )


def load_candidate_eligibility_summary(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            is_eligible_candidate,
            coalesce(exclusion_reason, 'eligible_candidate') as eligibility_reason,
            assessment_status,
            count(*) as account_month_count
        from main.mart_csm_priority_candidates
        group by
            is_eligible_candidate,
            coalesce(exclusion_reason, 'eligible_candidate'),
            assessment_status
        order by is_eligible_candidate desc, account_month_count desc
        """,
        database_path=database_path,
    )


def load_prioritization_input_summary(database_path: Path = WAREHOUSE_DB_PATH) -> Any:
    return query_dataframe(
        """
        select
            scenario_id,
            assumption_version,
            priority_tier,
            count(*) as candidate_count,
            sum(estimated_effort_hours) as total_estimated_effort_hours,
            sum(expected_protected_value) as total_expected_protected_value
        from main.mart_csm_prioritization_inputs
        group by scenario_id, assumption_version, priority_tier
        order by priority_tier
        """,
        database_path=database_path,
    )


def load_prioritization_export(
    output_path: Path = DEFAULT_PRIORITIZATION_SCENARIO.output_path,
) -> Any:
    records = load_priority_export_records(output_path=output_path)
    validate_priority_export_records(records)
    return _pandas().DataFrame.from_records(records)


def load_scenario_assumptions() -> Any:
    scenario = DEFAULT_PRIORITIZATION_SCENARIO
    values = {
        "available_csm_hours_per_month": str(scenario.available_csm_hours_per_month),
        "csm_count": str(scenario.csm_count),
        "max_accounts_per_csm": str(scenario.max_accounts_per_csm),
        "max_accounts_to_contact": str(scenario.max_accounts_to_contact),
        "max_solver_candidate_pool": str(scenario.max_solver_candidate_pool),
        "scenario_id": scenario.scenario_id,
        "assumption_version": scenario.assumption_version,
        "objective": scenario.objective,
    }
    rows = [
        {
            "assumption": name,
            "value": values.get(name, ""),
            "rationale": rationale,
        }
        for name, rationale in ASSUMPTION_DETAILS
    ]
    rows.extend(
        [
            {
                "assumption": "scenario_id",
                "value": scenario.scenario_id,
                "rationale": "Scenario identifier carried into generated recommendations.",
            },
            {
                "assumption": "assumption_version",
                "value": scenario.assumption_version,
                "rationale": "Version label for simulated prioritization assumptions.",
            },
            {
                "assumption": "objective",
                "value": scenario.objective,
                "rationale": "Optimization objective used by the CSM prioritization command.",
            },
        ]
    )
    return _pandas().DataFrame.from_records(rows)


def _pandas() -> Any:
    import pandas  # type: ignore[import-untyped]

    return pandas
