with contracts as (
    select * from {{ ref('int_contract_timeline') }}
),

accounts as (
    select * from {{ ref('stg_accounts') }}
),

billing as (
    select * from {{ ref('stg_billing_events') }}
),

incident_registry as (
    select
        incident_id,
        scenario_name,
        affected_record_identifier,
        expected_detection_method
    from {{ source('raw', 'incident_registry') }}
),

duplicate_active_contracts as (
    select distinct contracts.*
    from contracts
    where contracts.contract_status = 'active'
        and exists (
            select 1
            from contracts as other_contract
            where other_contract.account_id = contracts.account_id
                and other_contract.source_row_identifier <> contracts.source_row_identifier
                and other_contract.contract_status = 'active'
                and contracts.contract_start_date <= other_contract.contract_end_date
                and other_contract.contract_start_date <= contracts.contract_end_date
        )
),

crm_billing_disagreements as (
    select distinct contracts.*
    from contracts
    inner join accounts
        on contracts.account_id = accounts.account_id
    left join billing
        on contracts.contract_id = billing.contract_id
    where accounts.crm_renewal_status = 'renewed'
        and (
            contracts.contract_status = 'cancelled'
            or billing.billing_status = 'cancelled'
        )
),

candidate_exceptions as (
    select
        'DQ_CONTRACT_DUPLICATE_ACTIVE' as rule_id,
        'critical' as severity,
        'contracts' as source_domain,
        contract_id as affected_record_identifier,
        account_id,
        contract_start_date as relevant_date,
        cast(date_trunc('month', contract_start_date) as date) as account_month,
        'Active contract overlaps another active contract for the same account.' as explanation,
        'duplicate_active_contract' as scenario_name
    from duplicate_active_contracts

    union all

    select
        'DQ_CONTRACT_OVERLAPPING_PERIOD' as rule_id,
        'critical' as severity,
        'contracts' as source_domain,
        contract_id as affected_record_identifier,
        account_id,
        contract_start_date as relevant_date,
        cast(date_trunc('month', contract_start_date) as date) as account_month,
        'Contract period overlaps another contract period for the same account.' as explanation,
        'overlapping_contract_period' as scenario_name
    from contracts
    where has_overlapping_contract_period

    union all

    select
        'DQ_CONTRACT_ACTIVE_AFTER_END' as rule_id,
        'critical' as severity,
        'contracts' as source_domain,
        contract_id as affected_record_identifier,
        account_id,
        contract_end_date as relevant_date,
        cast(date_trunc('month', contract_end_date) as date) as account_month,
        'Contract is marked active after its observed end date.' as explanation,
        'active_contract_after_end_date' as scenario_name
    from contracts
    where has_active_status_after_observed_end

    union all

    select
        'DQ_CONTRACT_MISSING_RENEWAL_DATE' as rule_id,
        'warning' as severity,
        'contracts' as source_domain,
        contract_id as affected_record_identifier,
        account_id,
        contract_end_date as relevant_date,
        cast(date_trunc('month', contract_end_date) as date) as account_month,
        'Contract is missing a renewal date.' as explanation,
        'missing_renewal_date' as scenario_name
    from contracts
    where has_missing_renewal_date

    union all

    select
        'DQ_CONTRACT_CRM_BILLING_STATUS_DISAGREEMENT' as rule_id,
        'critical' as severity,
        'accounts,contracts' as source_domain,
        account_id || '|' || contract_id as affected_record_identifier,
        account_id,
        contract_end_date as relevant_date,
        cast(date_trunc('month', contract_end_date) as date) as account_month,
        'CRM renewal status indicates renewal while contract or billing status indicates cancellation.'
            as explanation,
        'crm_renewal_status_disagrees_with_billing_status' as scenario_name
    from crm_billing_disagreements
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
                candidate_exceptions.affected_record_identifier
            ) > 0
            or instr(
                incident_registry.affected_record_identifier,
                candidate_exceptions.account_id
            ) > 0
        )
)

select * from with_incident
