with health as (
    select * from {{ ref('mart_account_health') }}
),

totals as (
    select
        count(*) as total_observable_account_months,
        count(*) filter (
            where assessment_status = 'blocked_due_to_data_quality'
        ) as blocked_account_months,
        count(*) filter (
            where assessment_status = 'not_assessable'
        ) as not_assessable_account_months,
        count(*) filter (
            where assessment_status = 'eligible_with_caveat'
        ) as eligible_with_caveat_account_months,
        count(*) filter (
            where assessment_status = 'eligible'
        ) as eligible_account_months
    from health
),

reason_counts as (
    select
        assessment_status,
        assessment_reason_category as reason_category,
        count(*) as reason_count
    from health
    group by assessment_status, assessment_reason_category
)

select
    'synthetic_diagnostic_account_health' as synthetic_data_label,
    totals.total_observable_account_months,
    totals.blocked_account_months,
    totals.not_assessable_account_months,
    totals.eligible_with_caveat_account_months,
    totals.eligible_account_months,
    reason_counts.assessment_status,
    reason_counts.reason_category,
    reason_counts.reason_count,
    false as is_predictive_model_output,
    false as is_automated_recommendation
from totals
cross join reason_counts
