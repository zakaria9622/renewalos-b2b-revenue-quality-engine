# Failure Scenarios

These scenarios define deliberately injected incidents for the simulated data. They are intended to test whether metrics and decisions remain trustworthy when realistic data-quality failures occur.

## 1. Duplicate Active Contracts

- **Why it matters:** The same account may appear to have more recurring revenue than it actually has.
- **KPI or decision distorted:** Opening ARR, closing ARR, NRR, GRR, renewal rate, and CSM prioritization by ARR at risk.
- **Detection approach:** Identify accounts with more than one active contract covering the same product or commercial period without an explicit amendment relationship.
- **Analyst recommendation:** Quarantine the affected account from management KPI reporting until the duplicate is resolved or one record is identified as the valid contract.

## 2. Overlapping Contract Periods

- **Why it matters:** Revenue can be counted twice or assigned to the wrong reporting period.
- **KPI or decision distorted:** ARR movement, renewal rate, churned ARR, contraction ARR, and renewal timing.
- **Detection approach:** Check for contract periods for the same account that overlap without a documented renewal, amendment, or replacement reason.
- **Analyst recommendation:** Review contract lineage and define which record controls ARR for each period.

## 3. Billing Event Received Late

- **Why it matters:** A real revenue movement may appear in the wrong month or quarter.
- **KPI or decision distorted:** New ARR, expansion ARR, contraction ARR, churned ARR, closing ARR, and period-level NRR.
- **Detection approach:** Compare event effective dates with ingestion or posting dates and flag events outside the accepted latency window.
- **Analyst recommendation:** Use effective-date logic for reporting, disclose late-arrival adjustments, and restate simulated period metrics where needed.

## 4. Orphaned Billing Event

- **Why it matters:** Revenue movement cannot be traced to a known account or contract.
- **KPI or decision distorted:** ARR reconciliation, new ARR, expansion ARR, contraction ARR, churned ARR, and account-level prioritization.
- **Detection approach:** Identify billing or subscription events that lack a valid account and contract relationship.
- **Analyst recommendation:** Exclude orphaned events from management KPIs until mapped, and create a reconciliation queue for source-system correction.

## 5. Inconsistent Account Identifiers

- **Why it matters:** Activity, contracts, tickets, and billing may be split across multiple account IDs or incorrectly merged.
- **KPI or decision distorted:** Logo churn, ARR by account, account-health score, renewal rate, and CSM prioritization.
- **Detection approach:** Flag records with mismatched account IDs across domains, duplicate names with conflicting IDs, or events tied to retired identifiers.
- **Analyst recommendation:** Resolve identity mapping before calculating account-level metrics or health scores.

## 6. Negative ARR Movement Without Explanation

- **Why it matters:** A revenue drop may be a valid contraction, a credit, a correction, or a data error.
- **KPI or decision distorted:** Contraction ARR, churned ARR, GRR, NRR, closing ARR, and risk prioritization.
- **Detection approach:** Identify negative recurring movements that are not tied to an approved contraction, churn, correction, or contract amendment category.
- **Analyst recommendation:** Classify the movement source before including it in recurring revenue metrics.

## 7. Contract Marked Active After End Date

- **Why it matters:** Expired contracts may continue contributing to ARR even though the commercial commitment ended.
- **KPI or decision distorted:** Closing ARR, churned ARR, renewal rate, logo churn, and renewal priority lists.
- **Detection approach:** Flag contracts whose status is active when the current or reporting date is after the contract end date and no renewal is linked.
- **Analyst recommendation:** Confirm whether a renewal exists, update status logic, and block affected accounts from final KPI rollups until resolved.

## 8. Churned Account With Active Usage

- **Why it matters:** The account may have been wrongly marked churned, or product usage may be linked to the wrong account.
- **KPI or decision distorted:** Logo churn, churned ARR, account-health score, and CSM outreach priority.
- **Detection approach:** Find accounts marked churned that show meaningful usage after the churn effective date.
- **Analyst recommendation:** Investigate account status and usage mapping before treating the account as churned or active.

## 9. Missing Renewal Date

- **Why it matters:** The team cannot reliably identify which accounts need attention before renewal.
- **KPI or decision distorted:** Renewal rate, renewal pipeline reporting, CSM capacity planning, and prioritization.
- **Detection approach:** Flag active contracts or accounts without a renewal date or renewal window.
- **Analyst recommendation:** Exclude affected accounts from renewal timing decisions and request source-system completion.

## 10. Stale Usage Extract

- **Why it matters:** Health deterioration may be missed or falsely reported because activity data is outdated.
- **KPI or decision distorted:** Account-health score, churn-risk diagnostics, and CSM prioritization.
- **Detection approach:** Compare the latest usage snapshot date with the reporting date and flag extracts outside the freshness threshold.
- **Analyst recommendation:** Mark health scores as stale and prevent prioritization that depends on usage until the extract is refreshed.

## 11. Duplicate Support Ticket

- **Why it matters:** Support burden and customer dissatisfaction may be overstated.
- **KPI or decision distorted:** Account-health score, support burden diagnostics, and CSM intervention priority.
- **Detection approach:** Detect tickets with matching account, issue category, created time window, and text or external reference similarity.
- **Analyst recommendation:** Deduplicate before using ticket volume or severity in health scoring.

## 12. CRM Renewal Status Disagrees With Billing Status

- **Why it matters:** Sales or Customer Success may believe an account renewed while billing shows cancellation, or the reverse.
- **KPI or decision distorted:** Renewal rate, churned ARR, closing ARR, account status, and management reporting.
- **Detection approach:** Compare CRM renewal status with contract and billing status for accounts in the renewal window.
- **Analyst recommendation:** Create an exception list and require source-system resolution before reporting renewal outcomes.

## 13. Account Missing Segment or Owner

- **Why it matters:** Leadership cannot interpret risk by segment, and CSM work cannot be assigned reliably.
- **KPI or decision distorted:** Segment-level ARR, churn diagnostics, capacity planning, and prioritization.
- **Detection approach:** Flag active accounts missing required ownership or segmentation attributes.
- **Analyst recommendation:** Keep affected accounts in revenue reconciliation where possible, but exclude them from segment or owner-level decision views until completed.

## 14. Customer-Success Interaction Logged to Wrong Account

- **Why it matters:** Intervention history and relationship health may be assigned to the wrong customer.
- **KPI or decision distorted:** Account-health score, intervention tracking, renewal readiness, and CSM prioritization.
- **Detection approach:** Identify interactions where account ID, contact domain, opportunity, or contract linkage conflicts.
- **Analyst recommendation:** Correct the account linkage before using interaction history to assess health or intervention effectiveness.
