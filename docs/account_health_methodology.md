# Account Health Methodology

RenewalOS account health is an explainable diagnostic assessment for synthetic account-month records. It combines supported source signals into a review-oriented score only when the account-month passes the required quality and assessability gates.

This is not a churn model, renewal prediction, automated prioritization system, or claim of Customer Success impact.

## Purpose

The account-health layer helps a Revenue Operations or Customer Success reviewer understand whether supported synthetic signals suggest account friction, renewal timing pressure, or data caveats that should be reviewed before any future decision workflow.

The output is diagnostic. It does not approve management KPI reporting and does not decide which accounts should receive intervention.

## Input Signals

The current implementation uses only fields available in the generated source data and existing dbt models:

- revenue exposure from active contract ARR and reconciliation diagnostics;
- renewal timing from contract renewal dates and contract end dates;
- account lifecycle and CRM renewal status from accounts;
- usage level and usage trend from monthly usage events;
- support-ticket burden from 90-day ticket counts, open or pending status, and severity;
- Customer Success engagement from 90-day interaction coverage and sentiment;
- account-month quality status from the quality-control layer.

Unavailable signals are not inferred. There are no contact-level details, product feature adoption fields, opportunity stages, intervention capacity fields, experiment outcomes, or real customer outcomes.

## Quality Gates

The account-health mart uses these assessment statuses:

- `blocked_due_to_data_quality`: critical account-month quality exceptions are present. Health score and health band are null.
- `not_assessable`: required current usage, active contract exposure, or observed revenue-balance evidence is absent. Health score and health band are null.
- `eligible_with_caveat`: a diagnostic score is available, but a warning, reconciliation gap, billing caveat, renewal-status disagreement, or missing renewal-date caveat exists.
- `eligible`: a diagnostic score is available and no mapped gate caveat is observed.

Blocked and not-assessable records must not receive normal health scores or operational recommendations.

## Scoring Components

The score is a simulated diagnostic score from 0 to 100. Higher values indicate fewer observed concerns under the current assumptions.

Component weights:

- revenue evidence: 15 points;
- renewal timing: 20 points;
- usage: 30 points;
- support burden: 20 points;
- Customer Success engagement: 15 points.

Health bands for scored records:

- `critical`: 0-44;
- `at_risk`: 45-64;
- `monitor`: 65-79;
- `stable`: 80-100.

These bands are simulated portfolio assumptions. They are not trained thresholds and are not calibrated to observed churn or renewal outcomes.

## Simulated Thresholds

Revenue component:

- 15 points when no supported revenue or billing concern is observed;
- 8 points when a reconciliation gap or billing caveat is observed;
- 0 points when critical data quality blocks scoring.

Renewal component:

- 5 points when renewal or contract end timing is current, within 30 days, or missing;
- 10 points when timing is 31-90 days away;
- 15 points when timing is 91-180 days away;
- 20 points when no near-term renewal timing concern is observed.

Usage component:

- 5 points for inactive usage, zero active users, or an active-user decline of at least 50 percent;
- 15 points for very low usage or an active-user decline of at least 25 percent;
- 30 points when no supported usage concern is observed.

Support component:

- 5 points for high-severity tickets, heavy open-ticket burden, or at least four tickets in the 90-day lookback;
- 12 points for open or multiple recent tickets;
- 20 points when no supported support concern is observed.

Customer Success component:

- 3 points for recent concerned sentiment;
- 8 points when no recent Customer Success interaction is observed;
- 15 points when recent Customer Success coverage has no supported concern signal.

## Explanation Layer

`mart_account_health_explanations` provides one row per account-month and explanation component. Each row includes the component value or signal, impact direction, severity, plain-language explanation, and source-lineage reference.

The explanation layer is meant to make the score auditable. It is not a recommendation narrative or automated outreach instruction.

## Coverage Layer

`mart_account_health_coverage` summarizes total observable account-months and counts by assessment status and reason category. These are synthetic diagnostic outputs, not management KPIs.

## Interpretation Guidance

Revenue Operations can use the output to check whether health scoring is being blocked by quality defects or missing evidence. Customer Success leaders can review scored records as diagnostic context, but should not treat the health band as a prediction or an instruction to prioritize an account.

Any future prioritization stage must separately consider intervention capacity, timing, decision policy, and validated business rules.

## Limitations

- All data is synthetic.
- The thresholds are simulated assumptions.
- The score is not trained, calibrated, or validated against outcomes.
- The source data has a deliberately finite set of quality incidents.
- The output does not calculate churn probability, renewal probability, or business impact.
- The output does not automate Customer Success prioritization or outreach.
