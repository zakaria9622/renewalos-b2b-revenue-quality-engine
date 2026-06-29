"""Deployment bootstrap helpers for the RenewalOS Streamlit app."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from renewalos.app.validation import (
    AppDataError,
    load_priority_export_records,
    validate_priority_export_records,
    validate_warehouse_ready,
)
from renewalos.config import DBT_DIR, PROJECT_ROOT, RAW_DATA_DIR
from renewalos.generation.config import DEFAULT_GENERATION_CONFIG, SOURCE_FILES
from renewalos.generation.validate_generation import generate_raw_data
from renewalos.prioritization.config import DEFAULT_PRIORITIZATION_SCENARIO
from renewalos.prioritization.optimizer import (
    load_candidate_records,
    optimize_priorities,
    write_prioritization_output,
)
from renewalos.warehouse.load_raw import WAREHOUSE_DB_PATH, load_raw_tables

LOCK_TIMEOUT_SECONDS = 300.0
LOCK_POLL_SECONDS = 0.5


class DeploymentBootstrapError(AppDataError):
    """Raised when synthetic demo artifacts cannot be prepared for app startup."""


@dataclass(frozen=True)
class BootstrapArtifacts:
    """Generated artifacts required by the Streamlit demo."""

    raw_dir: Path
    database_path: Path
    priority_output_path: Path


@dataclass(frozen=True)
class BootstrapCheck:
    """Readiness check for generated demo artifacts."""

    is_ready: bool
    missing_items: tuple[str, ...]


@dataclass(frozen=True)
class BootstrapResult:
    """Result of ensuring generated demo artifacts exist."""

    initialized: bool
    reason: str
    database_path: Path
    priority_output_path: Path
    missing_items: tuple[str, ...]


CommandRunner = Callable[[Sequence[str], Path], None]
ArtifactChecker = Callable[[], BootstrapCheck]
PipelineRunner = Callable[[], None]

DEFAULT_BOOTSTRAP_ARTIFACTS = BootstrapArtifacts(
    raw_dir=RAW_DATA_DIR,
    database_path=WAREHOUSE_DB_PATH,
    priority_output_path=DEFAULT_PRIORITIZATION_SCENARIO.output_path,
)


def check_bootstrap_artifacts(
    artifacts: BootstrapArtifacts = DEFAULT_BOOTSTRAP_ARTIFACTS,
) -> BootstrapCheck:
    """Return whether all generated artifacts needed by the app are present and valid."""

    missing_items: list[str] = []
    missing_raw_files = [
        filename
        for filename in SOURCE_FILES.values()
        if not (artifacts.raw_dir / filename).is_file()
    ]
    if missing_raw_files:
        missing = ", ".join(missing_raw_files)
        missing_items.append(
            f"synthetic raw CSV file(s) missing from {_display_path(artifacts.raw_dir)}: {missing}"
        )

    try:
        validate_warehouse_ready(database_path=artifacts.database_path)
    except AppDataError as error:
        missing_items.append(f"DuckDB warehouse not ready: {error}")

    try:
        records = load_priority_export_records(output_path=artifacts.priority_output_path)
        validate_priority_export_records(records)
    except AppDataError as error:
        missing_items.append(f"prioritization export not ready: {error}")

    return BootstrapCheck(is_ready=not missing_items, missing_items=tuple(missing_items))


def ensure_demo_data_ready(
    artifacts: BootstrapArtifacts = DEFAULT_BOOTSTRAP_ARTIFACTS,
    *,
    check_artifacts: ArtifactChecker | None = None,
    run_pipeline: PipelineRunner | None = None,
    lock_path: Path | None = None,
    lock_timeout_seconds: float = LOCK_TIMEOUT_SECONDS,
    lock_poll_seconds: float = LOCK_POLL_SECONDS,
) -> BootstrapResult:
    """Initialize the deterministic synthetic demo pipeline when generated artifacts are missing."""

    artifact_checker = check_artifacts or (lambda: check_bootstrap_artifacts(artifacts))
    initial_check = artifact_checker()
    if initial_check.is_ready:
        return BootstrapResult(
            initialized=False,
            reason="Required synthetic demo artifacts are already present.",
            database_path=artifacts.database_path.resolve(),
            priority_output_path=artifacts.priority_output_path.resolve(),
            missing_items=(),
        )

    lock_directory = lock_path or artifacts.database_path.parent / ".renewalos_bootstrap.lock"
    pipeline_runner = run_pipeline or (lambda: run_demo_pipeline(artifacts=artifacts))
    with _bootstrap_lock(
        lock_directory,
        timeout_seconds=lock_timeout_seconds,
        poll_seconds=lock_poll_seconds,
    ):
        locked_check = artifact_checker()
        if locked_check.is_ready:
            return BootstrapResult(
                initialized=False,
                reason="Required synthetic demo artifacts were initialized by another process.",
                database_path=artifacts.database_path.resolve(),
                priority_output_path=artifacts.priority_output_path.resolve(),
                missing_items=initial_check.missing_items,
            )

        try:
            pipeline_runner()
        except DeploymentBootstrapError:
            raise
        except Exception as error:
            message = (
                "RenewalOS synthetic demo bootstrap failed while rebuilding generated "
                f"artifacts: {error}"
            )
            raise DeploymentBootstrapError(message) from error

        final_check = artifact_checker()
        if not final_check.is_ready:
            missing = "; ".join(final_check.missing_items)
            raise DeploymentBootstrapError(
                "RenewalOS synthetic demo bootstrap finished, but required generated "
                f"artifact(s) are still missing or invalid: {missing}"
            )

    return BootstrapResult(
        initialized=True,
        reason="Missing generated synthetic demo artifacts were rebuilt.",
        database_path=artifacts.database_path.resolve(),
        priority_output_path=artifacts.priority_output_path.resolve(),
        missing_items=initial_check.missing_items,
    )


def run_demo_pipeline(
    artifacts: BootstrapArtifacts = DEFAULT_BOOTSTRAP_ARTIFACTS,
    *,
    command_runner: CommandRunner | None = None,
) -> None:
    """Run the existing deterministic generation, warehouse, dbt, and prioritization path."""

    runner = command_runner or _run_command
    generation_config = DEFAULT_GENERATION_CONFIG.with_output_dir(artifacts.raw_dir)
    generate_raw_data(config=generation_config)
    load_raw_tables(raw_dir=artifacts.raw_dir, database_path=artifacts.database_path)
    runner(_dbt_run_command(), DBT_DIR)
    candidates = load_candidate_records(database_path=artifacts.database_path)
    prioritization = optimize_priorities(candidates, DEFAULT_PRIORITIZATION_SCENARIO)
    write_prioritization_output(prioritization, output_path=artifacts.priority_output_path)


def _run_command(command: Sequence[str], cwd: Path) -> None:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise DeploymentBootstrapError(
            f"Could not run bootstrap command `{_format_command(command)}`: {error}"
        ) from error

    if completed.returncode != 0:
        detail = _command_failure_detail(completed.stdout, completed.stderr)
        raise DeploymentBootstrapError(
            "Bootstrap command failed: "
            f"`{_format_command(command)}` exited with code {completed.returncode}. {detail}"
        )


def _dbt_run_command() -> tuple[str, ...]:
    executable_name = "dbt.exe" if os.name == "nt" else "dbt"
    dbt_executable = Path(sys.executable).resolve().parent / executable_name
    if dbt_executable.is_file():
        return (
            str(dbt_executable),
            "run",
            "--project-dir",
            str(DBT_DIR),
            "--profiles-dir",
            str(DBT_DIR),
        )

    return (
        sys.executable,
        "-m",
        "dbt.cli.main",
        "run",
        "--project-dir",
        str(DBT_DIR),
        "--profiles-dir",
        str(DBT_DIR),
    )


@contextmanager
def _bootstrap_lock(
    lock_path: Path,
    *,
    timeout_seconds: float,
    poll_seconds: float,
) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    acquired = False

    while not acquired:
        try:
            os.mkdir(lock_path)
            acquired = True
        except FileExistsError as error:
            if time.monotonic() >= deadline:
                raise DeploymentBootstrapError(
                    "Timed out waiting for another RenewalOS synthetic demo bootstrap "
                    f"to finish. Lock path: {lock_path}"
                ) from error
            time.sleep(poll_seconds)

    try:
        yield
    finally:
        try:
            lock_path.rmdir()
        except FileNotFoundError:
            pass


def _command_failure_detail(stdout: str, stderr: str) -> str:
    combined = "\n".join(part for part in (stdout.strip(), stderr.strip()) if part)
    if not combined:
        return "No command output was captured."
    lines = combined.splitlines()
    tail = "\n".join(lines[-20:])
    return f"Last command output:\n{tail}"


def _format_command(command: Sequence[str]) -> str:
    return " ".join(command)


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)
