"""Validate RenewalOS diagnostic account-health outputs."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import duckdb

from renewalos.health.health_constants import (
    ASSESSMENT_STATUSES,
    HEALTH_BANDS,
    REQUIRED_EXPLANATION_COMPONENTS,
)
from renewalos.warehouse.load_raw import WAREHOUSE_DB_PATH


class HealthValidationError(RuntimeError):
    """Raised when account-health outputs are absent or violate gate rules."""


@dataclass(frozen=True)
class HealthValidationResult:
    """Summary of diagnostic account-health validation checks."""

    assessment_status_counts: dict[str, int]
    health_band_counts: dict[str, int]
    scored_account_month_count: int
    explanation_count: int


def validate_health_outputs(database_path: Path = WAREHOUSE_DB_PATH) -> HealthValidationResult:
    """Validate built account-health dbt outputs."""

    database_path = database_path.resolve()
    if not database_path.is_file():
        raise HealthValidationError(f"DuckDB database does not exist: {database_path}")

    with duckdb.connect(str(database_path), read_only=True) as connection:
        _ensure_tables_exist(
            connection,
            required_tables=(
                "int_account_month_operational_signals",
                "int_account_month_renewal_signals",
                "mart_account_health",
                "mart_account_health_explanations",
                "mart_account_health_coverage",
            ),
        )
        _validate_statuses(connection)
        _validate_quality_gate(connection)
        scored_count = _validate_scored_rows(connection)
        explanation_count = _validate_explanations(connection)
        _validate_coverage(connection)
        assessment_status_counts = _fetch_counts(
            connection,
            """
            select assessment_status, count(*)
            from main.mart_account_health
            group by assessment_status
            order by assessment_status
            """,
        )
        health_band_counts = _fetch_counts(
            connection,
            """
            select health_band, count(*)
            from main.mart_account_health
            where health_band is not null
            group by health_band
            order by health_band
            """,
        )

    return HealthValidationResult(
        assessment_status_counts=assessment_status_counts,
        health_band_counts=health_band_counts,
        scored_account_month_count=scored_count,
        explanation_count=explanation_count,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for diagnostic account-health validation."""

    parser = argparse.ArgumentParser(description="Validate RenewalOS account-health outputs.")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=WAREHOUSE_DB_PATH,
        help="Built DuckDB database containing dbt account-health models.",
    )
    args = parser.parse_args(argv)

    result = validate_health_outputs(database_path=args.database_path)
    print("RenewalOS account-health validation passed.")
    print(f"assessment_status_counts: {result.assessment_status_counts}")
    print(f"health_band_counts: {result.health_band_counts}")
    print(f"scored_account_month_count: {result.scored_account_month_count}")
    print(f"explanation_count: {result.explanation_count}")
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
        raise HealthValidationError(f"Missing built account-health table(s): {missing}")


def _validate_statuses(connection: duckdb.DuckDBPyConnection) -> None:
    status_counts = _fetch_counts(
        connection,
        """
        select assessment_status, count(*)
        from main.mart_account_health
        group by assessment_status
        """,
    )
    unexpected_statuses = sorted(set(status_counts) - set(ASSESSMENT_STATUSES))
    if unexpected_statuses:
        unexpected = ", ".join(unexpected_statuses)
        raise HealthValidationError(f"Unexpected assessment status(es): {unexpected}")
    expected_statuses: set[str] = set(ASSESSMENT_STATUSES)
    observed_statuses: set[str] = set(status_counts)
    missing_statuses = sorted(expected_statuses - observed_statuses)
    if missing_statuses:
        missing = ", ".join(missing_statuses)
        raise HealthValidationError(f"Assessment status(es) not represented: {missing}")


def _validate_quality_gate(connection: duckdb.DuckDBPyConnection) -> None:
    row = cast(
        tuple[int],
        connection.execute(
            """
            select count(*)
            from main.mart_account_health as health
            inner join main.dq_account_month_quality_status as quality_status
                on health.account_id = quality_status.account_id
                and health.account_month = quality_status.account_month
            where health.quality_status <> quality_status.quality_status
                or (
                    quality_status.quality_status = 'blocked'
                    and (
                        health.assessment_status <> 'blocked_due_to_data_quality'
                        or health.health_score is not null
                    )
                )
            """
        ).fetchone(),
    )
    if row[0] > 0:
        raise HealthValidationError("Account-health output bypasses the quality gate.")


def _validate_scored_rows(connection: duckdb.DuckDBPyConnection) -> int:
    row = cast(
        tuple[int, int],
        connection.execute(
            """
            select
                count(*) filter (where health_score is not null) as scored_count,
                count(*) filter (
                    where assessment_status in (
                        'blocked_due_to_data_quality',
                        'not_assessable'
                    )
                    and (health_score is not null or health_band is not null)
                ) as invalid_blocked_or_not_assessable_count
            from main.mart_account_health
            """
        ).fetchone(),
    )
    scored_count, invalid_count = row
    if scored_count == 0:
        raise HealthValidationError("No account-health rows received a diagnostic score.")
    if invalid_count > 0:
        raise HealthValidationError("Blocked or not-assessable account-months were scored.")

    band_rows = cast(
        list[tuple[str]],
        connection.execute(
            """
            select distinct health_band
            from main.mart_account_health
            where health_band is not null
            """
        ).fetchall(),
    )
    unexpected_bands = sorted({row[0] for row in band_rows} - set(HEALTH_BANDS))
    if unexpected_bands:
        unexpected = ", ".join(unexpected_bands)
        raise HealthValidationError(f"Unexpected health band(s): {unexpected}")
    return scored_count


def _validate_explanations(connection: duckdb.DuckDBPyConnection) -> int:
    missing_rows = cast(
        list[tuple[str, Any]],
        connection.execute(
            """
            with required_components(component_name) as (
                values
                    ('revenue'),
                    ('renewal'),
                    ('usage'),
                    ('support'),
                    ('customer_success')
            ),
            scored_rows as (
                select account_id, account_month
                from main.mart_account_health
                where health_score is not null
            )
            select scored_rows.account_id, scored_rows.account_month
            from scored_rows
            cross join required_components
            left join main.mart_account_health_explanations as explanations
                on scored_rows.account_id = explanations.account_id
                and scored_rows.account_month = explanations.account_month
                and required_components.component_name = explanations.component_name
            where explanations.component_name is null
            limit 1
            """
        ).fetchall(),
    )
    if missing_rows:
        raise HealthValidationError("A scored account-month is missing component explanations.")

    for component in REQUIRED_EXPLANATION_COMPONENTS:
        row = cast(
            tuple[int],
            connection.execute(
                """
                select count(*)
                from main.mart_account_health_explanations
                where component_name = ?
                """,
                [component],
            ).fetchone(),
        )
        if row[0] == 0:
            raise HealthValidationError(f"No explanations produced for component: {component}")

    row = cast(
        tuple[int],
        connection.execute(
            """
            select count(*)
            from main.mart_account_health_explanations
            where plain_language_explanation is null
                or plain_language_explanation = ''
            """
        ).fetchone(),
    )
    if row[0] > 0:
        raise HealthValidationError("Account-health explanation text is missing.")

    count_row = cast(
        tuple[int],
        connection.execute(
            "select count(*) from main.mart_account_health_explanations"
        ).fetchone(),
    )
    return count_row[0]


def _validate_coverage(connection: duckdb.DuckDBPyConnection) -> None:
    row = cast(
        tuple[int],
        connection.execute(
            """
            select count(distinct assessment_status)
            from main.mart_account_health_coverage
            """
        ).fetchone(),
    )
    if row[0] < len(ASSESSMENT_STATUSES):
        raise HealthValidationError("Health coverage output does not include every status.")


def _fetch_counts(
    connection: duckdb.DuckDBPyConnection,
    query: str,
) -> dict[str, int]:
    rows = cast(list[tuple[Any, Any]], connection.execute(query).fetchall())
    return {str(label): int(count) for label, count in rows}


if __name__ == "__main__":
    raise SystemExit(main())
