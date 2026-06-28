from __future__ import annotations

from pathlib import Path

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


def _candidate(
    account_id: str,
    expected_protected_value: float,
    effort_hours: float = 2.0,
    account_month: str = "2026-01-01",
) -> dict[str, object]:
    return {
        "account_id": account_id,
        "account_month": account_month,
        "assessment_status": "eligible",
        "quality_status": "no_observed_issue",
        "is_eligible_candidate": True,
        "exclusion_reason": "",
        "priority_tier": "tier_2",
        "priority_score": expected_protected_value / effort_hours,
        "estimated_account_value_at_risk": expected_protected_value * 10,
        "estimated_effort_hours": effort_hours,
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


def test_optimizer_is_deterministic_and_respects_capacity() -> None:
    scenario = _scenario()
    candidates = [
        _candidate("acct_001", 100.0),
        _candidate("acct_001", 50.0),
        _candidate("acct_002", 90.0),
        _candidate("acct_003", 80.0),
    ]

    first_result = optimize_priorities(candidates, scenario)
    second_result = optimize_priorities(candidates, scenario)

    first_selected = [
        record["account_id"]
        for record in first_result.records
        if record["recommendation_status"] == "selected"
    ]
    second_selected = [
        record["account_id"]
        for record in second_result.records
        if record["recommendation_status"] == "selected"
    ]

    assert first_selected == second_selected == ["acct_001", "acct_002"]
    assert first_result.selected_count == 2
    assert first_result.selected_effort_hours == 4.0
    assert first_result.selected_expected_protected_value == 190.0


def test_optimizer_outputs_metadata_for_selected_and_nonselected_records() -> None:
    result = optimize_priorities(
        [_candidate("acct_001", 100.0), _candidate("acct_002", 90.0), _candidate("acct_003", 80.0)],
        _scenario(),
    )

    statuses = {str(record["recommendation_status"]) for record in result.records}

    assert statuses == {"selected", "not_selected"}
    for record in result.records:
        assert record["scenario_id"] == "synthetic_csm_capacity_v1"
        assert record["assumption_version"] == "simulated_prioritization_assumptions_v1"
        assert record["assumption_label"] == "simulated_scenario_assumption_not_observed_effect"
        assert record["is_observed_intervention_outcome"] is False
        assert "explanation_drivers" in record
