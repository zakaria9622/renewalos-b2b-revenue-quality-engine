with accounts as (
    select * from {{ ref('stg_accounts') }}
),

usage_events as (
    select * from {{ ref('stg_usage_events') }}
),

cs_interactions as (
    select * from {{ ref('stg_cs_interactions') }}
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
        'DQ_IDENTIFIER_INCONSISTENT_ACCOUNT_ID' as rule_id,
        'critical' as severity,
        'usage_events' as source_domain,
        usage_events.usage_event_id as affected_record_identifier,
        usage_events.account_id,
        usage_events.activity_month as relevant_date,
        cast(date_trunc('month', usage_events.activity_month) as date) as account_month,
        'Usage event account ID is not present in the CRM account source.' as explanation,
        'inconsistent_account_identifier' as scenario_name
    from usage_events
    left join accounts
        on usage_events.account_id = accounts.account_id
    where accounts.account_id is null

    union all

    select
        'DQ_IDENTIFIER_ACCOUNT_MISSING_SEGMENT_OR_OWNER' as rule_id,
        'warning' as severity,
        'accounts' as source_domain,
        account_id as affected_record_identifier,
        account_id,
        created_date as relevant_date,
        cast(date_trunc('month', created_date) as date) as account_month,
        'Active CRM account is missing segment or owner fields.' as explanation,
        'account_missing_segment_or_owner' as scenario_name
    from accounts
    where lifecycle_status = 'active'
        and has_missing_segment_or_owner

    union all

    select
        'DQ_IDENTIFIER_CS_WRONG_ACCOUNT' as rule_id,
        'warning' as severity,
        'cs_interactions' as source_domain,
        cs_interactions.interaction_id as affected_record_identifier,
        cs_interactions.account_id,
        cs_interactions.interaction_date as relevant_date,
        cast(date_trunc('month', cs_interactions.interaction_date) as date) as account_month,
        'Customer Success interaction account ID is not present in the CRM account source.'
            as explanation,
        'cs_interaction_logged_to_wrong_account' as scenario_name
    from cs_interactions
    left join accounts
        on cs_interactions.account_id = accounts.account_id
    where accounts.account_id is null
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
        and (
            incident_registry.affected_record_identifier
            = candidate_exceptions.affected_record_identifier
            or instr(
                incident_registry.affected_record_identifier,
                candidate_exceptions.account_id
            ) > 0
        )
)

select * from with_incident
