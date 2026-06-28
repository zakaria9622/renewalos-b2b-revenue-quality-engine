"""Capacity-constrained CSM prioritization optimizer."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from math import fsum
from pathlib import Path
from typing import Any

import duckdb
from ortools.sat.python import cp_model

from renewalos.prioritization.config import (
    DEFAULT_PRIORITIZATION_SCENARIO,
    PrioritizationScenario,
)
from renewalos.prioritization.validation import validate_prioritization_results
from renewalos.warehouse.load_raw import WAREHOUSE_DB_PATH

type CandidateMapping = Mapping[str, object]


@dataclass(frozen=True)
class PrioritizationResult:
    """Summary of a prioritization optimization run."""

    scenario: PrioritizationScenario
    records: list[dict[str, object]]
    eligible_count: int
    excluded_count: int
    selected_count: int
    non_selected_count: int
    selected_effort_hours: float
    selected_expected_protected_value: float


def load_candidate_records(database_path: Path = WAREHOUSE_DB_PATH) -> list[dict[str, object]]:
    """Load prioritization candidates and optimization inputs from DuckDB."""

    query = """
        select
            candidates.account_id,
            candidates.account_month,
            candidates.assessment_status,
            candidates.quality_status,
            candidates.health_score,
            candidates.health_band,
            candidates.revenue_exposure_amount,
            candidates.renewal_urgency,
            candidates.usage_concern,
            candidates.support_concern,
            candidates.customer_success_engagement_concern,
            candidates.revenue_or_billing_status_concern,
            candidates.explanation_drivers,
            candidates.is_eligible_candidate,
            candidates.exclusion_reason,
            inputs.priority_tier,
            inputs.estimated_account_value_at_risk,
            inputs.estimated_effort_hours,
            inputs.assumed_intervention_effectiveness,
            inputs.expected_protected_value,
            inputs.priority_score,
            coalesce(inputs.scenario_id, 'synthetic_csm_capacity_v1') as scenario_id,
            coalesce(
                inputs.assumption_version,
                'simulated_prioritization_assumptions_v1'
            ) as assumption_version,
            coalesce(
                inputs.assumption_label,
                'simulated_scenario_assumption_not_observed_effect'
            ) as assumption_label
        from main.mart_csm_priority_candidates as candidates
        left join main.mart_csm_prioritization_inputs as inputs
            on candidates.account_id = inputs.account_id
            and candidates.account_month = inputs.account_month
        order by candidates.account_month, candidates.account_id
    """
    database_path = database_path.resolve()
    with duckdb.connect(str(database_path), read_only=True) as connection:
        cursor = connection.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def records_from_dataframe(dataframe: Any) -> list[dict[str, object]]:
    """Convert a dataframe-like object into optimizer records."""

    if not hasattr(dataframe, "to_dict"):
        raise TypeError("Expected a dataframe-like object with to_dict(orient='records').")
    records = dataframe.to_dict(orient="records")
    if not isinstance(records, list):
        raise TypeError("Dataframe conversion did not produce a record list.")
    return [dict(record) for record in records]


def optimize_priorities(
    candidate_records: Iterable[CandidateMapping],
    scenario: PrioritizationScenario = DEFAULT_PRIORITIZATION_SCENARIO,
) -> PrioritizationResult:
    """Select CSM priorities while respecting scenario capacity constraints."""

    records = [_normalize_record(record, scenario) for record in candidate_records]
    eligible_indexes = [
        index for index, record in enumerate(records) if _is_optimizer_eligible(record)
    ]
    solver_indexes = _candidate_pool_indexes(records, eligible_indexes, scenario)

    model = cp_model.CpModel()
    decision_vars = {
        index: model.new_bool_var(f"select_{index}") for index in solver_indexes
    }
    model.add(
        sum(
            _to_int(records[index]["estimated_effort_tenths"]) * decision_vars[index]
            for index in solver_indexes
        )
        <= int(round(scenario.available_csm_hours_per_month * 10))
    )
    model.add(
        sum(decision_vars[index] for index in solver_indexes)
        <= scenario.total_account_capacity
    )

    keys = Counter(_candidate_key(records[index]) for index in solver_indexes)
    for key in keys:
        same_key_indexes = [
            index for index in solver_indexes if _candidate_key(records[index]) == key
        ]
        if len(same_key_indexes) > 1:
            model.add(sum(decision_vars[index] for index in same_key_indexes) <= 1)

    model.maximize(
        sum(
            _to_int(records[index]["expected_protected_value_cents"]) * decision_vars[index]
            for index in solver_indexes
        )
    )

    selected_indexes: set[int] = set()
    if solver_indexes:
        solver = cp_model.CpSolver()
        solver.parameters.random_seed = 20260228
        solver.parameters.num_search_workers = 1
        solver.parameters.max_time_in_seconds = 20.0
        status = solver.solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError("Prioritization solver did not find a feasible solution.")
        selected_indexes = {
            index for index in solver_indexes if solver.value(decision_vars[index]) == 1
        }
    solver_index_set = set(solver_indexes)

    output_records = [
        _decision_record(
            record=record,
            is_selected=index in selected_indexes,
            has_duplicate_key=keys.get(_candidate_key(record), 0) > 1,
            is_in_solver_pool=index in solver_index_set,
            scenario=scenario,
        )
        for index, record in enumerate(records)
    ]

    validate_prioritization_results(output_records, scenario)

    eligible_count = sum(1 for record in output_records if record["is_eligible_candidate"])
    selected_records = [
        record for record in output_records if record["recommendation_status"] == "selected"
    ]
    selected_effort = fsum(
        _to_float(record["estimated_effort_hours"], default=0.0)
        for record in selected_records
    )
    selected_value = fsum(
        _to_float(record["expected_protected_value"], default=0.0)
        for record in selected_records
    )

    return PrioritizationResult(
        scenario=scenario,
        records=output_records,
        eligible_count=eligible_count,
        excluded_count=len(output_records) - eligible_count,
        selected_count=len(selected_records),
        non_selected_count=eligible_count - len(selected_records),
        selected_effort_hours=round(selected_effort, 2),
        selected_expected_protected_value=round(selected_value, 2),
    )


def write_prioritization_output(
    result: PrioritizationResult,
    output_path: Path | None = None,
) -> Path:
    """Write prioritization recommendations to a local generated CSV."""

    destination = output_path or result.scenario.output_path
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "account_id",
        "account_month",
        "is_selected",
        "recommendation_status",
        "priority_tier",
        "priority_score",
        "estimated_account_value_at_risk",
        "expected_protected_value",
        "estimated_effort_hours",
        "assumed_intervention_effectiveness",
        "selection_reason",
        "non_selection_reason",
        "scenario_id",
        "assumption_version",
        "assumption_label",
        "is_observed_intervention_outcome",
        "is_eligible_candidate",
        "exclusion_reason",
        "quality_status",
        "assessment_status",
        "health_band",
        "revenue_exposure_amount",
        "renewal_urgency",
        "usage_concern",
        "support_concern",
        "customer_success_engagement_concern",
        "revenue_or_billing_status_concern",
        "explanation_drivers",
    ]
    with destination.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in result.records:
            writer.writerow({field: record.get(field, "") for field in fieldnames})
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for running the synthetic CSM prioritization optimizer."""

    parser = argparse.ArgumentParser(description="Run RenewalOS CSM prioritization.")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=WAREHOUSE_DB_PATH,
        help="Built DuckDB database containing dbt prioritization input models.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_PRIORITIZATION_SCENARIO.output_path,
        help="Local generated CSV output path.",
    )
    args = parser.parse_args(argv)

    candidates = load_candidate_records(database_path=args.database_path)
    result = optimize_priorities(candidates, DEFAULT_PRIORITIZATION_SCENARIO)
    output_path = write_prioritization_output(result, output_path=args.output_path)
    print("RenewalOS CSM prioritization completed.")
    print(f"scenario_id: {result.scenario.scenario_id}")
    print(f"objective: {result.scenario.objective}")
    print(f"eligible_count: {result.eligible_count}")
    print(f"excluded_count: {result.excluded_count}")
    print(f"selected_count: {result.selected_count}")
    print(f"non_selected_count: {result.non_selected_count}")
    print(f"selected_effort_hours: {result.selected_effort_hours}")
    print(f"selected_expected_protected_value: {result.selected_expected_protected_value}")
    print(f"output_path: {output_path}")
    return 0


def _normalize_record(
    record: CandidateMapping,
    scenario: PrioritizationScenario,
) -> dict[str, object]:
    normalized = dict(record)
    normalized["account_id"] = str(normalized.get("account_id", ""))
    normalized["account_month"] = _stringify_date(normalized.get("account_month"))
    normalized["is_eligible_candidate"] = _to_bool(normalized.get("is_eligible_candidate"))
    estimated_effort_hours = _to_float(
        normalized.get("estimated_effort_hours"),
        default=0.0,
    )
    expected_protected_value = _to_float(
        normalized.get("expected_protected_value"),
        default=0.0,
    )
    normalized["estimated_effort_hours"] = estimated_effort_hours
    normalized["expected_protected_value"] = expected_protected_value
    normalized["estimated_effort_tenths"] = int(round(estimated_effort_hours * 10))
    normalized["expected_protected_value_cents"] = int(round(expected_protected_value * 100))
    normalized.setdefault("scenario_id", scenario.scenario_id)
    normalized.setdefault("assumption_version", scenario.assumption_version)
    normalized.setdefault("assumption_label", "simulated_scenario_assumption_not_observed_effect")
    return normalized


def _decision_record(
    record: Mapping[str, object],
    is_selected: bool,
    has_duplicate_key: bool,
    is_in_solver_pool: bool,
    scenario: PrioritizationScenario,
) -> dict[str, object]:
    output = dict(record)
    is_eligible = _is_optimizer_eligible(record)
    output["is_selected"] = is_selected
    output["recommendation_status"] = (
        "selected" if is_selected else "not_selected" if is_eligible else "excluded"
    )
    output["priority_tier"] = str(output.get("priority_tier") or "not_applicable")
    output["scenario_id"] = scenario.scenario_id
    output["assumption_version"] = scenario.assumption_version
    output["assumption_label"] = "simulated_scenario_assumption_not_observed_effect"
    output["is_observed_intervention_outcome"] = False
    output["selection_reason"] = (
        "Selected by OR-Tools capacity-constrained objective."
        if is_selected
        else ""
    )
    output["non_selection_reason"] = _non_selection_reason(
        record=record,
        is_selected=is_selected,
        is_eligible=is_eligible,
        has_duplicate_key=has_duplicate_key,
        is_in_solver_pool=is_in_solver_pool,
    )
    output["estimated_effort_hours"] = round(
        _to_float(output.get("estimated_effort_hours"), default=0.0),
        2,
    )
    output["expected_protected_value"] = round(
        _to_float(output.get("expected_protected_value"), default=0.0),
        2,
    )
    return output


def _non_selection_reason(
    record: Mapping[str, object],
    is_selected: bool,
    is_eligible: bool,
    has_duplicate_key: bool,
    is_in_solver_pool: bool,
) -> str:
    if is_selected:
        return ""
    if not is_eligible:
        return str(record.get("exclusion_reason") or "blocked_or_not_assessable")
    if not is_in_solver_pool:
        return "outside_solver_candidate_pool"
    if has_duplicate_key:
        return "duplicate_account_month_not_selected"
    return "capacity_limited_or_lower_objective_contribution"


def _candidate_pool_indexes(
    records: Sequence[Mapping[str, object]],
    eligible_indexes: Sequence[int],
    scenario: PrioritizationScenario,
) -> list[int]:
    sorted_indexes = sorted(
        eligible_indexes,
        key=lambda index: (
            -_to_float(records[index].get("priority_score"), default=0.0),
            -_to_float(records[index].get("expected_protected_value"), default=0.0),
            str(records[index].get("account_month", "")),
            str(records[index].get("account_id", "")),
        ),
    )
    return sorted_indexes[: scenario.max_solver_candidate_pool]


def _is_optimizer_eligible(record: Mapping[str, object]) -> bool:
    return (
        _to_bool(record.get("is_eligible_candidate"))
        and str(record.get("assessment_status")) not in {
            "blocked_due_to_data_quality",
            "not_assessable",
        }
        and str(record.get("quality_status")) != "blocked"
        and _to_float(record.get("estimated_effort_hours"), default=0.0) > 0
        and _to_float(record.get("expected_protected_value"), default=0.0) >= 0
    )


def _candidate_key(record: Mapping[str, object]) -> tuple[str, str]:
    return (str(record.get("account_id", "")), str(record.get("account_month", "")))


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "1", "yes"}
    return bool(value)


def _to_float(value: object, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value:
        return float(value)
    return default


def _to_int(value: object) -> int:
    return int(_to_float(value, default=0.0))


def _stringify_date(value: object) -> str:
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
