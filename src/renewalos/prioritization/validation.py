"""Validation helpers for CSM prioritization outputs."""

from __future__ import annotations

import argparse
import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

from renewalos.prioritization.config import DEFAULT_PRIORITIZATION_SCENARIO, PrioritizationScenario


class PrioritizationValidationError(RuntimeError):
    """Raised when prioritization output violates scenario constraints."""


def validate_prioritization_results(
    records: Sequence[Mapping[str, object]],
    scenario: PrioritizationScenario = DEFAULT_PRIORITIZATION_SCENARIO,
) -> None:
    """Validate selected and non-selected prioritization records."""

    allowed_statuses = {"selected", "not_selected", "excluded"}
    for record in records:
        recommendation_status = str(record.get("recommendation_status"))
        if recommendation_status not in allowed_statuses:
            raise PrioritizationValidationError(
                f"Unexpected recommendation status: {recommendation_status}"
            )
        if str(record.get("scenario_id")) != scenario.scenario_id:
            raise PrioritizationValidationError("Record is missing scenario metadata.")
        if str(record.get("assumption_version")) != scenario.assumption_version:
            raise PrioritizationValidationError("Record is missing assumption metadata.")
        if (
            str(record.get("assumption_label"))
            != "simulated_scenario_assumption_not_observed_effect"
        ):
            raise PrioritizationValidationError("Record is missing the simulated assumption label.")

    selected_records = [
        record for record in records if str(record.get("recommendation_status")) == "selected"
    ]
    selected_keys = [
        (str(record.get("account_id")), str(record.get("account_month")))
        for record in selected_records
    ]
    if len(selected_keys) != len(set(selected_keys)):
        raise PrioritizationValidationError("Selected account-month records are not unique.")

    selected_effort = sum(
        _to_float(record.get("estimated_effort_hours"), default=0.0)
        for record in selected_records
    )
    if selected_effort > scenario.available_csm_hours_per_month + 0.0001:
        raise PrioritizationValidationError("Selected effort exceeds scenario CSM capacity.")

    if len(selected_records) > scenario.total_account_capacity:
        raise PrioritizationValidationError("Selected account count exceeds scenario capacity.")

    for record in selected_records:
        if str(record.get("assessment_status")) in {
            "blocked_due_to_data_quality",
            "not_assessable",
        }:
            raise PrioritizationValidationError("Blocked or not-assessable record selected.")
        if str(record.get("quality_status")) == "blocked":
            raise PrioritizationValidationError("Blocked quality-status record selected.")
        if not str(record.get("explanation_drivers") or ""):
            raise PrioritizationValidationError("Selected record is missing explanation drivers.")


def validate_prioritization_output_file(
    output_path: Path = DEFAULT_PRIORITIZATION_SCENARIO.output_path,
    scenario: PrioritizationScenario = DEFAULT_PRIORITIZATION_SCENARIO,
) -> None:
    """Validate a generated prioritization CSV file."""

    output_path = output_path.resolve()
    if not output_path.is_file():
        raise PrioritizationValidationError(f"Prioritization output does not exist: {output_path}")
    with output_path.open("r", encoding="utf-8", newline="") as input_file:
        records = list(csv.DictReader(input_file))
    validate_prioritization_results(records, scenario)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for validating generated prioritization output."""

    parser = argparse.ArgumentParser(description="Validate RenewalOS prioritization output.")
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_PRIORITIZATION_SCENARIO.output_path,
        help="Generated prioritization CSV output path.",
    )
    args = parser.parse_args(argv)
    validate_prioritization_output_file(output_path=args.output_path)
    print("RenewalOS prioritization validation passed.")
    return 0


def _to_float(value: object, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value:
        return float(value)
    return default


if __name__ == "__main__":
    raise SystemExit(main())
