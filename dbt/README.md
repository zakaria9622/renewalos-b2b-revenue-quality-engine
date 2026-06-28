# dbt Warehouse Layer

This directory contains the local dbt-duckdb project for RenewalOS.

Run dbt commands from this directory after generating raw CSVs and loading DuckDB raw tables:

```powershell
cd dbt
dbt debug
dbt run
dbt test
```

The generated models are preliminary warehouse, quality-control, account-health, prioritization-input, and diagnostic models. They preserve synthetic incidents, expose reconciliation gaps, and are not approved for trusted management KPI reporting. Account-health and prioritization outputs are explainable synthetic scenario diagnostics, not predictive model outputs, observed intervention outcomes, or automated operational actions.
