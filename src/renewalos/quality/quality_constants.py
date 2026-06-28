"""Shared constants for RenewalOS quality-control outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["critical", "warning"]
QualityStatus = Literal["blocked", "warning", "eligible_with_caveat", "no_observed_issue"]
DetectionStatus = Literal["detected", "not_detected"]


@dataclass(frozen=True)
class QualityRule:
    """Documented quality rule expected from the dbt quality layer."""

    rule_id: str
    scenario_name: str
    source_domain: str
    severity: Severity
    expected_detection_method: str


QUALITY_RULES: tuple[QualityRule, ...] = (
    QualityRule(
        rule_id="DQ_CONTRACT_DUPLICATE_ACTIVE",
        scenario_name="duplicate_active_contract",
        source_domain="contracts",
        severity="critical",
        expected_detection_method=(
            "Find active contracts for the same account with overlapping periods."
        ),
    ),
    QualityRule(
        rule_id="DQ_CONTRACT_OVERLAPPING_PERIOD",
        scenario_name="overlapping_contract_period",
        source_domain="contracts",
        severity="critical",
        expected_detection_method=(
            "Find contract periods for the same account with overlapping dates."
        ),
    ),
    QualityRule(
        rule_id="DQ_BILLING_LATE_ARRIVAL",
        scenario_name="late_arriving_billing_event",
        source_domain="billing_events",
        severity="warning",
        expected_detection_method="Compare billing effective dates with received dates.",
    ),
    QualityRule(
        rule_id="DQ_BILLING_ORPHANED_EVENT",
        scenario_name="orphaned_billing_event",
        source_domain="billing_events",
        severity="critical",
        expected_detection_method=(
            "Check billing account and contract references against source records."
        ),
    ),
    QualityRule(
        rule_id="DQ_IDENTIFIER_INCONSISTENT_ACCOUNT_ID",
        scenario_name="inconsistent_account_identifier",
        source_domain="usage_events",
        severity="critical",
        expected_detection_method="Check source-domain account IDs against CRM account IDs.",
    ),
    QualityRule(
        rule_id="DQ_BILLING_INVALID_NEGATIVE_ARR",
        scenario_name="invalid_negative_arr_movement",
        source_domain="billing_events",
        severity="critical",
        expected_detection_method=(
            "Find negative recurring movements outside approved contraction/churn types."
        ),
    ),
    QualityRule(
        rule_id="DQ_CONTRACT_ACTIVE_AFTER_END",
        scenario_name="active_contract_after_end_date",
        source_domain="contracts",
        severity="critical",
        expected_detection_method=(
            "Find active contracts whose end date precedes the observed reporting window."
        ),
    ),
    QualityRule(
        rule_id="DQ_USAGE_CHURNED_ACCOUNT_ACTIVE",
        scenario_name="churned_account_with_active_usage",
        source_domain="usage_events",
        severity="warning",
        expected_detection_method="Find churned accounts with active usage after the churn date.",
    ),
    QualityRule(
        rule_id="DQ_CONTRACT_MISSING_RENEWAL_DATE",
        scenario_name="missing_renewal_date",
        source_domain="contracts",
        severity="warning",
        expected_detection_method="Find active contracts or accounts without a renewal date.",
    ),
    QualityRule(
        rule_id="DQ_USAGE_STALE_EXTRACT",
        scenario_name="stale_usage_extract",
        source_domain="usage_events",
        severity="warning",
        expected_detection_method="Compare usage extract dates with activity months.",
    ),
    QualityRule(
        rule_id="DQ_SUPPORT_DUPLICATE_TICKET",
        scenario_name="duplicate_support_ticket",
        source_domain="support_tickets",
        severity="warning",
        expected_detection_method=(
            "Find repeated ticket attributes by account, time, severity, and category."
        ),
    ),
    QualityRule(
        rule_id="DQ_CONTRACT_CRM_BILLING_STATUS_DISAGREEMENT",
        scenario_name="crm_renewal_status_disagrees_with_billing_status",
        source_domain="accounts,contracts",
        severity="critical",
        expected_detection_method="Compare CRM renewal status with contract or billing status.",
    ),
    QualityRule(
        rule_id="DQ_IDENTIFIER_ACCOUNT_MISSING_SEGMENT_OR_OWNER",
        scenario_name="account_missing_segment_or_owner",
        source_domain="accounts",
        severity="warning",
        expected_detection_method="Flag active accounts with missing segment or owner fields.",
    ),
    QualityRule(
        rule_id="DQ_IDENTIFIER_CS_WRONG_ACCOUNT",
        scenario_name="cs_interaction_logged_to_wrong_account",
        source_domain="cs_interactions",
        severity="warning",
        expected_detection_method="Check CS interaction account IDs against CRM account IDs.",
    ),
)

EXPECTED_INCIDENT_SCENARIOS: tuple[str, ...] = tuple(
    rule.scenario_name for rule in QUALITY_RULES
)

QUALITY_STATUSES: tuple[QualityStatus, ...] = (
    "blocked",
    "warning",
    "eligible_with_caveat",
    "no_observed_issue",
)

DETECTION_STATUSES: tuple[DetectionStatus, ...] = ("detected", "not_detected")
