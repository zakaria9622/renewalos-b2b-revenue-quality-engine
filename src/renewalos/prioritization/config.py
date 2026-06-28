"""Scenario configuration for synthetic CSM prioritization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from renewalos.config import PROCESSED_DATA_DIR


@dataclass(frozen=True)
class PrioritizationScenario:
    """Explicit simulated assumptions for one prioritization run."""

    scenario_id: str
    assumption_version: str
    available_csm_hours_per_month: float
    csm_count: int
    max_accounts_per_csm: int
    max_accounts_to_contact: int
    max_solver_candidate_pool: int
    objective: str
    output_path: Path

    @property
    def total_account_capacity(self) -> int:
        """Total account-contact capacity implied by CSM count and per-CSM cap."""

        return min(self.max_accounts_to_contact, self.csm_count * self.max_accounts_per_csm)


DEFAULT_PRIORITIZATION_SCENARIO = PrioritizationScenario(
    scenario_id="synthetic_csm_capacity_v1",
    assumption_version="simulated_prioritization_assumptions_v1",
    available_csm_hours_per_month=96.0,
    csm_count=4,
    max_accounts_per_csm=12,
    max_accounts_to_contact=48,
    max_solver_candidate_pool=960,
    objective="maximize_expected_protected_value",
    output_path=PROCESSED_DATA_DIR
    / "prioritization"
    / "csm_prioritization_recommendations.csv",
)

ASSUMPTION_DETAILS: tuple[tuple[str, str], ...] = (
    ("available_csm_hours_per_month", "96 simulated CSM hours available in the month."),
    ("csm_count", "4 simulated CSMs are available for this scenario."),
    ("max_accounts_per_csm", "Each simulated CSM can contact at most 12 accounts."),
    ("max_accounts_to_contact", "The scenario caps outreach recommendations at 48 account-months."),
    ("max_solver_candidate_pool", "OR-Tools evaluates the top 960 eligible account-months."),
    ("tier_1_effectiveness", "Tier 1 assumed intervention effectiveness is 18 percent."),
    ("tier_2_effectiveness", "Tier 2 assumed intervention effectiveness is 10 percent."),
    ("tier_3_effectiveness", "Tier 3 assumed intervention effectiveness is 4 percent."),
)
