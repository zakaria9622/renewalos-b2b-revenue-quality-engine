# Quality Control Framework

RenewalOS quality controls are diagnostic safeguards for synthetic source data. They detect known source problems, preserve affected identifiers, and gate future metric work before any management KPI can be reported.

These controls do not repair records, calculate final metrics, create dashboards, score accounts, or claim business impact.

## Control Scope

The current control layer covers the synthetic incidents registered in `data/raw/incident_registry.csv`:

- duplicate active contracts;
- overlapping contract periods;
- late-arriving billing events;
- orphaned billing events;
- inconsistent account identifiers;
- invalid negative ARR movements;
- active contracts after the observed end date;
- churned accounts with active usage;
- missing renewal dates;
- stale usage extracts;
- duplicate support tickets;
- CRM renewal-status disagreement with contract or billing status;
- active accounts missing segment or owner;
- Customer Success interactions linked to an unknown account identifier.

## Exception Outputs

The dbt quality models produce exception tables by source domain:

- `dq_contract_exceptions`;
- `dq_billing_exceptions`;
- `dq_usage_exceptions`;
- `dq_support_exceptions`;
- `dq_identifier_exceptions`.

Each exception row includes the rule identifier, severity, source domain, affected source-record identifier, account identifier when available, relevant date or account month when derivable, a concise explanation, and incident-registry linkage when matchable.

The models preserve defects for review. They do not filter them away or choose corrected source records.

## Detection Coverage

`dq_incident_detection_coverage` compares the registered synthetic incidents with detected exceptions. A row is marked `detected` when an exception links to the incident ID or to the same registered scenario. A `not_detected` row means the quality layer did not produce a matching exception and KPI work should not proceed until the gap is resolved or documented.

## Account-Month Quality Status

`dq_account_month_quality_status` assigns one status per observable account-month:

- `blocked`: at least one critical exception is mapped to the account-month.
- `warning`: no critical exception is mapped, but at least one warning exception is mapped.
- `eligible_with_caveat`: no mapped exception is observed, and the month has contract or billing evidence.
- `no_observed_issue`: no mapped exception is observed, and the month is observable only from non-revenue source activity.

These statuses are control inputs only. `eligible_with_caveat` does not mean a management KPI is approved.

## Validation Command

After generating raw data, loading DuckDB, and running dbt, validate the control outputs with:

```powershell
renewalos-validate-quality
```

This checks incident coverage, exception metadata, account-month status values, and whether reconciliation gaps remain observable.
