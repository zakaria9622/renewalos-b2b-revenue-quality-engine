# Warehouse Design

RenewalOS uses a local DuckDB database and dbt-duckdb project to turn generated synthetic raw CSV files into documented warehouse layers.

## Lineage

The current warehouse lineage is:

1. `data/raw/*.csv`
2. DuckDB `raw` schema loaded by `renewalos-load-raw`
3. dbt staging models in `dbt/models/staging`
4. dbt intermediate models in `dbt/models/intermediate`
5. preliminary dbt marts in `dbt/models/marts`

## Raw Layer

The raw loader reads every required generated CSV file from `data/raw` and writes one table per source file into DuckDB schema `raw`.

The loader preserves source values as text and adds only technical provenance fields:

- `source_file_name`
- `loaded_at`
- `source_row_number`
- `source_row_identifier`

It fails clearly if any required raw CSV file is absent.

## Staging Layer

Staging models safely parse dates and numeric values while preserving raw values and identifiers. Parse failures and suspicious source conditions are exposed as fields instead of being filtered away.

Examples include:

- missing renewal dates;
- stale usage extracts;
- late-arriving billing events;
- invalid negative ARR movements;
- incident-injection markers.

## Intermediate Layer

Intermediate models prepare source-aligned structures for later quality checks and reconciliation:

- `int_account_month_spine`: observable account-month rows based on actual source dates;
- `int_contract_timeline`: contract records with overlap and contradiction flags;
- `int_billing_movements`: generated billing event categories mapped to preliminary movement categories.

Incidents are intentionally preserved. The warehouse does not choose a corrected contract, remove duplicate records, repair orphaned billing events, or overwrite inconsistent identifiers.

## Preliminary Mart Layer

The mart models are diagnostic only:

- `mart_account_month_revenue` exposes account-month billing movement components when supported by generated billing events.
- `mart_revenue_reconciliation_diagnostics` exposes preliminary contract-vs-billing differences and exception flags.

These outputs are not trusted management KPIs. They are designed to make gaps and anomalies visible for review and future governed metric work.

## Mapping Assumptions

Billing event mappings are based only on actual generated `event_type` values:

- `opening_arr` maps to opening ARR movement;
- `new_arr` maps to new ARR movement;
- `expansion_arr` maps to expansion movement;
- `contraction_arr` maps to contraction movement;
- `churned_arr` maps to churn movement;
- `renewal` is treated as a renewal marker with no ARR movement component;
- `manual_adjustment` is retained as an unmapped manual adjustment and is not treated as a trusted KPI component.

## Current Validation

The current warehouse includes formal dbt tests and reconciliation controls. Those controls detect and report known failure scenarios before any future KPI output could be considered for management reporting.
