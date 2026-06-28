# Final Validation

This document lists the local commands used to validate RenewalOS reproducibility and integrity.
It is a command checklist, not a copied terminal log.

## Commands

| Command | What it verifies |
| --- | --- |
| `renewalos-generate-raw` | Regenerates deterministic synthetic raw CSV files from the fixed seed and controlled incident configuration. |
| `renewalos-load-raw` | Loads the generated raw CSV files into the local DuckDB warehouse without treating raw values as trusted. |
| `cd dbt` | Moves into the dbt project directory so dbt can find its local project and profile files. |
| `dbt run` | Rebuilds staging, intermediate, quality, mart, account-health, and prioritization-input models from the local DuckDB raw schema. |
| `dbt test` | Runs dbt data tests for quality detection coverage, reconciliation diagnostics, account-health integrity, and prioritization quality gates. |
| `cd ..` | Returns to the repository root for Python package and app commands. |
| `renewalos-run-prioritization` | Regenerates the local simulated CSM prioritization export from existing dbt outputs and documented scenario assumptions. |
| `streamlit run app/app.py` | Starts the local Control Tower interface against the built warehouse and generated prioritization export. |
| `ruff check .` | Checks Python formatting and lint rules for the repository. |
| `mypy src` | Type-checks the Python package under strict settings. |
| `pytest` | Runs Python tests for generation, incidents, raw loading, quality controls, account health, prioritization, and app data access. |

## Scope Notes

- Generated source CSVs, DuckDB files, dbt artifacts, caches, virtual environments, and local app outputs are ignored by Git.
- Deterministic synthetic generation should reproduce the same raw source files for the same code and fixed seed.
- Prioritization output is a simulated scenario recommendation derived from generated data and documented assumptions; it is not an observed business outcome.
- The validation flow does not certify management KPI reporting.
