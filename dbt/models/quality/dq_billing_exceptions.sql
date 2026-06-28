with billing as (
    select * from {{ ref('int_billing_movements') }}
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
        'DQ_BILLING_LATE_ARRIVAL' as rule_id,
        'warning' as severity,
        'billing_events' as source_domain,
        billing_event_id as affected_record_identifier,
        account_id,
        effective_date as relevant_date,
        movement_month as account_month,
        'Billing event was received more than 30 days after its effective date.' as explanation,
        'late_arriving_billing_event' as scenario_name
    from billing
    where has_late_arrival

    union all

    select
        'DQ_BILLING_ORPHANED_EVENT' as rule_id,
        'critical' as severity,
        'billing_events' as source_domain,
        billing_event_id as affected_record_identifier,
        account_id,
        effective_date as relevant_date,
        movement_month as account_month,
        'Billing event references an account or contract not present in the loaded source records.'
            as explanation,
        'orphaned_billing_event' as scenario_name
    from billing
    where is_orphaned_account_id or is_orphaned_contract_id

    union all

    select
        'DQ_BILLING_INVALID_NEGATIVE_ARR' as rule_id,
        'critical' as severity,
        'billing_events' as source_domain,
        billing_event_id as affected_record_identifier,
        account_id,
        effective_date as relevant_date,
        movement_month as account_month,
        'Negative ARR movement is not tied to an approved contraction or churn event type.'
            as explanation,
        'invalid_negative_arr_movement' as scenario_name
    from billing
    where has_invalid_negative_arr_movement
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
