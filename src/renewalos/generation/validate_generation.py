"""Write and validate synthetic RenewalOS raw source CSV files."""

from __future__ import annotations

import argparse
import csv
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from renewalos.generation.config import (
    DEFAULT_GENERATION_CONFIG,
    REQUIRED_INCIDENT_SCENARIOS,
    SOURCE_FILES,
    CsvRow,
    SyntheticDataConfig,
    TableMap,
)
from renewalos.generation.generate_baseline import generate_baseline
from renewalos.generation.inject_incidents import inject_controlled_incidents

VALID_NEGATIVE_ARR_EVENT_TYPES = frozenset({"contraction_arr", "churned_arr"})


@dataclass(frozen=True)
class GenerationResult:
    """Summary of a completed synthetic source-data generation run."""

    output_dir: Path
    record_counts: dict[str, int]
    incident_counts: dict[str, int]


def generate_raw_data(
    config: SyntheticDataConfig = DEFAULT_GENERATION_CONFIG,
) -> GenerationResult:
    """Generate baseline data, inject controlled incidents, write CSVs, and validate."""

    baseline_tables = generate_baseline(config)
    generated_tables = inject_controlled_incidents(baseline_tables, config)
    write_tables(generated_tables, config.output_dir)
    tables_from_disk = read_tables(config.output_dir)
    incident_counts = validate_generated_tables(tables_from_disk, config)
    return GenerationResult(
        output_dir=config.output_dir,
        record_counts={table_name: len(rows) for table_name, rows in tables_from_disk.items()},
        incident_counts=incident_counts,
    )


def validate_generated_tables(
    tables: TableMap,
    config: SyntheticDataConfig,
) -> dict[str, int]:
    """Validate expected files, layers, registry rows, and intentional incidents."""

    missing_tables = [table_name for table_name in SOURCE_FILES if table_name not in tables]
    if missing_tables:
        raise ValueError(f"Missing generated tables: {', '.join(missing_tables)}")

    if not _has_generation_layer(tables, "baseline"):
        raise ValueError("Baseline generation layer was not found in generated data.")
    if not _has_generation_layer(tables, "incident_injection"):
        raise ValueError("Incident injection layer was not found in generated data.")

    registry = tables["incident_registry"]
    registry_scenarios = {row["scenario_name"] for row in registry}
    missing_registry_scenarios = [
        scenario for scenario in REQUIRED_INCIDENT_SCENARIOS if scenario not in registry_scenarios
    ]
    if len(registry) < 12 or missing_registry_scenarios:
        raise ValueError(
            "Incident registry is missing required scenarios: "
            + ", ".join(missing_registry_scenarios)
        )

    incident_counts = detect_intentional_incidents(tables, config)
    missing_detected_scenarios = [
        scenario
        for scenario in REQUIRED_INCIDENT_SCENARIOS
        if incident_counts.get(scenario, 0) < 1
    ]
    if missing_detected_scenarios:
        raise ValueError(
            "Generated data does not contain expected intentional problems: "
            + ", ".join(missing_detected_scenarios)
        )

    return incident_counts


def detect_intentional_incidents(
    tables: TableMap,
    config: SyntheticDataConfig,
) -> dict[str, int]:
    """Return lightweight detector counts for the documented incident categories."""

    account_ids = {row["account_id"] for row in tables["accounts"]}
    contract_ids = {row["contract_id"] for row in tables["contracts"]}

    return {
        "duplicate_active_contract": _count_duplicate_active_contracts(tables["contracts"]),
        "overlapping_contract_period": _count_overlapping_contracts(tables["contracts"]),
        "late_arriving_billing_event": _count_late_billing_events(tables["billing_events"]),
        "orphaned_billing_event": _count_orphaned_billing_events(
            tables["billing_events"], account_ids, contract_ids
        ),
        "inconsistent_account_identifier": _count_inconsistent_account_ids(
            tables, account_ids
        ),
        "invalid_negative_arr_movement": _count_invalid_negative_arr_movements(
            tables["billing_events"]
        ),
        "active_contract_after_end_date": _count_active_contracts_after_end(
            tables["contracts"], config
        ),
        "churned_account_with_active_usage": _count_churned_accounts_with_active_usage(
            tables
        ),
        "missing_renewal_date": _count_missing_renewal_dates(tables["contracts"]),
        "stale_usage_extract": _count_stale_usage_extracts(tables["usage_events"]),
        "duplicate_support_ticket": _count_duplicate_support_tickets(
            tables["support_tickets"]
        ),
        "crm_renewal_status_disagrees_with_billing_status": _count_crm_billing_disagreements(
            tables
        ),
        "account_missing_segment_or_owner": _count_accounts_missing_segment_or_owner(
            tables["accounts"]
        ),
        "cs_interaction_logged_to_wrong_account": _count_wrong_account_cs_interactions(
            tables["cs_interactions"], account_ids
        ),
    }


def write_tables(tables: TableMap, output_dir: Path) -> None:
    """Write source-domain CSV files to the configured output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name, filename in SOURCE_FILES.items():
        rows = tables[table_name]
        path = output_dir / filename
        fieldnames = list(rows[0].keys()) if rows else []
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def read_tables(output_dir: Path) -> TableMap:
    """Read generated CSV files from disk for validation or tests."""

    tables: TableMap = {}
    for table_name, filename in SOURCE_FILES.items():
        path = output_dir / filename
        if not path.is_file():
            raise ValueError(f"Expected generated file is missing: {path}")
        with path.open("r", newline="", encoding="utf-8") as handle:
            tables[table_name] = [dict(row) for row in csv.DictReader(handle)]
    return tables


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for reproducible raw synthetic source-data generation."""

    parser = argparse.ArgumentParser(description="Generate RenewalOS synthetic raw source CSVs.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_GENERATION_CONFIG.output_dir,
        help="Directory where raw CSV files should be written.",
    )
    args = parser.parse_args(argv)
    config = DEFAULT_GENERATION_CONFIG.with_output_dir(args.output_dir)
    result = generate_raw_data(config)

    print(f"Synthetic RenewalOS raw data generated in: {result.output_dir}")
    print(f"scenario_version: {config.scenario_version}")
    print(f"random_seed: {config.random_seed}")
    for table_name in SOURCE_FILES:
        print(f"{table_name}: {result.record_counts[table_name]}")
    print("incident_counts:")
    for scenario_name in REQUIRED_INCIDENT_SCENARIOS:
        print(f"  {scenario_name}: {result.incident_counts[scenario_name]}")
    return 0


def _has_generation_layer(tables: TableMap, generation_layer: str) -> bool:
    for table_name, rows in tables.items():
        if table_name == "incident_registry":
            continue
        if any(row["generation_layer"] == generation_layer for row in rows):
            return True
    return False


def _count_duplicate_active_contracts(contracts: list[CsvRow]) -> int:
    groups: dict[tuple[str, str, str, str], int] = {}
    for contract in contracts:
        if contract["status"] != "active":
            continue
        key = (
            contract["account_id"],
            contract["contract_start_date"],
            contract["contract_end_date"],
            contract["product_tier"],
        )
        groups[key] = groups.get(key, 0) + 1
    return sum(count - 1 for count in groups.values() if count > 1)


def _count_overlapping_contracts(contracts: list[CsvRow]) -> int:
    by_account: dict[str, list[CsvRow]] = {}
    for contract in contracts:
        by_account.setdefault(contract["account_id"], []).append(contract)

    overlap_count = 0
    for account_contracts in by_account.values():
        sorted_contracts = sorted(account_contracts, key=lambda row: row["contract_start_date"])
        for index, current in enumerate(sorted_contracts):
            current_start = _parse_date(current["contract_start_date"])
            current_end = _parse_date(current["contract_end_date"])
            for other in sorted_contracts[index + 1 :]:
                other_start = _parse_date(other["contract_start_date"])
                other_end = _parse_date(other["contract_end_date"])
                if current_start <= other_end and other_start <= current_end:
                    overlap_count += 1
    return overlap_count


def _count_late_billing_events(billing_events: list[CsvRow]) -> int:
    return sum(
        1
        for event in billing_events
        if (_parse_date(event["received_at"]) - _parse_date(event["effective_date"])).days > 30
    )


def _count_orphaned_billing_events(
    billing_events: list[CsvRow],
    account_ids: set[str],
    contract_ids: set[str],
) -> int:
    return sum(
        1
        for event in billing_events
        if event["account_id"] not in account_ids or event["contract_id"] not in contract_ids
    )


def _count_inconsistent_account_ids(tables: TableMap, account_ids: set[str]) -> int:
    count = 0
    for table_name in ("usage_events", "support_tickets", "cs_interactions"):
        count += sum(1 for row in tables[table_name] if row["account_id"] not in account_ids)
    return count


def _count_invalid_negative_arr_movements(billing_events: list[CsvRow]) -> int:
    return sum(
        1
        for event in billing_events
        if int(event["arr_delta"]) < 0 and event["event_type"] not in VALID_NEGATIVE_ARR_EVENT_TYPES
    )


def _count_active_contracts_after_end(
    contracts: list[CsvRow],
    config: SyntheticDataConfig,
) -> int:
    return sum(
        1
        for contract in contracts
        if contract["status"] == "active"
        and _parse_date(contract["contract_end_date"]) < config.simulation_end
    )


def _count_churned_accounts_with_active_usage(tables: TableMap) -> int:
    churn_dates = {
        row["account_id"]: _parse_date(row["churn_date"])
        for row in tables["accounts"]
        if row["lifecycle_status"] == "churned" and row["churn_date"]
    }
    return sum(
        1
        for usage in tables["usage_events"]
        if usage["account_id"] in churn_dates
        and _parse_date(usage["activity_month"]) > churn_dates[usage["account_id"]]
        and int(usage["active_users"]) > 0
    )


def _count_missing_renewal_dates(contracts: list[CsvRow]) -> int:
    return sum(1 for contract in contracts if contract["renewal_date"] == "")


def _count_stale_usage_extracts(usage_events: list[CsvRow]) -> int:
    return sum(
        1
        for usage in usage_events
        if _parse_date(usage["extract_date"]) < _parse_date(usage["activity_month"])
    )


def _count_duplicate_support_tickets(support_tickets: list[CsvRow]) -> int:
    groups: dict[tuple[str, str, str, str], int] = {}
    for ticket in support_tickets:
        key = (
            ticket["account_id"],
            ticket["created_at"],
            ticket["severity"],
            ticket["category"],
        )
        groups[key] = groups.get(key, 0) + 1
    return sum(count - 1 for count in groups.values() if count > 1)


def _count_crm_billing_disagreements(tables: TableMap) -> int:
    renewed_account_ids = {
        row["account_id"] for row in tables["accounts"] if row["crm_renewal_status"] == "renewed"
    }
    return sum(
        1
        for contract in tables["contracts"]
        if contract["account_id"] in renewed_account_ids and contract["status"] == "cancelled"
    )


def _count_accounts_missing_segment_or_owner(accounts: list[CsvRow]) -> int:
    return sum(1 for account in accounts if account["segment"] == "" or account["owner_id"] == "")


def _count_wrong_account_cs_interactions(
    cs_interactions: list[CsvRow],
    account_ids: set[str],
) -> int:
    return sum(1 for interaction in cs_interactions if interaction["account_id"] not in account_ids)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


if __name__ == "__main__":
    raise SystemExit(main())
