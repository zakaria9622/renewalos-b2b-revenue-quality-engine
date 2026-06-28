from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from renewalos.config import PROCESSED_DATA_DIR
from renewalos.generation.config import SOURCE_FILES
from renewalos.warehouse.load_raw import WAREHOUSE_DB_PATH, load_raw_tables

MINIMAL_ROWS: dict[str, dict[str, str]] = {
    "accounts": {
        "account_id": "ACC-TEST",
        "account_name": "Synthetic Test Account LLC",
        "segment": "SMB",
        "region": "EMEA",
        "industry": "Business Services",
        "created_date": "2024-01-01",
        "lifecycle_status": "active",
        "crm_renewal_status": "open",
        "owner_id": "CSM-001",
        "churn_date": "",
        "synthetic_data_label": "synthetic_simulated_source_data",
        "scenario_version": "synthetic_b2b_sources_v1",
        "generation_layer": "baseline",
        "quality_issue_type": "",
    },
    "contracts": {
        "contract_id": "CON-TEST",
        "account_id": "ACC-TEST",
        "contract_start_date": "2024-01-01",
        "contract_end_date": "2024-12-31",
        "renewal_date": "2024-12-31",
        "status": "active",
        "arr_amount": "12000",
        "product_tier": "Core",
        "period_number": "1",
        "synthetic_data_label": "synthetic_simulated_source_data",
        "scenario_version": "synthetic_b2b_sources_v1",
        "generation_layer": "baseline",
        "quality_issue_type": "",
    },
    "billing_events": {
        "billing_event_id": "BILL-TEST",
        "account_id": "ACC-TEST",
        "contract_id": "CON-TEST",
        "event_date": "2024-01-01",
        "effective_date": "2024-01-01",
        "received_at": "2024-01-02",
        "event_type": "opening_arr",
        "arr_delta": "12000",
        "amount": "12000",
        "billing_status": "posted",
        "synthetic_data_label": "synthetic_simulated_source_data",
        "scenario_version": "synthetic_b2b_sources_v1",
        "generation_layer": "baseline",
        "quality_issue_type": "",
    },
    "usage_events": {
        "usage_event_id": "USE-TEST",
        "account_id": "ACC-TEST",
        "activity_month": "2024-01-01",
        "active_users": "4",
        "events_count": "40",
        "usage_status": "active",
        "extract_date": "2024-02-03",
        "synthetic_data_label": "synthetic_simulated_source_data",
        "scenario_version": "synthetic_b2b_sources_v1",
        "generation_layer": "baseline",
        "quality_issue_type": "",
    },
    "support_tickets": {
        "ticket_id": "TICK-TEST",
        "account_id": "ACC-TEST",
        "created_at": "2024-01-05",
        "status": "resolved",
        "severity": "low",
        "category": "training",
        "synthetic_data_label": "synthetic_simulated_source_data",
        "scenario_version": "synthetic_b2b_sources_v1",
        "generation_layer": "baseline",
        "quality_issue_type": "",
    },
    "cs_interactions": {
        "interaction_id": "CSI-TEST",
        "account_id": "ACC-TEST",
        "interaction_date": "2024-01-10",
        "interaction_type": "training",
        "sentiment": "neutral",
        "csm_owner_id": "CSM-001",
        "notes_category": "training",
        "synthetic_data_label": "synthetic_simulated_source_data",
        "scenario_version": "synthetic_b2b_sources_v1",
        "generation_layer": "baseline",
        "quality_issue_type": "",
    },
    "incident_registry": {
        "incident_id": "INC-TEST",
        "scenario_name": "synthetic_test_incident",
        "affected_domain": "accounts",
        "affected_record_identifier": "ACC-TEST",
        "injected_at": "2025-12-31",
        "expected_detection_method": "Synthetic test only.",
        "expected_business_impact": "Synthetic test only.",
        "severity": "low",
        "synthetic_data_label": "synthetic_simulated_source_data",
        "scenario_version": "synthetic_b2b_sources_v1",
    },
}


def test_warehouse_db_path_is_under_processed_data_dir() -> None:
    assert WAREHOUSE_DB_PATH == PROCESSED_DATA_DIR / "renewalos.duckdb"


def test_load_raw_tables_loads_all_required_files_with_provenance(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    database_path = tmp_path / "processed" / "renewalos.duckdb"
    _write_minimal_raw_files(raw_dir)

    result = load_raw_tables(raw_dir=raw_dir, database_path=database_path)

    assert result.database_path == database_path.resolve()
    assert result.row_counts == {table_name: 1 for table_name in SOURCE_FILES}

    with duckdb.connect(str(database_path)) as connection:
        row = connection.execute(
            """
            select
                account_id,
                source_file_name,
                source_row_number,
                source_row_identifier
            from raw.accounts
            """
        ).fetchone()

    assert row == ("ACC-TEST", "accounts.csv", 1, "accounts:1")


def test_load_raw_tables_fails_when_required_file_is_missing(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    database_path = tmp_path / "processed" / "renewalos.duckdb"
    _write_minimal_raw_files(raw_dir)
    (raw_dir / "accounts.csv").unlink()

    with pytest.raises(FileNotFoundError, match="accounts.csv"):
        load_raw_tables(raw_dir=raw_dir, database_path=database_path)


def _write_minimal_raw_files(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True)
    for table_name, filename in SOURCE_FILES.items():
        row = MINIMAL_ROWS[table_name]
        header = ",".join(row.keys())
        values = ",".join(row.values())
        (raw_dir / filename).write_text(f"{header}\n{values}\n", encoding="utf-8")
