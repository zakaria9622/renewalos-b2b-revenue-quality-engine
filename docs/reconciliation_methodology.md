# Reconciliation Methodology

RenewalOS reconciliation controls are diagnostic. They expose whether supported synthetic billing movements align with contract-derived balances, but they do not produce approved ARR, NRR, GRR, churn, renewal, or account-health KPIs.

## Grain

The current reconciliation diagnostic grain is one row per observable `account_id` and `account_month`.

The account-month spine is derived from source activity across accounts, contracts, billing events, usage events, support tickets, and Customer Success interactions.

## Supported Movement Components

The current movement mapping uses only actual generated billing event categories:

- `opening_arr`;
- `new_arr`;
- `expansion_arr`;
- `contraction_arr`;
- `churned_arr`.

`renewal` is treated as a renewal marker with no ARR movement component. `manual_adjustment` is retained as an unsupported manual adjustment and is not included in expected closing balance.

## Balance Logic

`mart_revenue_reconciliation_diagnostics` exposes:

- opening balance from prior supported billing movements;
- current supported movement components;
- expected closing balance as opening balance plus supported current-month movements;
- observed closing balance from source contract exposure where derivable;
- reconciliation gap as observed closing balance minus expected closing balance;
- quality blocker fields from the account-month quality status model.

Gaps are retained. The model does not force gaps to zero, suppress exceptions, or infer corrected source values.

## Diagnostic Status

The reconciliation status is assigned as:

- `blocked_by_quality_exception` when a critical quality exception maps to the account-month;
- `not_assessable_no_observed_contract_balance` when no observed contract closing balance can be derived;
- `gap_observed` when expected and observed balances are both derivable and differ;
- `eligible_with_caveat_quality_warning` when no gap is observed but warning exceptions exist;
- `no_gap_observed_preliminary` when no nonzero gap is observed in the current diagnostic comparison.

These statuses support review queues and future metric gating. They are not management KPI outputs.

## KPI Gate

`mart_kpi_trust_status` converts quality and reconciliation diagnostics into a future revenue-metric gate status:

- `blocked`;
- `eligible_with_caveat`;
- `not_assessable`.

`is_management_kpi_reporting_approved` remains false for every row in the current implementation.

## Known Limitations

The controls operate on synthetic source data and a deliberately finite incident set. They do not model every production reconciliation issue. They also do not define final ARR metric transformations, cohort logic, retention formulas, or account-prioritization rules.

Raw source data and diagnostic marts must not be used directly for management KPI reporting.
