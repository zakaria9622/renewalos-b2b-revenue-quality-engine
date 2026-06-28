"""Typed project paths for the RenewalOS repository."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Repository paths used by future RenewalOS implementation stages."""

    root: Path
    data: Path
    raw_data: Path
    processed_data: Path
    dbt: Path
    app: Path


PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
DBT_DIR: Path = PROJECT_ROOT / "dbt"
APP_DIR: Path = PROJECT_ROOT / "app"

PATHS = ProjectPaths(
    root=PROJECT_ROOT,
    data=DATA_DIR,
    raw_data=RAW_DATA_DIR,
    processed_data=PROCESSED_DATA_DIR,
    dbt=DBT_DIR,
    app=APP_DIR,
)
