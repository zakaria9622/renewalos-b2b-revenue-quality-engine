# Processed Warehouse Artifacts

This directory is the default local location for the DuckDB warehouse created by:

```powershell
renewalos-load-raw
```

The generated `renewalos.duckdb` file is ignored by Git. It contains synthetic raw source tables and dbt-built preliminary models when the local warehouse flow is run.

The warehouse marts are diagnostic and preliminary. They must not be used for management KPI reporting until formal data-quality checks and reconciliation controls are implemented.
