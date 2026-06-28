from __future__ import annotations

from pathlib import Path

import duckdb

from renewalos.prioritization.config import PrioritizationScenario
from renewalos.prioritization.optimizer import optimize_priorities


def _scenario() -> PrioritizationScenario:
    return PrioritizationScenario(
        scenario_id="synthetic_csm_capacity_v1",
        assumption_version="simulated_prioritization_assumptions_v1",
        available_csm_hours_per_month=4.0,
        csm_count=1,
        max_accounts_per_csm=2,
        max_accounts_to_contact=2,
        max_solver_candidate_pool=10,
        objective="maximize_expected_protected_value",
        output_path=Path("unused.csv"),
    )


def _candidate(account_id: str, expected_protected_value: float) -> dict[str, object]:
    return {
        "account_id": account_id,
        "account_month": "2026-01-01",
        "assessment_status": "eligible",
        "quality_status": "no_observed_issue",
        "is_eligible_candidate": True,
        "exclusion_reason": "",
        "priority_tier": "tier_2",
        "priority_score": expected_protected_value / 2.0,
        "estimated_account_value_at_risk": expected_protected_value * 10,
        "estimated_effort_hours": 2.0,
        "assumed_intervention_effectiveness": 0.10,
        "expected_protected_value": expected_protected_value,
        "health_band": "at_risk",
        "revenue_exposure_amount": 1000.0,
        "renewal_urgency": "high",
        "usage_concern": "usage_decline",
        "support_concern": "elevated_support",
        "customer_success_engagement_concern": "limited_recent_engagement",
        "revenue_or_billing_status_concern": "no_reconciliation_gap",
        "explanation_drivers": "usage:medium:synthetic diagnostic driver",
    }


def test_optimizer_never_selects_blocked_or_not_assessable_records() -> None:
    blocked = _candidate("acct_blocked", 10000.0)
    blocked["assessment_status"] = "blocked_due_to_data_quality"
    blocked["quality_status"] = "blocked"
    blocked["exclusion_reason"] = "blocked_due_to_data_quality"

    not_assessable = _candidate("acct_not_assessable", 9000.0)
    not_assessable["assessment_status"] = "not_assessable"
    not_assessable["exclusion_reason"] = "missing_usage_or_contract_signal"

    eligible = _candidate("acct_eligible", 10.0)

    result = optimize_priorities([blocked, not_assessable, eligible], _scenario())
    selected_accounts = {
        str(record["account_id"])
        for record in result.records
        if record["recommendation_status"] == "selected"
    }

    assert selected_accounts == {"acct_eligible"}

    excluded_accounts = {
        str(record["account_id"])
        for record in result.records
        if record["recommendation_status"] == "excluded"
    }
    assert {"acct_blocked", "acct_not_assessable"}.issubset(excluded_accounts)


def test_prioritization_dbt_inputs_respect_health_quality_gate(
    prioritization_connection: duckdb.DuckDBPyConnection,
) -> None:
    invalid_input_count = prioritization_connection.execute(
        """
        select count(*)
        from main.mart_csm_prioritization_inputs
        where assessment_status in ('blocked_due_to_data_quality', 'not_assessable')
            or quality_status = 'blocked'
        """
    ).fetchone()[0]

    assert invalid_input_count == 0


def test_prioritization_candidates_explain_all_exclusions(
    prioritization_connection: duckdb.DuckDBPyConnection,
) -> None:
    missing_reason_count = prioritization_connection.execute(
        """
        select count(*)
        from main.mart_csm_priority_candidates
        where not is_eligible_candidate
            and (
                exclusion_reason is null
                or exclusion_reason = ''
            )
        """
    ).fetchone()[0]

    assert missing_reason_count == 0
