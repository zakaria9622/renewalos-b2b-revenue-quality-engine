# Decision Policy

This policy defines future decision logic in words. It is design-phase guidance only and does not represent implemented automation, model output, or completed analysis.

## Data-Quality Gate

No account should be prioritized for Customer Success action until the relevant data-quality checks pass.

If critical checks fail for an account, contract, billing event, usage snapshot, support record, or Customer Success interaction, the account should be placed into an exception or review state rather than a recommended action state.

Management KPIs should be blocked, qualified, or clearly labelled when unresolved data-quality failures could distort the result.

## Prioritization Inputs

Future CSM prioritization must consider:

- ARR at risk, using reconciled and validated recurring revenue signals.
- Renewal timing, including whether the account is inside a meaningful intervention window.
- Health deterioration, using diagnostic signals such as usage decline, support burden, unresolved incidents, or negative Customer Success notes.
- Intervention capacity, including the number of accounts a team can realistically address during the period.

No single input should automatically determine priority.

## Churn Probability Is Not Enough

A high churn probability alone is not enough to prioritize an account.

An account with high estimated churn risk may still be a poor intervention target if the ARR at risk is low, the renewal date is too far away or already passed, the signal is based on stale data, the account lacks a clear owner, or the team has no capacity for meaningful action.

Likewise, a moderate-risk account may deserve attention if ARR at risk is high, renewal timing is urgent, recent health deterioration is clear, and data-quality checks have passed.

## Recommendation Status

Model outputs, health scores, and prioritization rankings are recommendations, not facts.

Any future model score should be presented with:

- The source domains used.
- The checks that passed or failed.
- The assumptions behind prioritization.
- The reason an account is recommended, deferred, or excluded.
- A clear synthetic-data label.

## Intervention Effectiveness

Intervention effectiveness must be presented as a scenario assumption unless supported by experiment data.

Future simulated analysis may describe hypothetical outcomes, but it must not claim that Customer Success intervention reduced churn, protected ARR, improved NRR, or caused business impact unless an explicitly designed experiment or valid causal method supports that claim.

## Decision States

Future account decision states should separate data readiness from action priority:

- **Blocked:** Required data-quality checks failed or source relationships cannot be trusted.
- **Review:** Data is incomplete or contradictory but may be resolved by analyst review.
- **Monitor:** Data checks passed, but timing, ARR exposure, health trend, or capacity does not justify immediate action.
- **Prioritize:** Data checks passed and the account has meaningful ARR at risk, relevant renewal timing, clear health deterioration, and capacity for intervention.
- **Excluded:** The account is outside the scope of the current decision cycle or lacks a valid basis for comparison.
