with support_tickets as (
    select * from {{ ref('stg_support_tickets') }}
),

incident_registry as (
    select
        incident_id,
        scenario_name,
        affected_record_identifier,
        expected_detection_method
    from {{ source('raw', 'incident_registry') }}
),

duplicate_groups as (
    select
        account_id,
        created_at,
        severity,
        category
    from support_tickets
    where account_id is not null
        and created_at is not null
        and severity is not null
        and category is not null
    group by account_id, created_at, severity, category
    having count(*) > 1
),

candidate_exceptions as (
    select
        'DQ_SUPPORT_DUPLICATE_TICKET' as rule_id,
        'warning' as severity,
        'support_tickets' as source_domain,
        support_tickets.ticket_id as affected_record_identifier,
        support_tickets.account_id,
        support_tickets.created_at as relevant_date,
        cast(date_trunc('month', support_tickets.created_at) as date) as account_month,
        'Support ticket repeats account, created date, severity, and category attributes.'
            as explanation,
        'duplicate_support_ticket' as scenario_name
    from support_tickets
    inner join duplicate_groups
        on support_tickets.account_id = duplicate_groups.account_id
        and support_tickets.created_at = duplicate_groups.created_at
        and support_tickets.severity = duplicate_groups.severity
        and support_tickets.category = duplicate_groups.category
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
