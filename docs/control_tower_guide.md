# Control Tower Guide

## Intended Audience

The RenewalOS Control Tower is a local Streamlit interface for Revenue Operations, Customer
Success, Sales leadership, and Finance reviewers. It helps those users inspect synthetic
diagnostic outputs before relying on revenue metrics or prioritization recommendations.

## How To Interpret The Pages

### Landing Page

The landing page confirms the app can read the local DuckDB warehouse and shows the current
trust-status summary. It is a starting point, not a KPI dashboard.

### Data Trust

Use this page first. It shows KPI gate status, account-month quality status, exception categories,
and registered incident detection coverage. If management KPI reporting is not approved by
`mart_kpi_trust_status`, users should treat revenue metrics as restricted.

### Revenue Reconciliation

This page shows diagnostic reconciliation statuses and account-month gaps. Gaps are intentionally
preserved. The view supports review and investigation, not certified ARR, NRR, GRR, churn, or
renewal reporting.

### Account Health

This page shows rule-based health coverage, eligible versus blocked records, health-band
distribution for scored rows, account-month detail, and explanation drivers. It is not a churn
model or renewal prediction.

### CSM Prioritization

This page shows simulated scenario assumptions, candidate eligibility, exclusions, capacity use,
and generated recommendations. Expected protected value is a synthetic scenario estimate, not
observed retained revenue or business impact.

### Methodology

This page maps the app back to project documents and project limitations.

## Supported Decisions

The app supports local review of:

- whether current synthetic diagnostic outputs restrict management KPI reporting;
- which quality issues and incident categories need review;
- which account-months are eligible for health assessment;
- which account-months were selected by the simulated prioritization scenario.

## Decisions The App Must Not Support

The app must not be used to:

- claim trusted ARR, NRR, GRR, churn, renewal, or retention metrics;
- claim business impact or intervention effectiveness;
- predict churn or renewal probability;
- automate Customer Success outreach;
- represent synthetic account IDs as real customers;
- make production decisions.

## Quality Gates

Quality gates affect every downstream page. Blocked and not-assessable account-months remain
visible as exclusions. The prioritization layer must not select blocked, quality-blocked, or
not-assessable rows. If the warehouse or prioritization export has not been built, the app fails
with a clear local setup message instead of silently hiding missing outputs.
