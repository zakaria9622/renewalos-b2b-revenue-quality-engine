"""Validate RenewalOS quality-control dbt outputs."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import duckdb

from renewalos.quality.quality_constants import EXPECTED_INCIDENT_SCENARIOS, QUALITY_STATUSES
from renewalos.warehouse.load_raw import WAREHOUSE_DB_PATH


class QualityValidationError(RuntimeError):
    """Raised when quality-control outputs are absent or incomplete."""


@dataclass(frozen=True)
class QualityValidationResult:
    """Summary of quality-control validation checks."""

    detected_incident_count: int
    exception_count: int
    nonzero_reconciliation_gap_count: int
    detection_status_counts: dict[str, int]
    quality_status_counts: dict[str, int]
    reconciliation_status_counts: dict[str, int]


def validate_quality_outputs(database_path: Path = WAREHOUSE_DB_PATH) -> QualityValidationResult:
    """Validate quality-control dbt outputs in a built RenewalOS DuckDB database."""

    database_path = database_path.resolve()
    if not database_path.is_file():
        raise QualityValidationError(f"DuckDB database does not exist: {database_path}")

    with duckdb.connect(str(database_path), read_only=True) as connection:
        _ensure_tables_exist(
            connection,
            required_tables=(
                "dq_contract_exceptions",
                "dq_billing_exceptions",
                "dq_usage_exceptions",
                "dq_support_exceptions",
                "dq_identifier_exceptions",
                "dq_incident_detection_coverage",
                "dq_account_month_quality_status",
                "mart_revenue_reconciliation_diagnostics",
                "mart_kpi_trust_status",
            ),
        )
        _validate_incident_coverage(connection)
        exception_count = _validate_exception_metadata(connection)
        quality_status_counts = _validate_quality_statuses(connection)
        nonzero_gap_count = _validate_reconciliation_gaps(connection)

        detection_status_counts = _fetch_counts(
            connection,
            """
            select detection_status, count(*)
            from main.dq_incident_detection_coverage
            group by detection_status
            order by detection_status
            """,
        )
        reconciliation_status_counts = _fetch_counts(
            connection,
            """
            select reconciliation_status, count(*)
            from main.mart_revenue_reconciliation_diagnostics
            group by reconciliation_status
            order by reconciliation_status
            """,
        )

    return QualityValidationResult(
        detected_incident_count=detection_status_counts.get("detected", 0),
        exception_count=exception_count,
        nonzero_reconciliation_gap_count=nonzero_gap_count,
        detection_status_counts=detection_status_counts,
        quality_status_counts=quality_status_counts,
        reconciliation_status_counts=reconciliation_status_counts,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for quality-control validation."""

    parser = argparse.ArgumentParser(description="Validate RenewalOS quality-control outputs.")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=WAREHOUSE_DB_PATH,
        help="Built DuckDB database containing dbt quality models.",
    )
    args = parser.parse_args(argv)

    result = validate_quality_outputs(database_path=args.database_path)
    print("RenewalOS quality-control validation passed.")
    print(f"detected_incident_count: {result.detected_incident_count}")
    print(f"exception_count: {result.exception_count}")
    print(f"nonzero_reconciliation_gap_count: {result.nonzero_reconciliation_gap_count}")
    print(f"detection_status_counts: {result.detection_status_counts}")
    print(f"quality_status_counts: {result.quality_status_counts}")
    print(f"reconciliation_status_counts: {result.reconciliation_status_counts}")
    return 0


def _ensure_tables_exist(
    connection: duckdb.DuckDBPyConnection,
    required_tables: Sequence[str],
) -> None:
    rows = cast(
        list[tuple[str]],
        connection.execute(
            """
            select table_name
            from information_schema.tables
            where table_schema = 'main'
            """
        ).fetchall(),
    )
    existing_tables = {row[0] for row in rows}
    missing_tables = sorted(set(required_tables) - existing_tables)
    if missing_tables:
        missing = ", ".join(missing_tables)
        raise QualityValidationError(f"Missing built quality-control table(s): {missing}")


def _validate_incident_coverage(connection: duckdb.DuckDBPyConnection) -> None:
    rows = cast(
        list[tuple[str, str]],
        connection.execute(
            """
            select scenario_name, detection_status
            from main.dq_incident_detection_coverage
            """
        ).fetchall(),
    )
    detected_by_scenario = {
        scenario_name
        for scenario_name, detection_status in rows
        if detection_status == "detected"
    }
    missing_scenarios = sorted(set(EXPECTED_INCIDENT_SCENARIOS) - detected_by_scenario)
    if missing_scenarios:
        missing = ", ".join(missing_scenarios)
        raise QualityValidationError(f"Incident scenario(s) not detected: {missing}")


def _validate_exception_metadata(connection: duckdb.DuckDBPyConnection) -> int:
    row = cast(
        tuple[int, int],
        connection.execute(
            """
            with exceptions as (
                select * from main.dq_contract_exceptions
                union all
                select * from main.dq_billing_exceptions
                union all
                select * from main.dq_usage_exceptions
                union all
                select * from main.dq_support_exceptions
                union all
                select * from main.dq_identifier_exceptions
            )
            select
                count(*) as exception_count,
                sum(
                    case
                        when rule_id is null
                            or severity is null
                            or source_domain is null
                            or affected_record_identifier is null
                            or scenario_name is null
                            then 1
                        else 0
                    end
                ) as missing_metadata_count
            from exceptions
            """
        ).fetchone(),
    )
    exception_count, missing_metadata_count = row
    if exception_count == 0:
        raise QualityValidationError("No quality exceptions were produced.")
    if missing_metadata_count > 0:
        raise QualityValidationError("Detected quality exceptions have missing metadata.")
    return exception_count


def _validate_quality_statuses(connection: duckdb.DuckDBPyConnection) -> dict[str, int]:
    status_counts = _fetch_counts(
        connection,
        """
        select quality_status, count(*)
        from main.dq_account_month_quality_status
        group by quality_status
        order by quality_status
        """,
    )
    observed_statuses = set(status_counts)
    unexpected_statuses = sorted(observed_statuses - set(QUALITY_STATUSES))
    if unexpected_statuses:
        unexpected = ", ".join(unexpected_statuses)
        raise QualityValidationError(f"Unexpected account-month quality status(es): {unexpected}")
    for required_status in ("blocked", "warning", "eligible_with_caveat"):
        if status_counts.get(required_status, 0) == 0:
            raise QualityValidationError(
                f"No account-month rows produced required status: {required_status}"
            )
    return status_counts


def _validate_reconciliation_gaps(connection: duckdb.DuckDBPyConnection) -> int:
    row = cast(
        tuple[int],
        connection.execute(
            """
            select count(*)
            from main.mart_revenue_reconciliation_diagnostics
            where reconciliation_gap_amount is not null
                and abs(reconciliation_gap_amount) > 0.01
            """
        ).fetchone(),
    )
    nonzero_gap_count = row[0]
    if nonzero_gap_count == 0:
        raise QualityValidationError("No nonzero reconciliation gaps are observable.")
    return nonzero_gap_count


def _fetch_counts(
    connection: duckdb.DuckDBPyConnection,
    query: str,
) -> dict[str, int]:
    rows = cast(list[tuple[Any, Any]], connection.execute(query).fetchall())
    return {str(label): int(count) for label, count in rows}


if __name__ == "__main__":
    raise SystemExit(main())
