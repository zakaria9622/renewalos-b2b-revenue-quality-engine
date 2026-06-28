from __future__ import annotations

import pytest

from renewalos.app import data_access
from renewalos.app.validation import AppDataError
from renewalos.prioritization.config import DEFAULT_PRIORITIZATION_SCENARIO
from renewalos.warehouse.load_raw import WAREHOUSE_DB_PATH


def _require_built_warehouse() -> None:
    if not WAREHOUSE_DB_PATH.is_file():
        pytest.skip("Warehouse database is not built.")


def _require_prioritization_export() -> None:
    if not DEFAULT_PRIORITIZATION_SCENARIO.output_path.is_file():
        pytest.skip("Prioritization export is not generated.")


def test_data_access_functions_return_expected_columns() -> None:
    _require_built_warehouse()

    trust_counts = data_access.load_kpi_trust_status_counts()
    quality_counts = data_access.load_account_month_quality_counts()
    reconciliation = data_access.load_reconciliation_details()
    health = data_access.load_account_health_details()

    assert {"gate_status", "is_management_kpi_reporting_approved"}.issubset(
        trust_counts.columns
    )
    assert {"quality_status", "critical_exception_count"}.issubset(quality_counts.columns)
    assert {"account_id", "account_month", "reconciliation_status"}.issubset(
        reconciliation.columns
    )
    assert {"account_id", "account_month", "assessment_status", "health_band"}.issubset(
        health.columns
    )


def test_prioritization_export_has_scenario_metadata() -> None:
    _require_prioritization_export()

    export = data_access.load_prioritization_export()

    assert {"scenario_id", "assumption_version", "assumption_label"}.issubset(export.columns)
    assert set(export["scenario_id"]) == {DEFAULT_PRIORITIZATION_SCENARIO.scenario_id}
    assert set(export["assumption_version"]) == {
        DEFAULT_PRIORITIZATION_SCENARIO.assumption_version
    }
    assert set(export["assumption_label"]) == {
        "simulated_scenario_assumption_not_observed_effect"
    }


def test_selected_recommendations_exclude_blocked_and_not_assessable_records() -> None:
    _require_prioritization_export()

    export = data_access.load_prioritization_export()
    selected = export[export["recommendation_status"] == "selected"]
    invalid = selected[
        selected["assessment_status"].isin(["blocked_due_to_data_quality", "not_assessable"])
        | (selected["quality_status"] == "blocked")
    ]

    assert invalid.empty


def test_query_failure_message_is_clear_for_invalid_sql() -> None:
    _require_built_warehouse()

    with pytest.raises(AppDataError, match="Warehouse query failed"):
        data_access.query_dataframe("select * from main.not_a_real_table")
