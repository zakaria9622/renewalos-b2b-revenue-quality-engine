from pathlib import Path

import renewalos
from renewalos.config import PROCESSED_DATA_DIR, PROJECT_ROOT, RAW_DATA_DIR


def test_package_imports() -> None:
    assert renewalos.__version__ == "0.1.0"


def test_project_root_exists() -> None:
    assert PROJECT_ROOT.exists()
    assert (PROJECT_ROOT / "pyproject.toml").is_file()


def test_expected_data_directories_exist() -> None:
    expected_dirs: tuple[Path, ...] = (RAW_DATA_DIR, PROCESSED_DATA_DIR)

    for directory in expected_dirs:
        assert directory.is_dir()
