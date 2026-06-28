with incident_registry as (
    select
        incident_id,
        scenario_name,
        affected_domain,
        affected_record_identifier,
        expected_detection_method,
        expected_business_impact,
        severity
    from {{ source('raw', 'incident_registry') }}
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

detected_by_incident as (
    select
        incident_id,
        string_agg(distinct rule_id, ', ' order by rule_id) as detected_rule_id
    from detected_exceptions
    where incident_id is not null
    group by incident_id
),

detected_by_scenario as (
    select
        scenario_name,
        string_agg(distinct rule_id, ', ' order by rule_id) as detected_rule_id
    from detected_exceptions
    group by scenario_name
)

select
    incident_registry.incident_id,
    incident_registry.scenario_name,
    incident_registry.affected_domain,
    incident_registry.affected_record_identifier,
    incident_registry.expected_detection_method,
    incident_registry.expected_business_impact,
    incident_registry.severity as registered_severity,
    coalesce(
        detected_by_incident.detected_rule_id,
        detected_by_scenario.detected_rule_id
    ) as detected_rule_id,
    case
        when coalesce(
            detected_by_incident.detected_rule_id,
            detected_by_scenario.detected_rule_id
        ) is not null
            then 'detected'
        else 'not_detected'
    end as detection_status,
    case
        when coalesce(
            detected_by_incident.detected_rule_id,
            detected_by_scenario.detected_rule_id
        ) is not null
            then null
        else 'No matching quality exception was produced for this registered incident.'
    end as unmatched_explanation
from incident_registry
left join detected_by_incident
    on incident_registry.incident_id = detected_by_incident.incident_id
left join detected_by_scenario
    on incident_registry.scenario_name = detected_by_scenario.scenario_name
