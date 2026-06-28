from __future__ import annotations

import hashlib
from pathlib import Path

from renewalos.generation.config import DEFAULT_GENERATION_CONFIG, SOURCE_FILES
from renewalos.generation.validate_generation import generate_raw_data


def test_generation_is_deterministic_with_fixed_seed(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first_config = DEFAULT_GENERATION_CONFIG.with_output_dir(first_dir)
    second_config = DEFAULT_GENERATION_CONFIG.with_output_dir(second_dir)

    generate_raw_data(first_config)
    generate_raw_data(second_config)

    for filename in SOURCE_FILES.values():
        assert _sha256(first_dir / filename) == _sha256(second_dir / filename)


def test_source_files_are_created(tmp_path: Path) -> None:
    output_dir = tmp_path / "raw"
    result = generate_raw_data(DEFAULT_GENERATION_CONFIG.with_output_dir(output_dir))

    for filename in SOURCE_FILES.values():
        assert (output_dir / filename).is_file()

    assert result.record_counts["accounts"] == DEFAULT_GENERATION_CONFIG.portfolio_size
    assert result.record_counts["usage_events"] == (
        DEFAULT_GENERATION_CONFIG.portfolio_size
        * DEFAULT_GENERATION_CONFIG.simulation_months
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()
