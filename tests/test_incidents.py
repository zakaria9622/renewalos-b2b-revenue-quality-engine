from __future__ import annotations

from pathlib import Path

from renewalos.generation.config import DEFAULT_GENERATION_CONFIG, REQUIRED_INCIDENT_SCENARIOS
from renewalos.generation.validate_generation import (
    detect_intentional_incidents,
    generate_raw_data,
    read_tables,
)


def test_incident_registry_contains_required_scenarios(tmp_path: Path) -> None:
    output_dir = tmp_path / "raw"
    generate_raw_data(DEFAULT_GENERATION_CONFIG.with_output_dir(output_dir))
    tables = read_tables(output_dir)

    registry_scenarios = {row["scenario_name"] for row in tables["incident_registry"]}

    assert len(tables["incident_registry"]) >= 12
    assert set(REQUIRED_INCIDENT_SCENARIOS).issubset(registry_scenarios)


def test_each_documented_incident_category_is_detectable(tmp_path: Path) -> None:
    output_dir = tmp_path / "raw"
    config = DEFAULT_GENERATION_CONFIG.with_output_dir(output_dir)
    generate_raw_data(config)
    tables = read_tables(output_dir)

    incident_counts = detect_intentional_incidents(tables, config)

    for scenario_name in REQUIRED_INCIDENT_SCENARIOS:
        assert incident_counts[scenario_name] >= 1
