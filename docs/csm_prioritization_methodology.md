# CSM Prioritization Methodology

## Purpose

The CSM prioritization layer demonstrates how a limited Customer Success team could prioritize
synthetic account-months only after diagnostic data-quality and account-health gates are applied.
It is a scenario analysis layer, not an operational system and not evidence of intervention impact.

## Source Inputs

The prioritization layer uses only existing synthetic dbt outputs:

- `mart_account_health`
- `mart_account_health_explanations`

The candidate model carries account-month fields from the account-health layer, including
assessment status, quality status, health band, revenue exposure, renewal urgency, diagnostic
concerns, and plain-language explanation drivers.

## Eligibility Gate

`mart_csm_priority_candidates` keeps every account-month from `mart_account_health`, but marks
candidate eligibility separately. A row is eligible only when:

- `assessment_status` is `eligible` or `eligible_with_caveat`;
- `health_score` is present;
- `revenue_exposure_amount` is present and positive.

Rows with `blocked_due_to_data_quality` or `not_assessable` remain visible with exclusion reasons.
They are not passed into the prioritization optimizer.

## Baseline Inputs Versus Optimization

`mart_csm_prioritization_inputs` converts eligible account-months into scenario inputs:

- `priority_tier`;
- `estimated_account_value_at_risk`;
- `estimated_effort_hours`;
- `assumed_intervention_effectiveness`;
- `expected_protected_value`;
- `priority_score`;
- scenario and assumption metadata.

The Python optimizer then solves a capacity-constrained selection problem with OR-Tools CP-SAT over
a documented top-candidate solver pool. The objective is to maximize simulated expected protected
value within that pool while respecting:

- total available CSM hours;
- total account-contact capacity;
- one selected row per account-month.

## Output Fields

The generated CSV contains selected, non-selected, and excluded rows. It includes scenario ID,
assumption version, account-month fields, quality gate status, health drivers, revenue exposure,
renewal urgency, expected protected value, estimated effort, selected flag, and selection or
non-selection reason.

## Guardrails

This layer does not:

- calculate management KPIs;
- create dashboards, charts, notebooks, or application features;
- train or apply machine-learning models;
- claim that an intervention would retain revenue;
- claim business impact, accuracy, lift, or ROI.

Raw and diagnostic synthetic data remain unsuitable for management KPI reporting. Any real-world
use would require validated source systems, human review, governance approval, and measurement of
actual intervention outcomes.
