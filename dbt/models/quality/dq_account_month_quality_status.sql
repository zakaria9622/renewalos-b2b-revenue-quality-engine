with spine as (
    select * from {{ ref('int_account_month_spine') }}
),

detected_exceptions as (
    select * from {{ ref('dq_contract_exceptions') }}
    union all
    select * from {{ ref('dq_billing_exceptions') }}
    union all
    select * from {{ ref('dq_usage_exceptions') }}
    union all
    select * from {{ ref('dq_support_exceptions') }}
    union all
    select * from {{ ref('dq_identifier_exceptions') }}
),

exception_rollup as (
    select
        account_id,
        account_month,
        count(*) as exception_count,
        sum(case when severity = 'critical' then 1 else 0 end) as critical_exception_count,
        sum(case when severity = 'warning' then 1 else 0 end) as warning_exception_count,
        string_agg(distinct rule_id, ', ' order by rule_id) as detected_rule_ids,
        string_agg(distinct source_domain, ', ' order by source_domain) as source_domains,
        string_agg(distinct incident_id, ', ' order by incident_id) as linked_incident_ids
    from detected_exceptions
    where account_id is not null
        and account_month is not null
    group by account_id, account_month
)

select
    spine.account_id,
    spine.account_month,
    spine.observation_sources,
    coalesce(exception_rollup.exception_count, 0) as exception_count,
    coalesce(exception_rollup.critical_exception_count, 0) as critical_exception_count,
    coalesce(exception_rollup.warning_exception_count, 0) as warning_exception_count,
    exception_rollup.detected_rule_ids,
    exception_rollup.source_domains,
    exception_rollup.linked_incident_ids,
    case
        when coalesce(exception_rollup.critical_exception_count, 0) > 0
            then 'blocked'
        when coalesce(exception_rollup.warning_exception_count, 0) > 0
            then 'warning'
        when spine.observed_in_contracts or spine.observed_in_billing
            then 'eligible_with_caveat'
        else 'no_observed_issue'
    end as quality_status,
    case
        when coalesce(exception_rollup.critical_exception_count, 0) > 0
            then 'Critical source exception blocks management KPI use for this account-month.'
        when coalesce(exception_rollup.warning_exception_count, 0) > 0
            then 'Warning source exception requires caveated review before KPI use.'
        when spine.observed_in_contracts or spine.observed_in_billing
            then 'No mapped exception was observed, but output remains synthetic and preliminary.'
        else 'No mapped exception was observed for this account-month.'
    end as quality_status_reason
from spine
left join exception_rollup
    on spine.account_id = exception_rollup.account_id
    and spine.account_month = exception_rollup.account_month
