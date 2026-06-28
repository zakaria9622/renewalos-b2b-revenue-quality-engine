with spine as (
    select * from {{ ref('int_account_month_spine') }}
),

accounts as (
    select * from {{ ref('stg_accounts') }}
),

quality_status as (
    select * from {{ ref('dq_account_month_quality_status') }}
),

usage_with_history as (
    select
        usage_events.*,
        lag(active_users) over (
            partition by account_id
            order by activity_month
        ) as previous_active_users,
        lag(events_count) over (
            partition by account_id
            order by activity_month
        ) as previous_events_count
    from {{ ref('stg_usage_events') }} as usage_events
),

support_rollup as (
    select
        spine.account_id,
        spine.account_month,
        count(support_tickets.ticket_id) as support_ticket_count_90d,
        count(*) filter (where support_tickets.severity = 'high') as high_support_ticket_count_90d,
        count(*) filter (
            where support_tickets.ticket_status in ('open', 'pending')
        ) as open_support_ticket_count_90d,
        max(support_tickets.created_at) as latest_support_ticket_date
    from spine
    left join {{ ref('stg_support_tickets') }} as support_tickets
        on spine.account_id = support_tickets.account_id
        and support_tickets.created_at >= spine.account_month - interval '90 days'
        and support_tickets.created_at < spine.account_month + interval '1 month'
    group by spine.account_id, spine.account_month
),

cs_rollup as (
    select
        spine.account_id,
        spine.account_month,
        count(cs_interactions.interaction_id) as cs_interaction_count_90d,
        count(*) filter (where cs_interactions.sentiment = 'concerned')
            as concerned_cs_interaction_count_90d,
        max(cs_interactions.interaction_date) as latest_cs_interaction_date,
        string_agg(distinct cs_interactions.sentiment, ', ' order by cs_interactions.sentiment)
            as cs_sentiments_90d
    from spine
    left join {{ ref('stg_cs_interactions') }} as cs_interactions
        on spine.account_id = cs_interactions.account_id
        and cs_interactions.interaction_date >= spine.account_month - interval '90 days'
        and cs_interactions.interaction_date < spine.account_month + interval '1 month'
    group by spine.account_id, spine.account_month
),

contract_exposure as (
    select
        spine.account_id,
        spine.account_month,
        count(contract_timeline.contract_id) as active_contract_record_count,
        sum(contract_timeline.arr_amount) as active_contract_arr_amount,
        max(case when contract_timeline.contract_status = 'active' then 1 else 0 end) = 1
            as has_active_contract,
        max(case when contract_timeline.contract_status = 'cancelled' then 1 else 0 end) = 1
            as has_cancelled_contract_in_month
    from spine
    left join {{ ref('int_contract_timeline') }} as contract_timeline
        on spine.account_id = contract_timeline.account_id
        and spine.account_month between
            cast(date_trunc('month', contract_timeline.contract_start_date) as date)
            and cast(date_trunc('month', contract_timeline.contract_end_date) as date)
    group by spine.account_id, spine.account_month
),

joined as (
    select
        spine.account_id,
        spine.account_month,
        spine.observation_sources,
        accounts.lifecycle_status,
        accounts.crm_renewal_status,
        accounts.segment,
        accounts.owner_id,
        quality_status.quality_status,
        quality_status.quality_status_reason,
        quality_status.critical_exception_count,
        quality_status.warning_exception_count,
        usage_with_history.usage_event_id is not null as has_current_usage_record,
        usage_with_history.usage_status,
        usage_with_history.active_users,
        usage_with_history.events_count,
        usage_with_history.previous_active_users,
        usage_with_history.previous_events_count,
        case
            when usage_with_history.previous_active_users is null
                or usage_with_history.previous_active_users = 0
                then null
            else (
                usage_with_history.active_users - usage_with_history.previous_active_users
            )::double / usage_with_history.previous_active_users
        end as active_user_change_pct,
        coalesce(support_rollup.support_ticket_count_90d, 0) as support_ticket_count_90d,
        coalesce(support_rollup.high_support_ticket_count_90d, 0)
            as high_support_ticket_count_90d,
        coalesce(support_rollup.open_support_ticket_count_90d, 0)
            as open_support_ticket_count_90d,
        support_rollup.latest_support_ticket_date,
        case
            when support_rollup.latest_support_ticket_date is null
                then null
            else date_diff(
                'day',
                support_rollup.latest_support_ticket_date,
                spine.account_month + interval '1 month' - interval '1 day'
            )
        end as days_since_last_support_ticket,
        coalesce(cs_rollup.cs_interaction_count_90d, 0) as cs_interaction_count_90d,
        coalesce(cs_rollup.concerned_cs_interaction_count_90d, 0)
            as concerned_cs_interaction_count_90d,
        cs_rollup.latest_cs_interaction_date,
        case
            when cs_rollup.latest_cs_interaction_date is null
                then null
            else date_diff(
                'day',
                cs_rollup.latest_cs_interaction_date,
                spine.account_month + interval '1 month' - interval '1 day'
            )
        end as days_since_last_cs_interaction,
        cs_rollup.cs_sentiments_90d,
        coalesce(contract_exposure.active_contract_record_count, 0)
            as active_contract_record_count,
        coalesce(contract_exposure.active_contract_arr_amount, 0) as revenue_exposure_amount,
        coalesce(contract_exposure.has_active_contract, false) as has_active_contract,
        coalesce(contract_exposure.has_cancelled_contract_in_month, false)
            as has_cancelled_contract_in_month
    from spine
    left join accounts
        on spine.account_id = accounts.account_id
    left join quality_status
        on spine.account_id = quality_status.account_id
        and spine.account_month = quality_status.account_month
    left join usage_with_history
        on spine.account_id = usage_with_history.account_id
        and spine.account_month = usage_with_history.activity_month
    left join support_rollup
        on spine.account_id = support_rollup.account_id
        and spine.account_month = support_rollup.account_month
    left join cs_rollup
        on spine.account_id = cs_rollup.account_id
        and spine.account_month = cs_rollup.account_month
    left join contract_exposure
        on spine.account_id = contract_exposure.account_id
        and spine.account_month = contract_exposure.account_month
)

select
    *,
    case
        when not has_current_usage_record
            then 'not_observed'
        when usage_status = 'inactive'
            or active_users = 0
            or (active_user_change_pct <= -0.50 and previous_active_users >= 5)
            then 'high'
        when active_users <= 2
            or active_user_change_pct <= -0.25
            then 'medium'
        else 'none'
    end as usage_concern,
    case
        when high_support_ticket_count_90d > 0
            or open_support_ticket_count_90d >= 3
            or support_ticket_count_90d >= 4
            then 'high'
        when open_support_ticket_count_90d >= 1
            or support_ticket_count_90d >= 2
            then 'medium'
        else 'none'
    end as support_concern,
    case
        when concerned_cs_interaction_count_90d > 0
            then 'high'
        when cs_interaction_count_90d = 0
            then 'medium'
        else 'none'
    end as customer_success_engagement_concern
from joined
