with usage_events as (
    select * from {{ ref('stg_usage_events') }}
),

accounts as (
    select * from {{ ref('stg_accounts') }}
),

incident_registry as (
    select
        incident_id,
        scenario_name,
        affected_record_identifier,
        expected_detection_method
    from {{ source('raw', 'incident_registry') }}
),

candidate_exceptions as (
    select
        'DQ_USAGE_CHURNED_ACCOUNT_ACTIVE' as rule_id,
        'warning' as severity,
        'usage_events' as source_domain,
        usage_events.usage_event_id as affected_record_identifier,
        usage_events.account_id,
        usage_events.activity_month as relevant_date,
        cast(date_trunc('month', usage_events.activity_month) as date) as account_month,
        'Account is marked churned but has active usage after the churn date.' as explanation,
        'churned_account_with_active_usage' as scenario_name
    from usage_events
    inner join accounts
        on usage_events.account_id = accounts.account_id
    where accounts.lifecycle_status = 'churned'
        and accounts.churn_date is not null
        and usage_events.activity_month > cast(date_trunc('month', accounts.churn_date) as date)
        and usage_events.active_users > 0

    union all

    select
        'DQ_USAGE_STALE_EXTRACT' as rule_id,
        'warning' as severity,
        'usage_events' as source_domain,
        usage_event_id as affected_record_identifier,
        account_id,
        activity_month as relevant_date,
        cast(date_trunc('month', activity_month) as date) as account_month,
        'Usage extract date is older than the activity month.' as explanation,
        'stale_usage_extract' as scenario_name
    from usage_events
    where has_stale_extract_date
),

with_incident as (
    select
        candidate_exceptions.rule_id,
        candidate_exceptions.severity,
        candidate_exceptions.source_domain,
        candidate_exceptions.affected_record_identifier,
        candidate_exceptions.account_id,
        candidate_exceptions.relevant_date,
        candidate_exceptions.account_month,
        candidate_exceptions.explanation,
        incident_registry.incident_id,
        candidate_exceptions.scenario_name,
        incident_registry.expected_detection_method
    from candidate_exceptions
    left join incident_registry
        on incident_registry.scenario_name = candidate_exceptions.scenario_name
        and incident_registry.affected_record_identifier
            = candidate_exceptions.affected_record_identifier
)

select * from with_incident
