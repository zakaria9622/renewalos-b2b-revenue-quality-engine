# Metric Definitions

These definitions are conceptual and design-phase only. They do not depend on final source fields, and they should not be treated as implemented formulas.

## Opening ARR

- **Business meaning:** The recurring annualized revenue base at the start of a reporting period.
- **Intended grain:** Account and reporting period, with contract or subscription detail available for audit.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events.
- **Likely failure modes:** Missing prior-period contract state, duplicate active contracts, inconsistent account identifiers, late billing events, or contracts incorrectly marked active.
- **KPI treatment:** Management KPI when reconciled and validated.

## New ARR

- **Business meaning:** Recurring annualized revenue added from newly acquired customers or newly activated accounts during the reporting period.
- **Intended grain:** Account and reporting period, tied to the first qualifying recurring revenue event.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events.
- **Likely failure modes:** Misclassified returning customers, delayed contract activation, duplicate account records, or billing events that arrive before account creation.
- **KPI treatment:** Management KPI when reconciled and validated.

## Expansion ARR

- **Business meaning:** Additional recurring annualized revenue from existing accounts, such as upgrades, added seats, additional products, or expanded contract value.
- **Intended grain:** Account, contract or subscription change, and reporting period.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events.
- **Likely failure modes:** Expansion confused with new ARR, overlapping amendments, missing amendment dates, negative adjustments posted as expansions, or account merges that obscure history.
- **KPI treatment:** Management KPI when reconciled and validated.

## Contraction ARR

- **Business meaning:** Reduction in recurring annualized revenue from existing accounts that remain active after downsell, seat reduction, product removal, or price reduction.
- **Intended grain:** Account, contract or subscription change, and reporting period.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events, optional Customer Success interactions.
- **Likely failure modes:** Contraction confused with churn, missing downgrade records, credits treated as recurring reductions, or late billing events shifting the movement into the wrong period.
- **KPI treatment:** Management KPI when reconciled and validated.

## Churned ARR

- **Business meaning:** Recurring annualized revenue lost when an account or subscription no longer renews or remains active.
- **Intended grain:** Account and reporting period, with subscription or contract lineage for audit.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events, optional product usage or activity.
- **Likely failure modes:** Churned accounts with active billing or usage, missing termination dates, conflicting renewal statuses, or inactive contracts still marked active.
- **KPI treatment:** Management KPI when reconciled and validated.

## Closing ARR

- **Business meaning:** The recurring annualized revenue base at the end of a reporting period after accounting for new ARR, expansion, contraction, churn, and other approved recurring adjustments.
- **Intended grain:** Account and reporting period, with supporting movement detail.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events.
- **Likely failure modes:** Revenue movements that do not reconcile, duplicate active contracts, late events, orphaned billing records, or inconsistent account identifiers.
- **KPI treatment:** Management KPI when reconciled and validated.

## Gross Revenue Retention

- **Business meaning:** The share of starting recurring revenue retained from existing accounts before counting expansion.
- **Intended grain:** Cohort or reporting period, usually aggregating account-level opening ARR, contraction ARR, and churned ARR.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events.
- **Likely failure modes:** Expansion incorrectly included, churn and contraction misclassified, opening ARR overstated by duplicates, or period boundaries applied inconsistently.
- **KPI treatment:** Management KPI when reconciled and validated.

## Net Revenue Retention

- **Business meaning:** The share of starting recurring revenue retained after accounting for expansion, contraction, and churn among existing accounts.
- **Intended grain:** Cohort or reporting period, aggregating account-level revenue movement for existing accounts.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events.
- **Likely failure modes:** New ARR included in the existing-customer cohort, expansion misclassified, missing contraction events, duplicate contracts, or unresolved account merges.
- **KPI treatment:** Management KPI when reconciled and validated.

## Logo Churn

- **Business meaning:** The loss of customer accounts, regardless of the ARR size associated with each lost account.
- **Intended grain:** Account and reporting period.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events, optional usage activity.
- **Likely failure modes:** Duplicate account records, parent-child account confusion, inactive accounts with active subscriptions, or churn status disagreement between CRM and billing.
- **KPI treatment:** Management KPI when account identity and status are validated.

## Renewal Rate

- **Business meaning:** The share of accounts or renewable recurring revenue that renews within a defined renewal window.
- **Intended grain:** Account renewal event and reporting period, with account-level and ARR-weighted views possible.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events, Customer Success interactions.
- **Likely failure modes:** Missing renewal dates, overlapping contract periods, early renewals counted in the wrong period, verbal renewal statuses not reflected in billing, or renewal opportunities not tied to contracts.
- **KPI treatment:** Management KPI when renewal population and status rules are validated.

## Account-Health Score

- **Business meaning:** A diagnostic signal summarizing account risk or strength based on indicators such as product activity, support burden, Customer Success engagement, renewal timing, and revenue exposure.
- **Intended grain:** Account and health snapshot date.
- **Required source domains:** Accounts / CRM, contracts, subscription or billing events, product usage or activity, support tickets, Customer Success interactions, optional operational incidents.
- **Likely failure modes:** Stale usage extracts, duplicated support tickets, missing interaction logs, biased weighting assumptions, unresolved billing status, or health signals calculated before data-quality checks pass.
- **KPI treatment:** Diagnostic KPI. It may support prioritization but should not be treated as a standalone management KPI.
