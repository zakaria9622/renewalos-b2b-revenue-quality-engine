from __future__ import annotations

from renewalos.config import PROCESSED_DATA_DIR
from renewalos.prioritization.config import (
    ASSUMPTION_DETAILS,
    DEFAULT_PRIORITIZATION_SCENARIO,
)


def test_default_prioritization_scenario_is_explicit() -> None:
    scenario = DEFAULT_PRIORITIZATION_SCENARIO

    assert scenario.scenario_id == "synthetic_csm_capacity_v1"
    assert scenario.assumption_version == "simulated_prioritization_assumptions_v1"
    assert scenario.available_csm_hours_per_month == 96.0
    assert scenario.csm_count == 4
    assert scenario.max_accounts_per_csm == 12
    assert scenario.max_accounts_to_contact == 48
    assert scenario.max_solver_candidate_pool == 960
    assert scenario.total_account_capacity == 48
    assert scenario.objective == "maximize_expected_protected_value"
    assert scenario.output_path.is_relative_to(PROCESSED_DATA_DIR)


def test_prioritization_assumptions_are_documented_in_code() -> None:
    documented_assumption_names = {name for name, _rationale in ASSUMPTION_DETAILS}

    assert documented_assumption_names == {
        "available_csm_hours_per_month",
        "csm_count",
        "max_accounts_per_csm",
        "max_accounts_to_contact",
        "max_solver_candidate_pool",
        "tier_1_effectiveness",
        "tier_2_effectiveness",
        "tier_3_effectiveness",
    }
    assert all(rationale for _name, rationale in ASSUMPTION_DETAILS)
