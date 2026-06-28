"""Configuration for deterministic synthetic source-data generation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path

from renewalos.config import RAW_DATA_DIR

CsvRow = dict[str, str]
TableMap = dict[str, list[CsvRow]]

SYNTHETIC_DATA_LABEL = "synthetic_simulated_source_data"
SCENARIO_VERSION = "synthetic_b2b_sources_v1"
RANDOM_SEED = 20260228

SOURCE_TABLES: tuple[str, ...] = (
    "accounts",
    "contracts",
    "billing_events",
    "usage_events",
    "support_tickets",
    "cs_interactions",
    "incident_registry",
)

SOURCE_FILES: dict[str, str] = {
    "accounts": "accounts.csv",
    "contracts": "contracts.csv",
    "billing_events": "billing_events.csv",
    "usage_events": "usage_events.csv",
    "support_tickets": "support_tickets.csv",
    "cs_interactions": "cs_interactions.csv",
    "incident_registry": "incident_registry.csv",
}

REQUIRED_INCIDENT_SCENARIOS: tuple[str, ...] = (
    "duplicate_active_contract",
    "overlapping_contract_period",
    "late_arriving_billing_event",
    "orphaned_billing_event",
    "inconsistent_account_identifier",
    "invalid_negative_arr_movement",
    "active_contract_after_end_date",
    "churned_account_with_active_usage",
    "missing_renewal_date",
    "stale_usage_extract",
    "duplicate_support_ticket",
    "crm_renewal_status_disagrees_with_billing_status",
    "account_missing_segment_or_owner",
    "cs_interaction_logged_to_wrong_account",
)


@dataclass(frozen=True)
class SyntheticDataConfig:
    """Typed settings for the synthetic source-data scenario."""

    random_seed: int
    simulation_start: date
    simulation_months: int
    portfolio_size: int
    output_dir: Path
    scenario_version: str

    @property
    def simulation_end(self) -> date:
        """Last calendar day covered by the simulation window."""

        return add_months(self.simulation_start, self.simulation_months) - timedelta(days=1)

    def month_starts(self) -> tuple[date, ...]:
        """Return first-of-month dates in the simulation window."""

        return tuple(
            add_months(self.simulation_start, index)
            for index in range(self.simulation_months)
        )

    def with_output_dir(self, output_dir: Path) -> SyntheticDataConfig:
        """Return a copy of this config using a different output directory."""

        return replace(self, output_dir=output_dir)


DEFAULT_GENERATION_CONFIG = SyntheticDataConfig(
    random_seed=RANDOM_SEED,
    simulation_start=date(2024, 1, 1),
    simulation_months=24,
    portfolio_size=750,
    output_dir=RAW_DATA_DIR,
    scenario_version=SCENARIO_VERSION,
)


def add_months(value: date, months: int) -> date:
    """Add whole months to a date while preserving the day when possible."""

    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, _days_in_month(year, month))
    return date(year, month, day)


def month_end(value: date) -> date:
    """Return the last day of the month containing the given date."""

    return add_months(date(value.year, value.month, 1), 1) - timedelta(days=1)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day
