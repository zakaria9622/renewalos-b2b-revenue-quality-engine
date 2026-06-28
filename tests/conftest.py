from __future__ import annotations

from collections.abc import Iterator

import duckdb
import pytest

from renewalos.warehouse.load_raw import WAREHOUSE_DB_PATH

QUALITY_OUTPUT_TABLES: tuple[str, ...] = (
    "dq_contract_exceptions",
    "dq_billing_exceptions",
    "dq_usage_exceptions",
    "dq_support_exceptions",
    "dq_identifier_exceptions",
    "dq_incident_detection_coverage",
    "dq_account_month_quality_status",
    "mart_revenue_reconciliation_diagnostics",
    "mart_kpi_trust_status",
)

HEALTH_OUTPUT_TABLES: tuple[str, ...] = (
    "int_account_month_operational_signals",
    "int_account_month_renewal_signals",
    "mart_account_health",
    "mart_account_health_explanations",
    "mart_account_health_coverage",
)

PRIORITIZATION_OUTPUT_TABLES: tuple[str, ...] = (
    "mart_csm_priority_candidates",
    "mart_csm_prioritization_inputs",
)


@pytest.fixture
def quality_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    if not WAREHOUSE_DB_PATH.is_file():
        pytest.skip("Quality dbt outputs are not built; run raw load and dbt run first.")

    connection = duckdb.connect(str(WAREHOUSE_DB_PATH), read_only=True)
    try:
        rows = connection.execute(
            """
            select table_name
            from information_schema.tables
            where table_schema = 'main'
            """
        ).fetchall()
        existing_tables = {str(row[0]) for row in rows}
        missing_tables = sorted(set(QUALITY_OUTPUT_TABLES) - existing_tables)
        if missing_tables:
            missing = ", ".join(missing_tables)
            pytest.skip(f"Quality dbt outputs are not built: {missing}")
        yield connection
    finally:
        connection.close()


@pytest.fixture
def health_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    if not WAREHOUSE_DB_PATH.is_file():
        pytest.skip("Health dbt outputs are not built; run raw load and dbt run first.")

    connection = duckdb.connect(str(WAREHOUSE_DB_PATH), read_only=True)
    try:
        rows = connection.execute(
            """
            select table_name
            from information_schema.tables
            where table_schema = 'main'
            """
        ).fetchall()
        existing_tables = {str(row[0]) for row in rows}
        missing_tables = sorted(set(HEALTH_OUTPUT_TABLES) - existing_tables)
        if missing_tables:
            missing = ", ".join(missing_tables)
            pytest.skip(f"Health dbt outputs are not built: {missing}")
        yield connection
    finally:
        connection.close()


@pytest.fixture
def prioritization_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    if not WAREHOUSE_DB_PATH.is_file():
        pytest.skip("Prioritization dbt outputs are not built; run raw load and dbt run first.")

    connection = duckdb.connect(str(WAREHOUSE_DB_PATH), read_only=True)
    try:
        rows = connection.execute(
            """
            select table_name
            from information_schema.tables
            where table_schema = 'main'
            """
        ).fetchall()
        existing_tables = {str(row[0]) for row in rows}
        missing_tables = sorted(set(PRIORITIZATION_OUTPUT_TABLES) - existing_tables)
        if missing_tables:
            missing = ", ".join(missing_tables)
            pytest.skip(f"Prioritization dbt outputs are not built: {missing}")
        yield connection
    finally:
        connection.close()
