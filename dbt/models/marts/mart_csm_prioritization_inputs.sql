with candidates as (
    select * from {{ ref('mart_csm_priority_candidates') }}
),

scored as (
    select
        *,
        case health_band
            when 'critical' then 1.00
            when 'at_risk' then 0.75
            when 'monitor' then 0.35
            when 'stable' then 0.10
            else 0.00
        end as health_severity_factor,
        case renewal_urgency
            when 'high' then 1.00
            when 'unknown_missing_renewal_date' then 1.00
            when 'medium' then 0.75
            when 'low' then 0.45
            else 0.20
        end as renewal_urgency_factor,
        case
            when health_band in ('critical', 'at_risk')
                and renewal_urgency in ('high', 'medium', 'unknown_missing_renewal_date')
                then 'tier_1'
            when health_band in ('critical', 'at_risk', 'monitor')
                or renewal_urgency in ('high', 'medium', 'low', 'unknown_missing_renewal_date')
                then 'tier_2'
            else 'tier_3'
        end as priority_tier
    from candidates
    where is_eligible_candidate
)

select
    account_id,
    account_month,
    assessment_status,
    quality_status,
    health_score,
    health_band,
    revenue_exposure_amount,
    renewal_urgency,
    usage_concern,
    support_concern,
    customer_success_engagement_concern,
    revenue_or_billing_status_concern,
    explanation_drivers,
    priority_tier,
    health_severity_factor,
    renewal_urgency_factor,
    revenue_exposure_amount
        * health_severity_factor
        * renewal_urgency_factor as estimated_account_value_at_risk,
    case priority_tier
        when 'tier_1' then 4.0
        when 'tier_2' then 3.0
        else 1.5
    end as estimated_effort_hours,
    case priority_tier
        when 'tier_1' then 0.18
        when 'tier_2' then 0.10
        else 0.04
    end as assumed_intervention_effectiveness,
    revenue_exposure_amount
        * health_severity_factor
        * renewal_urgency_factor
        * case priority_tier
            when 'tier_1' then 0.18
            when 'tier_2' then 0.10
            else 0.04
        end as expected_protected_value,
    (
        revenue_exposure_amount
        * health_severity_factor
        * renewal_urgency_factor
        * case priority_tier
            when 'tier_1' then 0.18
            when 'tier_2' then 0.10
            else 0.04
        end
    ) / nullif(
        case priority_tier
            when 'tier_1' then 4.0
            when 'tier_2' then 3.0
            else 1.5
        end,
        0
    ) as priority_score,
    'synthetic_csm_capacity_v1' as scenario_id,
    'simulated_prioritization_assumptions_v1' as assumption_version,
    'simulated_scenario_assumption_not_observed_effect' as assumption_label,
    false as is_observed_intervention_outcome
from scored
