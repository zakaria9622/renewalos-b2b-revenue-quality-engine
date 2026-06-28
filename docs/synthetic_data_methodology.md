# Synthetic Data Methodology

RenewalOS uses synthetic source data so the project can demonstrate analytics engineering patterns without real customer data, proprietary schemas, internal terminology, or private business logic.

## Simulation Window and Scope

- Fixed random seed: `20260228`.
- Scenario version: `synthetic_b2b_sources_v1`.
- Simulation window: 24 monthly periods from `2024-01-01` through `2025-12-31`.
- Portfolio size: 750 fictional accounts.
- Account names use generic synthetic labels, such as `Synthetic Account 0001 LLC`.

## Source-Domain Grains

- `accounts.csv`: one row per synthetic account.
- `contracts.csv`: one row per contract period.
- `billing_events.csv`: one row per ARR movement or billing event.
- `usage_events.csv`: one row per account-month.
- `support_tickets.csv`: one row per support ticket.
- `cs_interactions.csv`: one row per Customer Success interaction.
- `incident_registry.csv`: one row per controlled incident injected into the raw data.

## Baseline Generation and Incident Injection

Baseline generation creates internally plausible source-domain rows with synthetic labels and no intentional quality flags.

Incident injection runs after baseline generation and deliberately introduces controlled problems based on `docs/failure_scenarios.md`. The incident layer is separate so future work can compare clean baseline assumptions with raw source data that contains known issues.

Each injected incident is recorded in `incident_registry.csv` with:

- incident ID;
- scenario name;
- affected source domain;
- affected record identifier;
- expected detection method;
- expected business impact;
- severity.

## Known Limitations

- The data is useful for testing reconciliation and data-quality workflows, not for proving real-world business impact.
- Source-domain fields are representative and synthetic, not replicas of any real company's systems.
- The incident set is deliberate and finite; it does not cover every possible production data failure.
- No final ARR, NRR, churn, renewal, health-score, prioritization, or intervention-effectiveness result is calculated here.

## Reporting Rule

Raw synthetic source data must not be used directly for management KPI reporting. Future KPI work must first run data-quality checks, reconcile source relationships, and clearly label outputs as simulated.
