from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from renewalos.app.bootstrap import (
    BootstrapArtifacts,
    BootstrapCheck,
    DeploymentBootstrapError,
    ensure_demo_data_ready,
)
from renewalos.config import PROJECT_ROOT


def _artifacts(tmp_path: Path) -> BootstrapArtifacts:
    return BootstrapArtifacts(
        raw_dir=tmp_path / "raw",
        database_path=tmp_path / "processed" / "renewalos.duckdb",
        priority_output_path=tmp_path
        / "processed"
        / "prioritization"
        / "csm_prioritization_recommendations.csv",
    )


def test_missing_artifacts_trigger_initialization(tmp_path: Path) -> None:
    checks = iter(
        (
            BootstrapCheck(is_ready=False, missing_items=("DuckDB warehouse not ready",)),
            BootstrapCheck(is_ready=False, missing_items=("DuckDB warehouse not ready",)),
            BootstrapCheck(is_ready=True, missing_items=()),
        )
    )
    run_count = 0

    def check_artifacts() -> BootstrapCheck:
        return next(checks)

    def run_pipeline() -> None:
        nonlocal run_count
        run_count += 1

    result = ensure_demo_data_ready(
        _artifacts(tmp_path),
        check_artifacts=check_artifacts,
        run_pipeline=run_pipeline,
        lock_timeout_seconds=1.0,
        lock_poll_seconds=0.01,
    )

    assert result.initialized is True
    assert result.missing_items == ("DuckDB warehouse not ready",)
    assert run_count == 1


def test_existing_valid_artifacts_do_not_trigger_rebuild(tmp_path: Path) -> None:
    def check_artifacts() -> BootstrapCheck:
        return BootstrapCheck(is_ready=True, missing_items=())

    def run_pipeline() -> None:
        raise AssertionError("Pipeline should not run when artifacts are valid.")

    result = ensure_demo_data_ready(
        _artifacts(tmp_path),
        check_artifacts=check_artifacts,
        run_pipeline=run_pipeline,
        lock_timeout_seconds=1.0,
        lock_poll_seconds=0.01,
    )

    assert result.initialized is False
    assert result.missing_items == ()


def test_bootstrap_failures_raise_clear_error(tmp_path: Path) -> None:
    checks = iter(
        (
            BootstrapCheck(is_ready=False, missing_items=("prioritization export missing",)),
            BootstrapCheck(is_ready=False, missing_items=("prioritization export missing",)),
        )
    )

    def check_artifacts() -> BootstrapCheck:
        return next(checks)

    def run_pipeline() -> None:
        raise RuntimeError("dbt run failed for test")

    with pytest.raises(
        DeploymentBootstrapError,
        match="RenewalOS synthetic demo bootstrap failed.*dbt run failed for test",
    ):
        ensure_demo_data_ready(
            _artifacts(tmp_path),
            check_artifacts=check_artifacts,
            run_pipeline=run_pipeline,
            lock_timeout_seconds=1.0,
            lock_poll_seconds=0.01,
        )


def test_generated_artifact_paths_are_not_tracked_and_are_git_ignored() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "data/raw", "data/processed", "dbt/target", "dbt/logs"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    allowed_tracked_files = {
        "data/raw/.gitkeep",
        "data/raw/README.md",
        "data/processed/.gitkeep",
        "data/processed/README.md",
    }

    assert sorted(set(tracked) - allowed_tracked_files) == []

    generated_paths = [
        "data/raw/accounts.csv",
        "data/raw/billing_events.csv",
        "data/processed/renewalos.duckdb",
        "data/processed/prioritization/csm_prioritization_recommendations.csv",
        "dbt/target/manifest.json",
        "dbt/logs/dbt.log",
    ]
    ignored = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        cwd=PROJECT_ROOT,
        input=("\n".join(generated_paths) + "\n").encode(),
        capture_output=True,
        check=True,
    ).stdout.decode().splitlines()

    assert sorted(ignored) == sorted(generated_paths)
