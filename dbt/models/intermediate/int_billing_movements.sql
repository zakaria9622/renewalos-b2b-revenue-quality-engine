with billing as (
    select * from {{ ref('stg_billing_events') }}
),

accounts as (
    select account_id from {{ ref('stg_accounts') }}
),

contracts as (
    select contract_id from {{ ref('stg_contracts') }}
)

select
    billing.*,
    cast(date_trunc('month', billing.effective_date) as date) as movement_month,
    case billing.event_type
        when 'opening_arr' then 'opening_arr'
        when 'new_arr' then 'new_arr'
        when 'expansion_arr' then 'expansion_arr'
        when 'contraction_arr' then 'contraction_arr'
        when 'churned_arr' then 'churned_arr'
        when 'renewal' then 'renewal_marker'
        when 'manual_adjustment' then 'manual_adjustment_unmapped'
        else 'unmapped_event_type'
    end as movement_category,
    billing.event_type in (
        'opening_arr',
        'new_arr',
        'expansion_arr',
        'contraction_arr',
        'churned_arr'
    ) as is_supported_revenue_movement,
    billing.event_type = 'manual_adjustment' as is_manual_adjustment,
    accounts.account_id is null as is_orphaned_account_id,
    contracts.contract_id is null as is_orphaned_contract_id,
    (
        billing.has_late_arrival
        or billing.has_invalid_negative_arr_movement
        or billing.has_injected_quality_issue
        or accounts.account_id is null
        or contracts.contract_id is null
    ) as is_exception_ready
from billing
left join accounts
    on billing.account_id = accounts.account_id
left join contracts
    on billing.contract_id = contracts.contract_id
