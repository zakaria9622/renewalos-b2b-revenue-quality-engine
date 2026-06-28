with observed_months as (
    select account_id, cast(date_trunc('month', created_date) as date) as account_month, 'accounts_created' as observation_source
    from {{ ref('stg_accounts') }}
    where account_id is not null and created_date is not null

    union all

    select account_id, cast(date_trunc('month', contract_start_date) as date) as account_month, 'contract_start' as observation_source
    from {{ ref('stg_contracts') }}
    where account_id is not null and contract_start_date is not null

    union all

    select account_id, cast(date_trunc('month', contract_end_date) as date) as account_month, 'contract_end' as observation_source
    from {{ ref('stg_contracts') }}
    where account_id is not null and contract_end_date is not null

    union all

    select account_id, cast(date_trunc('month', effective_date) as date) as account_month, 'billing_effective' as observation_source
    from {{ ref('stg_billing_events') }}
    where account_id is not null and effective_date is not null

    union all

    select account_id, cast(date_trunc('month', activity_month) as date) as account_month, 'usage_activity' as observation_source
    from {{ ref('stg_usage_events') }}
    where account_id is not null and activity_month is not null

    union all

    select account_id, cast(date_trunc('month', created_at) as date) as account_month, 'support_ticket' as observation_source
    from {{ ref('stg_support_tickets') }}
    where account_id is not null and created_at is not null

    union all

    select account_id, cast(date_trunc('month', interaction_date) as date) as account_month, 'cs_interaction' as observation_source
    from {{ ref('stg_cs_interactions') }}
    where account_id is not null and interaction_date is not null
)

select
    account_id,
    account_month,
    max(case when observation_source = 'accounts_created' then 1 else 0 end) = 1
        as observed_in_accounts,
    max(case when observation_source in ('contract_start', 'contract_end') then 1 else 0 end) = 1
        as observed_in_contracts,
    max(case when observation_source = 'billing_effective' then 1 else 0 end) = 1
        as observed_in_billing,
    max(case when observation_source = 'usage_activity' then 1 else 0 end) = 1
        as observed_in_usage,
    max(case when observation_source = 'support_ticket' then 1 else 0 end) = 1
        as observed_in_support,
    max(case when observation_source = 'cs_interaction' then 1 else 0 end) = 1
        as observed_in_cs,
    string_agg(distinct observation_source, ', ' order by observation_source) as observation_sources
from observed_months
group by account_id, account_month
