# RenewalOS

## B2B Revenue Reconciliation & Account-Health Decision System

RenewalOS is a synthetic portfolio project that designs a trustworthy analytics workflow for reconciling B2B revenue metrics and prioritizing Customer Success attention only after data quality is understood.

## Current Status

**Design phase only — no data, models, or results yet.**

No datasets, pipelines, dbt models, dashboards, machine-learning code, notebooks, charts, screenshots, Docker files, or deployment artifacts have been created.

## Current Implementation Status

The repository now contains a minimal Python package scaffold, local configuration paths, placeholder data directories, a Streamlit placeholder page, and CI configuration.

No source data, synthetic data generators, data pipelines, KPI calculations, reconciliation checks, dbt models, dashboards, charts, notebooks, machine-learning models, optimization logic, decision outputs, or business results are implemented.

## Local Setup

This project targets Python 3.12.

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest
```

## Business Problem

B2B companies often use ARR, NRR, churn, renewal, and account-health metrics to make Sales, Customer Success, Finance, and management decisions. Those decisions become risky when source systems disagree, revenue movements do not reconcile, account records are incomplete, or risk indicators are unreliable.

RenewalOS is designed to show how an analytics engineering project can make those risks visible before operational decisions are made.

## Project Questions

1. Can the company trust its ARR, NRR, churn, and renewal metrics?
2. Which data-quality issues could distort management decisions?
3. Which accounts should a limited Customer Success team prioritize once the data is trustworthy?

## Planned Architecture

The future architecture is expected to include simulated source domains, validation checks, reconciled metric logic, account-health diagnostics, and decision-policy documentation.

Planned components:

- Synthetic source data representing CRM accounts, contracts, billing or subscription events, usage activity, support tickets, Customer Success interactions, and optional operational incidents.
- Data-quality checks that detect known failure scenarios before KPI reporting or prioritization.
- Revenue reconciliation logic that explains ARR movement from opening ARR to closing ARR.
- Metric definitions that distinguish management KPIs from diagnostic KPIs.
- Account-health decision rules that combine revenue at risk, renewal timing, health deterioration, and intervention capacity.
- Documentation that keeps assumptions, limitations, and synthetic-data labels visible.

## Synthetic-Data Disclaimer

This is a synthetic public portfolio project only. It does not use real customer data, real company schemas, proprietary business logic, or internal systems. All future metrics, examples, source systems, incidents, and analysis outputs must be explicitly labelled as simulated.

The project must not mention unrelated real companies, imply access to internal systems, or present fabricated business impact, model accuracy, screenshots, or completed analysis.

## Planned Future Stages

1. Finalize design documents and review assumptions.
2. Design simulated source schemas and data-generation rules.
3. Generate synthetic data with deliberately injected data-quality incidents.
4. Build validation checks and reconciliation tests.
5. Define conceptual metric transformations and traceability.
6. Create simulated management and diagnostic outputs only after validation passes.
7. Add account-prioritization logic with clearly labelled scenario assumptions.
8. Document limitations, review findings, and next analytical questions.
