# Data Domains

These are future source domains and expected grains only. This document intentionally avoids detailed schemas until the design is reviewed.

## Accounts / CRM

- **Primary business purpose:** Represent customer and prospect organizations, ownership, lifecycle stage, segment, and commercial context.
- **Expected entity or event grain:** One account record per business entity, with possible parent-child relationships and lifecycle status history.
- **Expected relationship to other domains:** Accounts should connect to contracts, billing events, usage activity, support tickets, Customer Success interactions, and optional operational incidents.
- **Likely data-quality risks:** Duplicate accounts, inconsistent account identifiers, stale ownership, missing segment or lifecycle status, unclear parent-child rollups, and CRM status disagreement with billing status.

## Contracts

- **Primary business purpose:** Represent commercial commitments, renewal windows, active periods, contracted recurring value, and amendment history.
- **Expected entity or event grain:** One contract or amendment record per contractual period or commercial change.
- **Expected relationship to other domains:** Contracts should link accounts to subscription or billing events and provide context for renewals, churn, expansion, and contraction.
- **Likely data-quality risks:** Duplicate active contracts, overlapping periods, missing renewal dates, contracts marked active after their end date, amendments that cannot be tied to prior contracts, and inconsistent status values.

## Subscription or Billing Events

- **Primary business purpose:** Represent recurring revenue activity, invoice or subscription changes, start and end events, credits, cancellations, and adjustments.
- **Expected entity or event grain:** One billing or subscription event per revenue-relevant change or transaction.
- **Expected relationship to other domains:** Billing events should connect to accounts and contracts, and should provide evidence for ARR movement and reconciliation.
- **Likely data-quality risks:** Late-arriving events, orphaned events, duplicate transactions, credits mistaken for recurring changes, negative ARR movements without explanation, and mismatched billing account identifiers.

## Product Usage or Activity

- **Primary business purpose:** Represent whether accounts are actively using the product and whether usage is improving, stable, or deteriorating.
- **Expected entity or event grain:** Account-level activity snapshots or product events over time.
- **Expected relationship to other domains:** Usage should connect to accounts and help interpret churn risk, renewal readiness, and health deterioration.
- **Likely data-quality risks:** Stale extracts, missing activity for active accounts, churned accounts with active usage, usage events tied to obsolete identifiers, and inconsistent aggregation windows.

## Support Tickets

- **Primary business purpose:** Represent customer support burden, unresolved issues, severity, and service experience.
- **Expected entity or event grain:** One support ticket per customer-reported issue, with status and severity changes over time.
- **Expected relationship to other domains:** Tickets should connect to accounts and can contribute to diagnostic account-health indicators.
- **Likely data-quality risks:** Duplicate tickets, missing account links, inconsistent severity, reopened tickets counted incorrectly, and status values that do not reflect resolution reality.

## Customer-Success Interactions

- **Primary business purpose:** Represent CSM touchpoints, renewal conversations, risk notes, intervention attempts, and customer sentiment.
- **Expected entity or event grain:** One logged interaction, task, meeting, note, or touchpoint per account event.
- **Expected relationship to other domains:** Customer Success interactions should connect to accounts, contracts, renewal windows, and health signals.
- **Likely data-quality risks:** Missing interaction logs, subjective notes without consistent categories, stale risk flags, duplicated tasks, and interactions not tied to renewal or account context.

## Optional Claims or Operational Incidents

- **Primary business purpose:** Represent operational disruptions, claims, service incidents, or delivery issues that may affect customer experience and renewal risk.
- **Expected entity or event grain:** One operational incident or claim event per account, service unit, or affected period.
- **Expected relationship to other domains:** Incidents should connect to accounts and may help explain support burden, usage decline, or Customer Success risk notes.
- **Likely data-quality risks:** Incidents not linked to the correct account, inconsistent severity, missing resolution dates, duplicate incident reports, and unclear relationship to recurring revenue.
