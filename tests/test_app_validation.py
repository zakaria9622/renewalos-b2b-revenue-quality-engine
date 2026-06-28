from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from renewalos.app.validation import (
    AppDataError,
    validate_priority_export_records,
    validate_warehouse_ready,
)


def test_warehouse_missing_error_mentions_build_commands(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.duckdb"

    with pytest.raises(AppDataError, match="renewalos-generate-raw"):
        validate_warehouse_ready(database_path=missing_path)


def test_required_table_validation_lists_missing_models(tmp_path: Path) -> None:
    database_path = tmp_path / "empty.duckdb"
    with duckdb.connect(str(database_path)):
        pass

    with pytest.raises(AppDataError, match="mart_kpi_trust_status"):
        validate_warehouse_ready(database_path=database_path)


def test_priority_export_validation_rejects_blocked_selected_record() -> None:
    records = [
        {
            "account_id": "acct_001",
            "account_month": "2025-01-01",
            "is_selected": "True",
            "recommendation_status": "selected",
            "scenario_id": "synthetic_csm_capacity_v1",
            "assumption_version": "simulated_prioritization_assumptions_v1",
            "assumption_label": "simulated_scenario_assumption_not_observed_effect",
            "assessment_status": "blocked_due_to_data_quality",
            "quality_status": "blocked",
            "expected_protected_value": "100",
            "estimated_effort_hours": "2",
            "selection_reason": "Selected by test.",
            "non_selection_reason": "",
            "explanation_drivers": "quality:high:blocked synthetic record",
        }
    ]

    with pytest.raises(AppDataError, match="Blocked or not-assessable"):
        validate_priority_export_records(records)
