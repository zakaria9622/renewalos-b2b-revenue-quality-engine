"""Documented constants for RenewalOS diagnostic account-health logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AssessmentStatus = Literal[
    "blocked_due_to_data_quality",
    "not_assessable",
    "eligible_with_caveat",
    "eligible",
]
HealthBand = Literal["critical", "at_risk", "monitor", "stable"]
ImpactDirection = Literal["negative", "neutral", "positive"]
SignalSeverity = Literal["high", "medium", "low", "none"]


@dataclass(frozen=True)
class ComponentThreshold:
    """A documented threshold or mapping for one component."""

    label: str
    score: int
    explanation: str


@dataclass(frozen=True)
class HealthComponent:
    """A transparent account-health component and its simulated assumptions."""

    component_name: str
    max_score: int
    rationale: str
    source_lineage: str
    simulated_assumption: str
    thresholds: tuple[ComponentThreshold, ...]


ASSESSMENT_STATUSES: tuple[AssessmentStatus, ...] = (
    "blocked_due_to_data_quality",
    "not_assessable",
    "eligible_with_caveat",
    "eligible",
)

HEALTH_BANDS: tuple[HealthBand, ...] = ("critical", "at_risk", "monitor", "stable")

HEALTH_BAND_THRESHOLDS: tuple[ComponentThreshold, ...] = (
    ComponentThreshold("critical", 44, "Scores from 0 through 44."),
    ComponentThreshold("at_risk", 64, "Scores from 45 through 64."),
    ComponentThreshold("monitor", 79, "Scores from 65 through 79."),
    ComponentThreshold("stable", 100, "Scores from 80 through 100."),
)

HEALTH_COMPONENTS: tuple[HealthComponent, ...] = (
    HealthComponent(
        component_name="revenue",
        max_score=15,
        rationale=(
            "Revenue evidence affects how much confidence to place in account-health context."
        ),
        source_lineage="mart_revenue_reconciliation_diagnostics",
        simulated_assumption=(
            "Reconciliation gaps reduce diagnostic confidence but do not predict churn."
        ),
        thresholds=(
            ComponentThreshold("no_revenue_concern", 15, "No reconciliation gap is observed."),
            ComponentThreshold(
                "revenue_caveat",
                8,
                "A reconciliation gap or manual adjustment is observed.",
            ),
            ComponentThreshold("revenue_blocked", 0, "Critical quality issues block scoring."),
        ),
    ),
    HealthComponent(
        component_name="renewal",
        max_score=20,
        rationale="Near-term renewal timing can make account-health signals more urgent to review.",
        source_lineage="int_account_month_renewal_signals",
        simulated_assumption="0-30 days is high urgency; 31-90 days is medium urgency.",
        thresholds=(
            ComponentThreshold(
                "high_urgency",
                5,
                "Renewal or contract end date is within 30 days.",
            ),
            ComponentThreshold(
                "medium_urgency",
                10,
                "Renewal or contract end date is within 31-90 days.",
            ),
            ComponentThreshold(
                "low_urgency",
                15,
                "Renewal or contract end date is within 91-180 days.",
            ),
            ComponentThreshold(
                "no_near_term_urgency",
                20,
                "Renewal timing is farther out or inactive.",
            ),
        ),
    ),
    HealthComponent(
        component_name="usage",
        max_score=30,
        rationale="Low or declining product usage is a diagnostic health concern.",
        source_lineage="stg_usage_events",
        simulated_assumption=(
            "Usage concern thresholds are portfolio assumptions, not a trained model."
        ),
        thresholds=(
            ComponentThreshold(
                "high_concern",
                5,
                "Inactive usage or a drop of at least 50 percent.",
            ),
            ComponentThreshold(
                "medium_concern",
                15,
                "Very low usage or a drop of at least 25 percent.",
            ),
            ComponentThreshold(
                "no_observed_concern",
                30,
                "No supported usage concern is observed.",
            ),
        ),
    ),
    HealthComponent(
        component_name="support",
        max_score=20,
        rationale="Recent support burden can indicate friction in the customer experience.",
        source_lineage="stg_support_tickets",
        simulated_assumption="90-day support burden thresholds are simulated review assumptions.",
        thresholds=(
            ComponentThreshold("high_concern", 5, "High-severity or heavy open support burden."),
            ComponentThreshold("medium_concern", 12, "Moderate recent support burden."),
            ComponentThreshold(
                "no_observed_concern",
                20,
                "No supported support concern is observed.",
            ),
        ),
    ),
    HealthComponent(
        component_name="customer_success",
        max_score=15,
        rationale="Recent Customer Success coverage and sentiment provide diagnostic context.",
        source_lineage="stg_cs_interactions",
        simulated_assumption=(
            "CS engagement recency is a simulated review signal, not an outcome claim."
        ),
        thresholds=(
            ComponentThreshold("high_concern", 3, "Concerned sentiment is logged recently."),
            ComponentThreshold("medium_concern", 8, "No recent CS interaction is observed."),
            ComponentThreshold(
                "no_observed_concern",
                15,
                "Recent CS engagement has no concern signal.",
            ),
        ),
    ),
)

REQUIRED_EXPLANATION_COMPONENTS: tuple[str, ...] = tuple(
    component.component_name for component in HEALTH_COMPONENTS
)

TOTAL_HEALTH_SCORE: int = sum(component.max_score for component in HEALTH_COMPONENTS)
