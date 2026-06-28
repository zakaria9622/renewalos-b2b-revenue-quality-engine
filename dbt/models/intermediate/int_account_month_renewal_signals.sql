with spine as (
    select * from {{ ref('int_account_month_spine') }}
),

accounts as (
    select * from {{ ref('stg_accounts') }}
),

contracts as (
    select * from {{ ref('int_contract_timeline') }}
),

billing_movements as (
    select * from {{ ref('int_billing_movements') }}
),

reconciliation as (
    select * from {{ ref('mart_revenue_reconciliation_diagnostics') }}
),

contract_exception_flags as (
    select
        account_id,
        account_month,
        max(case when scenario_name = 'crm_renewal_status_disagrees_with_billing_status' then 1 else 0 end) = 1
            as has_renewal_status_disagreement
    from {{ ref('dq_contract_exceptions') }}
    group by account_id, account_month
),

contract_rollup as (
    select
        spine.account_id,
        spine.account_month,
        min(contracts.renewal_date) filter (
            where contracts.renewal_date >= spine.account_month
        ) as nearest_renewal_date,
        min(contracts.contract_end_date) filter (
            where contracts.contract_end_date >= spine.account_month
        ) as nearest_contract_end_date,
        max(case when contracts.has_missing_renewal_date then 1 else 0 end) = 1
            as has_missing_renewal_date,
        max(case when contracts.has_active_status_after_observed_end then 1 else 0 end) = 1
            as has_active_contract_after_end_date,
        max(case when contracts.has_overlapping_contract_period then 1 else 0 end) = 1
            as has_overlapping_contract_period,
        max(case when contracts.contract_status = 'active' then 1 else 0 end) = 1
            as has_active_contract_in_month,
        max(case when contracts.contract_status = 'cancelled' then 1 else 0 end) = 1
            as has_cancelled_contract_in_month
    from spine
    left join contracts
        on spine.account_id = contracts.account_id
        and spine.account_month between
            cast(date_trunc('month', contracts.contract_start_date) as date)
            and cast(date_trunc('month', contracts.contract_end_date) as date)
    group by spine.account_id, spine.account_month
),

billing_rollup as (
    select
        account_id,
        movement_month as account_month,
        count(*) filter (where billing_status = 'cancelled') as cancelled_billing_event_count,
        max(case when has_late_arrival then 1 else 0 end) = 1 as has_late_billing_event,
        max(case when is_orphaned_account_id or is_orphaned_contract_id then 1 else 0 end) = 1
            as has_orphaned_billing_reference,
        max(case when has_invalid_negative_arr_movement then 1 else 0 end) = 1
            as has_invalid_negative_arr_movement
    from billing_movements
    where movement_month is not null
    group by account_id, movement_month
),

joined as (
    select
        spine.account_id,
        spine.account_month,
        accounts.crm_renewal_status,
        accounts.lifecycle_status,
        contract_rollup.nearest_renewal_date,
        contract_rollup.nearest_contract_end_date,
        case
            when contract_rollup.nearest_renewal_date is null
                then null
            else date_diff('day', spine.account_month, contract_rollup.nearest_renewal_date)
        end as days_to_renewal,
        case
            when contract_rollup.nearest_contract_end_date is null
                then null
            else date_diff('day', spine.account_month, contract_rollup.nearest_contract_end_date)
        end as days_to_contract_end,
        coalesce(contract_rollup.has_missing_renewal_date, false) as has_missing_renewal_date,
        coalesce(contract_rollup.has_active_contract_after_end_date, false)
            as has_active_contract_after_end_date,
        coalesce(contract_rollup.has_overlapping_contract_period, false)
            as has_overlapping_contract_period,
        coalesce(contract_rollup.has_active_contract_in_month, false) as has_active_contract_in_month,
        coalesce(contract_rollup.has_cancelled_contract_in_month, false)
            as has_cancelled_contract_in_month,
        coalesce(billing_rollup.cancelled_billing_event_count, 0) as cancelled_billing_event_count,
        coalesce(billing_rollup.has_late_billing_event, false) as has_late_billing_event,
        coalesce(billing_rollup.has_orphaned_billing_reference, false)
            as has_orphaned_billing_reference,
        coalesce(billing_rollup.has_invalid_negative_arr_movement, false)
            as has_invalid_negative_arr_movement,
        coalesce(contract_exception_flags.has_renewal_status_disagreement, false)
            as has_renewal_status_disagreement,
        reconciliation.reconciliation_status,
        reconciliation.reconciliation_gap_amount,
        reconciliation.observed_closing_balance_amount
    from spine
    left join accounts
        on spine.account_id = accounts.account_id
    left join contract_rollup
        on spine.account_id = contract_rollup.account_id
        and spine.account_month = contract_rollup.account_month
    left join billing_rollup
        on spine.account_id = billing_rollup.account_id
        and spine.account_month = billing_rollup.account_month
    left join contract_exception_flags
        on spine.account_id = contract_exception_flags.account_id
        and spine.account_month = contract_exception_flags.account_month
    left join reconciliation
        on spine.account_id = reconciliation.account_id
        and spine.account_month = reconciliation.account_month
),

with_windows as (
    select
        *,
        least(
            coalesce(days_to_renewal, 99999),
            coalesce(days_to_contract_end, 99999)
        ) as nearest_renewal_or_end_days
    from joined
)

select
    *,
    case
        when has_missing_renewal_date
            then 'unknown_missing_renewal_date'
        when not has_active_contract_in_month
            then 'not_observed'
        when nearest_renewal_or_end_days <= 0
            then 'past_due_or_current'
        when nearest_renewal_or_end_days <= 30
            then 'high'
        when nearest_renewal_or_end_days <= 90
            then 'medium'
        when nearest_renewal_or_end_days <= 180
            then 'low'
        else 'none'
    end as renewal_urgency,
    (
        has_active_contract_after_end_date
        or has_overlapping_contract_period
    ) as has_active_contract_contradiction,
    case
        when has_orphaned_billing_reference
            or has_invalid_negative_arr_movement
            then 'high'
        when reconciliation_status = 'gap_observed'
            or has_late_billing_event
            or cancelled_billing_event_count > 0
            then 'medium'
        else 'none'
    end as revenue_or_billing_status_concern
from with_windows
