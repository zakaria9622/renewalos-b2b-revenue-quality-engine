with duplicate_candidates as (
    select
        account_id,
        account_month,
        count(*) as candidate_count
    from {{ ref('mart_csm_prioritization_inputs') }}
    group by account_id, account_month
    having count(*) > 1
),

invalid_inputs as (
    select
        account_id,
        account_month,
        1 as candidate_count
    from {{ ref('mart_csm_prioritization_inputs') }}
    where estimated_account_value_at_risk is null
        or estimated_effort_hours is null
        or assumed_intervention_effectiveness is null
        or expected_protected_value is null
        or priority_score is null
        or estimated_effort_hours <= 0
        or assumed_intervention_effectiveness <= 0
        or scenario_id <> 'synthetic_csm_capacity_v1'
        or assumption_label <> 'simulated_scenario_assumption_not_observed_effect'
)

select * from duplicate_candidates
union all
select * from invalid_inputs
