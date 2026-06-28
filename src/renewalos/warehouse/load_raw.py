"""Load synthetic raw CSV files into the local DuckDB warehouse."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from renewalos.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from renewalos.generation.config import SOURCE_FILES

RAW_SCHEMA = "raw"
WAREHOUSE_DB_PATH = PROCESSED_DATA_DIR / "renewalos.duckdb"


@dataclass(frozen=True)
class RawLoadResult:
    """Summary of a raw CSV load into DuckDB."""

    database_path: Path
    raw_dir: Path
    loaded_at: datetime
    row_counts: dict[str, int]


def load_raw_tables(
    raw_dir: Path = RAW_DATA_DIR,
    database_path: Path = WAREHOUSE_DB_PATH,
) -> RawLoadResult:
    """Load every required generated CSV into DuckDB raw schema tables.

    Source column values are loaded as text. The loader only appends technical
    provenance metadata: source file name, load timestamp, source row number,
    and source row identifier.
    """

    raw_dir = raw_dir.resolve()
    database_path = database_path.resolve()
    _ensure_required_files(raw_dir)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    loaded_at = datetime.now(UTC)
    row_counts: dict[str, int] = {}

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(f"create schema if not exists {_identifier(RAW_SCHEMA)}")
        for table_name, filename in SOURCE_FILES.items():
            csv_path = raw_dir / filename
            _load_single_table(
                connection=connection,
                table_name=table_name,
                csv_path=csv_path,
                loaded_at=loaded_at,
            )
            row_counts[table_name] = _table_count(connection, table_name)

    return RawLoadResult(
        database_path=database_path,
        raw_dir=raw_dir,
        loaded_at=loaded_at,
        row_counts=row_counts,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for loading raw synthetic CSV files into DuckDB."""

    parser = argparse.ArgumentParser(description="Load RenewalOS raw CSVs into DuckDB.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help="Directory containing generated raw CSV files.",
    )
    parser.add_argument(
        "--database-path",
        type=Path,
        default=WAREHOUSE_DB_PATH,
        help="DuckDB database path to create or update.",
    )
    args = parser.parse_args(argv)

    result = load_raw_tables(raw_dir=args.raw_dir, database_path=args.database_path)
    print(f"Loaded raw RenewalOS tables into: {result.database_path}")
    print(f"raw_dir: {result.raw_dir}")
    print(f"loaded_at: {result.loaded_at.isoformat()}")
    for table_name in SOURCE_FILES:
        print(f"{RAW_SCHEMA}.{table_name}: {result.row_counts[table_name]}")
    return 0


def _ensure_required_files(raw_dir: Path) -> None:
    missing_files = [
        filename
        for filename in SOURCE_FILES.values()
        if not (raw_dir / filename).is_file()
    ]
    if missing_files:
        missing = ", ".join(missing_files)
        raise FileNotFoundError(f"Missing required raw CSV file(s) in {raw_dir}: {missing}")


def _load_single_table(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    csv_path: Path,
    loaded_at: datetime,
) -> None:
    relation_name = f"{_identifier(RAW_SCHEMA)}.{_identifier(table_name)}"
    source_file_name = csv_path.name
    source_file_literal = _literal(source_file_name)
    loaded_at_literal = _literal(loaded_at.isoformat())
    csv_path_literal = _literal(str(csv_path))
    source_prefix_literal = _literal(f"{table_name}:")

    connection.execute(
        f"""
        create or replace table {relation_name} as
        with raw_rows as (
            select *
            from read_csv(
                {csv_path_literal},
                header = true,
                all_varchar = true
            )
        ),
        numbered_rows as (
            select
                raw_rows.*,
                row_number() over () as source_row_number
            from raw_rows
        )
        select
            numbered_rows.*,
            {source_file_literal} as source_file_name,
            try_cast({loaded_at_literal} as timestamp with time zone) as loaded_at,
            {source_prefix_literal} || cast(source_row_number as varchar) as source_row_identifier
        from numbered_rows
        """
    )


def _table_count(connection: duckdb.DuckDBPyConnection, table_name: str) -> int:
    result = connection.execute(
        f"select count(*) from {_identifier(RAW_SCHEMA)}.{_identifier(table_name)}"
    ).fetchone()
    if result is None:
        raise RuntimeError(f"Could not count loaded rows for table: {table_name}")
    return int(result[0])


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


if __name__ == "__main__":
    raise SystemExit(main())
