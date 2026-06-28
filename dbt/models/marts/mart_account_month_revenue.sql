with spine as (
    select * from {{ ref('int_account_month_spine') }}
),

movement_rollup as (
    select
        account_id,
        movement_month as account_month,
        count(*) as billing_event_count,
        sum(case when event_type = 'opening_arr' then arr_delta else 0 end) as opening_arr_movement,
        sum(case when event_type = 'new_arr' then arr_delta else 0 end) as new_arr_movement,
        sum(case when event_type = 'expansion_arr' then arr_delta else 0 end) as expansion_arr_movement,
        sum(case when event_type = 'contraction_arr' then arr_delta else 0 end) as contraction_arr_movement,
        sum(case when event_type = 'churned_arr' then arr_delta else 0 end) as churned_arr_movement,
        sum(case when is_manual_adjustment then arr_delta else 0 end) as manual_adjustment_amount,
        sum(case when is_supported_revenue_movement then arr_delta else 0 end)
            as supported_revenue_movement_amount,
        max(case when has_late_arrival then 1 else 0 end) = 1 as has_late_arrival,
        max(case when is_orphaned_account_id or is_orphaned_contract_id then 1 else 0 end) = 1
            as has_orphaned_billing_reference,
        max(case when has_invalid_negative_arr_movement then 1 else 0 end) = 1
            as has_invalid_negative_arr_movement,
        max(case when has_injected_quality_issue then 1 else 0 end) = 1
            as has_injected_quality_issue
    from {{ ref('int_billing_movements') }}
    where movement_month is not null
    group by account_id, movement_month
)

select
    spine.account_id,
    spine.account_month,
    spine.observation_sources,
    coalesce(movement_rollup.billing_event_count, 0) as billing_event_count,
    coalesce(movement_rollup.opening_arr_movement, 0) as opening_arr_movement,
    coalesce(movement_rollup.new_arr_movement, 0) as new_arr_movement,
    coalesce(movement_rollup.expansion_arr_movement, 0) as expansion_arr_movement,
    coalesce(movement_rollup.contraction_arr_movement, 0) as contraction_arr_movement,
    coalesce(movement_rollup.churned_arr_movement, 0) as churned_arr_movement,
    coalesce(movement_rollup.manual_adjustment_amount, 0) as manual_adjustment_amount,
    coalesce(movement_rollup.supported_revenue_movement_amount, 0)
        as supported_revenue_movement_amount,
    coalesce(movement_rollup.has_late_arrival, false) as has_late_arrival,
    coalesce(movement_rollup.has_orphaned_billing_reference, false)
        as has_orphaned_billing_reference,
    coalesce(movement_rollup.has_invalid_negative_arr_movement, false)
        as has_invalid_negative_arr_movement,
    coalesce(movement_rollup.has_injected_quality_issue, false) as has_injected_quality_issue,
    false as is_kpi_eligible,
    case
        when coalesce(movement_rollup.has_late_arrival, false)
            or coalesce(movement_rollup.has_orphaned_billing_reference, false)
            or coalesce(movement_rollup.has_invalid_negative_arr_movement, false)
            or coalesce(movement_rollup.has_injected_quality_issue, false)
            then 'exception_review_required'
        else 'preliminary_not_approved_for_management_reporting'
    end as quality_status,
    'trusted KPI reporting is blocked until formal data-quality checks are complete'
        as kpi_block_reason
from spine
left join movement_rollup
    on spine.account_id = movement_rollup.account_id
    and spine.account_month = movement_rollup.account_month
