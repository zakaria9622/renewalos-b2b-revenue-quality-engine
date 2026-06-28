# Portfolio Case Study

## Business Problem

B2B revenue teams often depend on ARR, retention, renewal, and account-health views even when
source systems disagree. RenewalOS demonstrates how an analytics engineering workflow can expose
data-quality and reconciliation risk before leaders rely on those outputs.

## Architecture

The project uses synthetic source CSVs, a local DuckDB warehouse, dbt-duckdb models, Python
validation commands, and a local Streamlit Control Tower. The app reads existing diagnostic marts
and generated prioritization output; it does not create new data or business logic.

## Data-Quality Challenge

Synthetic incidents are deliberately injected into contracts, billing, usage, support, Customer
Success, and identifier records. Quality models preserve exceptions, map them to incident coverage,
and gate downstream reconciliation, health assessment, and prioritization views.

## Methodology

The workflow separates source generation, raw loading, staging, quality detection, reconciliation
diagnostics, account-health assessment, and simulated prioritization. Each stage documents grain,
lineage, assumptions, and limitations. Blocked or not-assessable records remain visible.

## Decision Framework

RenewalOS distinguishes management KPI readiness from diagnostic evidence. The Control Tower helps
reviewers inspect whether KPI reporting is restricted, which issues block decisions, which records
are health-assessable, and which account-months are selected under the simulated CSM capacity
scenario.

## Technical Stack

- Python 3.12
- DuckDB
- dbt-duckdb
- pandas
- Streamlit
- OR-Tools for the existing capacity-constrained prioritization command
- pytest, Ruff, and mypy for validation

## Limitations

All data is synthetic. The project does not claim production readiness, trusted management KPIs,
machine-learning accuracy, customer outcomes, retained revenue, ROI, or any observed business
impact. Scenario assumptions are illustrative and would need replacement with governed evidence
before real-world use.
