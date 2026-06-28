"""Inject controlled data-quality incidents into synthetic source data."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

from renewalos.generation.config import (
    REQUIRED_INCIDENT_SCENARIOS,
    SYNTHETIC_DATA_LABEL,
    CsvRow,
    SyntheticDataConfig,
    TableMap,
    add_months,
    month_end,
)

Severity = str


def inject_controlled_incidents(
    baseline_tables: TableMap,
    config: SyntheticDataConfig,
) -> TableMap:
    """Return a copy of baseline tables with documented incidents injected."""

    tables = _copy_tables(baseline_tables)
    registry: list[CsvRow] = []

    _inject_duplicate_active_contract(tables, registry, config)
    _inject_overlapping_contract_period(tables, registry, config)
    _inject_late_arriving_billing_event(tables, registry, config)
    _inject_orphaned_billing_event(tables, registry, config)
    _inject_inconsistent_account_identifier(tables, registry, config)
    _inject_invalid_negative_arr_movement(tables, registry, config)
    _inject_active_contract_after_end_date(tables, registry, config)
    _inject_churned_account_with_active_usage(tables, registry, config)
    _inject_missing_renewal_date(tables, registry, config)
    _inject_stale_usage_extract(tables, registry, config)
    _inject_duplicate_support_ticket(tables, registry, config)
    _inject_crm_billing_status_disagreement(tables, registry, config)
    _inject_account_missing_segment_or_owner(tables, registry, config)
    _inject_cs_interaction_logged_to_wrong_account(tables, registry, config)

    tables["incident_registry"] = registry
    return tables


def _inject_duplicate_active_contract(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    source = _find_nth(tables["contracts"], lambda row: row["status"] == "active", 0)
    duplicate = source.copy()
    duplicate["contract_id"] = "CON-INC-0001"
    _mark_incident(duplicate, "duplicate_active_contract")
    tables["contracts"].append(duplicate)
    registry.append(
        _registry_row(
            incident_number=1,
            scenario_name="duplicate_active_contract",
            affected_domain="contracts",
            affected_record_identifier=duplicate["contract_id"],
            expected_detection_method="Group active contracts by account, dates, and product tier.",
            expected_business_impact="Can overstate recurring revenue and ARR at risk.",
            severity="high",
            config=config,
        )
    )


def _inject_overlapping_contract_period(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    source = _find_nth(tables["contracts"], lambda row: row["status"] == "active", 1)
    overlap = source.copy()
    original_start = _parse_date(source["contract_start_date"])
    original_end = _parse_date(source["contract_end_date"])
    overlap["contract_id"] = "CON-INC-0002"
    overlap["contract_start_date"] = add_months(original_start, 6).isoformat()
    overlap["contract_end_date"] = add_months(original_end, 6).isoformat()
    overlap["renewal_date"] = overlap["contract_end_date"]
    _mark_incident(overlap, "overlapping_contract_period")
    tables["contracts"].append(overlap)
    registry.append(
        _registry_row(
            incident_number=2,
            scenario_name="overlapping_contract_period",
            affected_domain="contracts",
            affected_record_identifier=overlap["contract_id"],
            expected_detection_method="Check contract date ranges by account for overlaps.",
            expected_business_impact="Can double count revenue or shift renewal timing.",
            severity="high",
            config=config,
        )
    )


def _inject_late_arriving_billing_event(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    contract = _find_nth(tables["contracts"], lambda row: row["status"] == "active", 2)
    effective_date = add_months(config.simulation_start, 10)
    event = _billing_incident_row(
        billing_event_id="BILL-INC-0003",
        account_id=contract["account_id"],
        contract_id=contract["contract_id"],
        event_type="expansion_arr",
        arr_delta="2400",
        amount="2400",
        billing_status="posted",
        event_date=effective_date.isoformat(),
        effective_date=effective_date.isoformat(),
        received_at=(effective_date + timedelta(days=52)).isoformat(),
        scenario_name="late_arriving_billing_event",
        config=config,
    )
    tables["billing_events"].append(event)
    registry.append(
        _registry_row(
            incident_number=3,
            scenario_name="late_arriving_billing_event",
            affected_domain="billing_events",
            affected_record_identifier=event["billing_event_id"],
            expected_detection_method="Compare billing received_at to effective_date.",
            expected_business_impact="Can place revenue movement in the wrong reporting period.",
            severity="medium",
            config=config,
        )
    )


def _inject_orphaned_billing_event(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    event = _billing_incident_row(
        billing_event_id="BILL-INC-0004",
        account_id="ACC-ORPHAN-9999",
        contract_id="CON-MISSING-9999",
        event_type="new_arr",
        arr_delta="18000",
        amount="18000",
        billing_status="posted",
        event_date=add_months(config.simulation_start, 8).isoformat(),
        effective_date=add_months(config.simulation_start, 8).isoformat(),
        received_at=(add_months(config.simulation_start, 8) + timedelta(days=2)).isoformat(),
        scenario_name="orphaned_billing_event",
        config=config,
    )
    tables["billing_events"].append(event)
    registry.append(
        _registry_row(
            incident_number=4,
            scenario_name="orphaned_billing_event",
            affected_domain="billing_events",
            affected_record_identifier=event["billing_event_id"],
            expected_detection_method=(
                "Check billing account_id and contract_id against source keys."
            ),
            expected_business_impact="Breaks source-to-KPI traceability for revenue movement.",
            severity="high",
            config=config,
        )
    )


def _inject_inconsistent_account_identifier(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    usage_row = _find_nth(tables["usage_events"], lambda row: int(row["active_users"]) > 0, 0)
    usage_row["account_id"] = "ACC-ALIAS-0001"
    _mark_incident(usage_row, "inconsistent_account_identifier")
    registry.append(
        _registry_row(
            incident_number=5,
            scenario_name="inconsistent_account_identifier",
            affected_domain="usage_events",
            affected_record_identifier=usage_row["usage_event_id"],
            expected_detection_method="Check usage account_id values against CRM account IDs.",
            expected_business_impact=(
                "Can split activity and health signals away from the real account."
            ),
            severity="high",
            config=config,
        )
    )


def _inject_invalid_negative_arr_movement(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    contract = _find_nth(tables["contracts"], lambda row: row["status"] == "active", 3)
    event = _billing_incident_row(
        billing_event_id="BILL-INC-0006",
        account_id=contract["account_id"],
        contract_id=contract["contract_id"],
        event_type="manual_adjustment",
        arr_delta="-9600",
        amount="9600",
        billing_status="posted",
        event_date=add_months(config.simulation_start, 12).isoformat(),
        effective_date=add_months(config.simulation_start, 12).isoformat(),
        received_at=(add_months(config.simulation_start, 12) + timedelta(days=4)).isoformat(),
        scenario_name="invalid_negative_arr_movement",
        config=config,
    )
    tables["billing_events"].append(event)
    registry.append(
        _registry_row(
            incident_number=6,
            scenario_name="invalid_negative_arr_movement",
            affected_domain="billing_events",
            affected_record_identifier=event["billing_event_id"],
            expected_detection_method=(
                "Flag negative ARR deltas outside approved negative event types."
            ),
            expected_business_impact=(
                "Can make contraction or churn appear without a valid source reason."
            ),
            severity="high",
            config=config,
        )
    )


def _inject_active_contract_after_end_date(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    contract = _find_nth(tables["contracts"], lambda row: row["status"] == "active", 4)
    contract["contract_end_date"] = month_end(add_months(config.simulation_start, 18)).isoformat()
    contract["renewal_date"] = contract["contract_end_date"]
    _mark_incident(contract, "active_contract_after_end_date")
    registry.append(
        _registry_row(
            incident_number=7,
            scenario_name="active_contract_after_end_date",
            affected_domain="contracts",
            affected_record_identifier=contract["contract_id"],
            expected_detection_method="Flag active contracts with end dates before simulation end.",
            expected_business_impact="Can keep expired revenue in active ARR populations.",
            severity="high",
            config=config,
        )
    )


def _inject_churned_account_with_active_usage(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    account = _find_nth(tables["accounts"], lambda row: row["lifecycle_status"] == "churned", 0)
    churn_date = _parse_date(account["churn_date"])
    usage_row = _find_nth(
        tables["usage_events"],
        lambda row: row["account_id"] == account["account_id"]
        and _parse_date(row["activity_month"]) > churn_date,
        0,
    )
    usage_row["active_users"] = "18"
    usage_row["events_count"] = "540"
    usage_row["usage_status"] = "active"
    _mark_incident(usage_row, "churned_account_with_active_usage")
    registry.append(
        _registry_row(
            incident_number=8,
            scenario_name="churned_account_with_active_usage",
            affected_domain="usage_events",
            affected_record_identifier=usage_row["usage_event_id"],
            expected_detection_method="Join churned accounts to post-churn active usage.",
            expected_business_impact=(
                "Can misclassify churn or account identity in health analysis."
            ),
            severity="medium",
            config=config,
        )
    )


def _inject_missing_renewal_date(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    contract = _find_nth(tables["contracts"], lambda row: row["status"] == "active", 5)
    contract["renewal_date"] = ""
    _mark_incident(contract, "missing_renewal_date")
    registry.append(
        _registry_row(
            incident_number=9,
            scenario_name="missing_renewal_date",
            affected_domain="contracts",
            affected_record_identifier=contract["contract_id"],
            expected_detection_method="Flag active contracts with blank renewal_date.",
            expected_business_impact="Can remove accounts from renewal prioritization windows.",
            severity="medium",
            config=config,
        )
    )


def _inject_stale_usage_extract(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    latest_month = add_months(config.simulation_start, config.simulation_months - 1)
    usage_row = _find_nth(
        tables["usage_events"],
        lambda row: (
            row["activity_month"] == latest_month.isoformat()
            and int(row["active_users"]) > 0
        ),
        0,
    )
    usage_row["extract_date"] = config.simulation_start.isoformat()
    _mark_incident(usage_row, "stale_usage_extract")
    registry.append(
        _registry_row(
            incident_number=10,
            scenario_name="stale_usage_extract",
            affected_domain="usage_events",
            affected_record_identifier=usage_row["usage_event_id"],
            expected_detection_method="Compare usage extract_date with activity_month.",
            expected_business_impact=(
                "Can make account-health signals appear current when they are stale."
            ),
            severity="medium",
            config=config,
        )
    )


def _inject_duplicate_support_ticket(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    source = _find_nth(tables["support_tickets"], lambda row: row["ticket_id"] != "", 0)
    duplicate = source.copy()
    duplicate["ticket_id"] = "TICK-INC-0011"
    _mark_incident(duplicate, "duplicate_support_ticket")
    tables["support_tickets"].append(duplicate)
    registry.append(
        _registry_row(
            incident_number=11,
            scenario_name="duplicate_support_ticket",
            affected_domain="support_tickets",
            affected_record_identifier=duplicate["ticket_id"],
            expected_detection_method=(
                "Find repeated ticket attributes by account, time, severity, and category."
            ),
            expected_business_impact="Can overstate support burden in account-health diagnostics.",
            severity="low",
            config=config,
        )
    )


def _inject_crm_billing_status_disagreement(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    contract = _find_nth(tables["contracts"], lambda row: row["status"] == "active", 12)
    account = _find_nth(
        tables["accounts"],
        lambda row: row["account_id"] == contract["account_id"],
        0,
    )
    account["crm_renewal_status"] = "renewed"
    contract["status"] = "cancelled"
    _mark_incident(account, "crm_renewal_status_disagrees_with_billing_status")
    _mark_incident(contract, "crm_renewal_status_disagrees_with_billing_status")
    registry.append(
        _registry_row(
            incident_number=12,
            scenario_name="crm_renewal_status_disagrees_with_billing_status",
            affected_domain="accounts,contracts",
            affected_record_identifier=f"{account['account_id']}|{contract['contract_id']}",
            expected_detection_method="Compare CRM renewal status with contract or billing status.",
            expected_business_impact="Can report a renewal while billing indicates cancellation.",
            severity="high",
            config=config,
        )
    )


def _inject_account_missing_segment_or_owner(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    account = _find_nth(tables["accounts"], lambda row: row["lifecycle_status"] == "active", 1)
    account["segment"] = ""
    account["owner_id"] = ""
    _mark_incident(account, "account_missing_segment_or_owner")
    registry.append(
        _registry_row(
            incident_number=13,
            scenario_name="account_missing_segment_or_owner",
            affected_domain="accounts",
            affected_record_identifier=account["account_id"],
            expected_detection_method="Flag active accounts with missing segment or owner fields.",
            expected_business_impact="Can break segment reporting and CSM assignment.",
            severity="medium",
            config=config,
        )
    )


def _inject_cs_interaction_logged_to_wrong_account(
    tables: TableMap,
    registry: list[CsvRow],
    config: SyntheticDataConfig,
) -> None:
    interaction = _find_nth(tables["cs_interactions"], lambda row: row["interaction_id"] != "", 0)
    interaction["account_id"] = "ACC-WRONG-9999"
    _mark_incident(interaction, "cs_interaction_logged_to_wrong_account")
    registry.append(
        _registry_row(
            incident_number=14,
            scenario_name="cs_interaction_logged_to_wrong_account",
            affected_domain="cs_interactions",
            affected_record_identifier=interaction["interaction_id"],
            expected_detection_method="Check CS interaction account IDs against CRM account IDs.",
            expected_business_impact="Can assign intervention history to the wrong customer.",
            severity="medium",
            config=config,
        )
    )


def _billing_incident_row(
    billing_event_id: str,
    account_id: str,
    contract_id: str,
    event_type: str,
    arr_delta: str,
    amount: str,
    billing_status: str,
    event_date: str,
    effective_date: str,
    received_at: str,
    scenario_name: str,
    config: SyntheticDataConfig,
) -> CsvRow:
    row = {
        "billing_event_id": billing_event_id,
        "account_id": account_id,
        "contract_id": contract_id,
        "event_date": event_date,
        "effective_date": effective_date,
        "received_at": received_at,
        "event_type": event_type,
        "arr_delta": arr_delta,
        "amount": amount,
        "billing_status": billing_status,
        "synthetic_data_label": SYNTHETIC_DATA_LABEL,
        "scenario_version": config.scenario_version,
        "generation_layer": "incident_injection",
        "quality_issue_type": scenario_name,
    }
    return row


def _registry_row(
    incident_number: int,
    scenario_name: str,
    affected_domain: str,
    affected_record_identifier: str,
    expected_detection_method: str,
    expected_business_impact: str,
    severity: Severity,
    config: SyntheticDataConfig,
) -> CsvRow:
    if scenario_name not in REQUIRED_INCIDENT_SCENARIOS:
        raise ValueError(f"Unknown incident scenario: {scenario_name}")
    return {
        "incident_id": f"INC-{incident_number:03d}",
        "scenario_name": scenario_name,
        "affected_domain": affected_domain,
        "affected_record_identifier": affected_record_identifier,
        "injected_at": config.simulation_end.isoformat(),
        "expected_detection_method": expected_detection_method,
        "expected_business_impact": expected_business_impact,
        "severity": severity,
        "synthetic_data_label": SYNTHETIC_DATA_LABEL,
        "scenario_version": config.scenario_version,
    }


def _copy_tables(tables: TableMap) -> TableMap:
    return {table_name: [row.copy() for row in rows] for table_name, rows in tables.items()}


def _mark_incident(row: CsvRow, scenario_name: str) -> None:
    row["generation_layer"] = "incident_injection"
    row["quality_issue_type"] = scenario_name


def _find_nth(rows: list[CsvRow], predicate: Callable[[CsvRow], bool], index: int) -> CsvRow:
    matches = [row for row in rows if predicate(row)]
    if index >= len(matches):
        raise ValueError(f"Could not find incident target at index {index}.")
    return matches[index]


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)
