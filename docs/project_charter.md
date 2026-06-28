# Project Charter

## Project Objective

RenewalOS is a synthetic analytics engineering portfolio project that demonstrates how a B2B company could assess trust in ARR, NRR, churn, renewal, and account-health metrics before using those metrics for management decisions or Customer Success prioritization.

The objective is not to prove business impact. The objective is to design a defensible workflow for metric reconciliation, data-quality detection, and decision support using simulated data.

## Target Users

- Revenue Operations teams responsible for metric definitions, source-system alignment, and pipeline quality.
- Customer Success leaders deciding which accounts need attention when team capacity is limited.
- Sales leadership reviewing renewals, churn risk, and expansion or contraction signals.
- Finance teams validating revenue movements and management reporting assumptions.

## Decision Workflow

1. Confirm that the relevant source domains are present, current, and internally consistent.
2. Run data-quality checks against known failure scenarios.
3. Block or qualify management KPIs when critical checks fail.
4. Reconcile revenue movement from opening ARR to closing ARR using simulated source domains.
5. Separate management KPIs from diagnostic indicators.
6. Identify accounts that may need Customer Success attention only after relevant checks pass.
7. Prioritize accounts by combining ARR at risk, renewal timing, health deterioration, and available intervention capacity.
8. Present recommendations as decision support, not as factual predictions of outcomes.

## In Scope

- Conceptual design for synthetic B2B revenue and account-health analytics.
- Definitions for key revenue, retention, churn, renewal, and health metrics.
- Synthetic source-domain descriptions and expected data grain.
- Reproducible synthetic source-data generation with controlled quality incidents.
- Local DuckDB and dbt diagnostic warehouse layers.
- Quality, reconciliation, account-health, and prioritization evidence layers.
- Decision policies for when metrics can be used and how account prioritization should work.
- Durable project instructions for future Codex work.

## Out of Scope

- Real customer data or real company data.
- Proprietary business logic, private schemas, or internal-system references.
- Production datasets, notebooks, screenshots, Docker files, deployment files, or production operations.
- Claims about business impact, production readiness, model accuracy, or completed analysis.
- A detailed source schema before the conceptual domains are reviewed.
- Automated account outreach or operational execution.

## Success Criteria

- A reviewer can understand the business problem, intended users, and planned decision workflow.
- Every documented metric has a clear business meaning, intended grain, required source domains, likely failure modes, and KPI classification.
- Source domains are described without relying on real company schemas or proprietary system details.
- Failure scenarios are realistic and tied to management or diagnostic risk.
- Decision rules prevent account prioritization when relevant data-quality checks fail.
- Synthetic-data limitations and assumptions remain visible throughout the project.

## Assumptions That Must Remain Visible

- All data and future examples are simulated.
- Future source systems are representative domains, not replicas of any real company's systems.
- Metric logic may change after source-domain design is reviewed.
- Account-health indicators will be diagnostic until validated against clearly defined simulated outcomes.
- Intervention effectiveness must be treated as a scenario assumption unless supported by experimental evidence.
- Any future model score should be interpreted as a recommendation signal, not as a statement of fact.

## Risks and Limitations

- Synthetic data can demonstrate analytical reasoning but cannot prove real-world impact.
- Metric definitions may look precise while still depending on unresolved source-domain assumptions.
- Simulated incidents may not cover every production data failure mode.
- Account-health logic can encode subjective weighting choices if assumptions are not documented.
- Prioritization can over-focus on large accounts unless capacity and timing constraints are explicit.
- Presenting recommendations without data-quality gates could make unreliable signals appear decision-ready.
