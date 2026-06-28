"""Validation helpers for the RenewalOS Streamlit evidence layer."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import duckdb

from renewalos.prioritization.config import DEFAULT_PRIORITIZATION_SCENARIO
from renewalos.warehouse.load_raw import WAREHOUSE_DB_PATH


class AppDataError(RuntimeError):
    """Raised when the local app cannot read required generated outputs."""


REQUIRED_WAREHOUSE_TABLES: tuple[str, ...] = (
    "main.mart_kpi_trust_status",
    "main.dq_account_month_quality_status",
    "main.dq_incident_detection_coverage",
    "main.dq_contract_exceptions",
    "main.dq_billing_exceptions",
    "main.dq_usage_exceptions",
    "main.dq_support_exceptions",
    "main.dq_identifier_exceptions",
    "main.mart_revenue_reconciliation_diagnostics",
    "main.mart_account_health",
    "main.mart_account_health_explanations",
    "main.mart_account_health_coverage",
    "main.mart_csm_priority_candidates",
    "main.mart_csm_prioritization_inputs",
)

REQUIRED_PRIORITY_EXPORT_COLUMNS: tuple[str, ...] = (
    "account_id",
    "account_month",
    "is_selected",
    "recommendation_status",
    "scenario_id",
    "assumption_version",
    "assumption_label",
    "assessment_status",
    "quality_status",
    "expected_protected_value",
    "estimated_effort_hours",
    "selection_reason",
    "non_selection_reason",
    "explanation_drivers",
)


@dataclass(frozen=True)
class WarehouseValidationResult:
    """Result of checking whether the local warehouse is readable for the app."""

    database_path: Path
    required_tables: tuple[str, ...]
    existing_tables: tuple[str, ...]


def validate_warehouse_ready(
    database_path: Path = WAREHOUSE_DB_PATH,
    required_tables: Sequence[str] = REQUIRED_WAREHOUSE_TABLES,
) -> WarehouseValidationResult:
    """Validate that the local DuckDB warehouse and required dbt outputs exist."""

    database_path = database_path.resolve()
    if not database_path.is_file():
        raise AppDataError(
            "Warehouse database not found. Run renewalos-generate-raw, "
            "renewalos-load-raw, then dbt run before opening the app. "
            f"Expected path: {database_path}"
        )

    try:
        with duckdb.connect(str(database_path), read_only=True) as connection:
            rows = cast(
                list[tuple[str, str]],
                connection.execute(
                    """
                    select table_schema, table_name
                    from information_schema.tables
                    where table_schema in ('main', 'raw')
                    """
                ).fetchall(),
            )
    except duckdb.Error as error:
        message = f"Could not open DuckDB warehouse at {database_path}: {error}"
        raise AppDataError(message) from error

    existing_tables = tuple(sorted(f"{schema}.{table}" for schema, table in rows))
    missing_tables = sorted(set(required_tables) - set(existing_tables))
    if missing_tables:
        missing = ", ".join(missing_tables)
        raise AppDataError(
            "Required warehouse table(s) missing. Run dbt run from the dbt directory "
            f"before opening the app. Missing: {missing}"
        )

    return WarehouseValidationResult(
        database_path=database_path,
        required_tables=tuple(required_tables),
        existing_tables=existing_tables,
    )


def load_priority_export_records(
    output_path: Path = DEFAULT_PRIORITIZATION_SCENARIO.output_path,
) -> list[dict[str, str]]:
    """Load the generated prioritization CSV as plain records."""

    output_path = output_path.resolve()
    if not output_path.is_file():
        raise AppDataError(
            "Prioritization export not found. Run renewalos-run-prioritization before "
            f"opening the CSM Prioritization page. Expected path: {output_path}"
        )
    with output_path.open("r", encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def validate_priority_export_records(
    records: Sequence[Mapping[str, Any]],
    required_columns: Iterable[str] = REQUIRED_PRIORITY_EXPORT_COLUMNS,
) -> None:
    """Validate generated prioritization rows for app display and CSV export."""

    if not records:
        raise AppDataError("Prioritization export is empty.")

    observed_columns = set(records[0])
    missing_columns = sorted(set(required_columns) - observed_columns)
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise AppDataError(f"Prioritization export is missing required column(s): {missing}")

    for record in records:
        if str(record.get("scenario_id")) != DEFAULT_PRIORITIZATION_SCENARIO.scenario_id:
            raise AppDataError("Prioritization export contains missing or unexpected scenario_id.")
        if (
            str(record.get("assumption_version"))
            != DEFAULT_PRIORITIZATION_SCENARIO.assumption_version
        ):
            raise AppDataError(
                "Prioritization export contains missing or unexpected assumption_version."
            )
        if (
            str(record.get("assumption_label"))
            != "simulated_scenario_assumption_not_observed_effect"
        ):
            raise AppDataError("Prioritization export is missing the simulated assumption label.")
        if str(record.get("recommendation_status")) == "selected":
            if str(record.get("assessment_status")) in {
                "blocked_due_to_data_quality",
                "not_assessable",
            }:
                raise AppDataError("Blocked or not-assessable account-month selected.")
            if str(record.get("quality_status")) == "blocked":
                raise AppDataError("Quality-blocked account-month selected.")
