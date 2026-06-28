with health as (
    select * from {{ ref('mart_account_health') }}
),

explanation_rollup as (
    select
        account_id,
        account_month,
        string_agg(
            component_name || ':' || severity || ':' || plain_language_explanation,
            ' | '
            order by
                case severity
                    when 'high' then 1
                    when 'medium' then 2
                    when 'low' then 3
                    else 4
                end,
                component_name
        ) as explanation_drivers,
        string_agg(
            component_name || ':' || source_lineage_reference,
            ', '
            order by component_name
        ) as explanation_lineage_references
    from {{ ref('mart_account_health_explanations') }}
    where severity in ('high', 'medium')
        or component_name in ('renewal', 'revenue', 'usage', 'support', 'customer_success')
    group by account_id, account_month
)

select
    health.account_id,
    health.account_month,
    health.assessment_status,
    health.quality_status,
    health.health_score,
    health.health_band,
    health.revenue_component_score,
    health.renewal_component_score,
    health.usage_component_score,
    health.support_component_score,
    health.customer_success_component_score,
    health.revenue_exposure_amount,
    health.renewal_urgency,
    health.usage_concern,
    health.support_concern,
    health.customer_success_engagement_concern,
    health.revenue_or_billing_status_concern,
    health.reconciliation_status,
    health.reconciliation_gap_amount,
    health.days_to_renewal,
    health.days_to_contract_end,
    health.nearest_renewal_date,
    health.nearest_contract_end_date,
    health.explanation_summary,
    coalesce(
        explanation_rollup.explanation_drivers,
        health.explanation_summary
    ) as explanation_drivers,
    explanation_rollup.explanation_lineage_references,
    case
        when health.assessment_status in ('eligible', 'eligible_with_caveat')
            and health.health_score is not null
            and health.revenue_exposure_amount is not null
            and health.revenue_exposure_amount > 0
            then true
        else false
    end as is_eligible_candidate,
    case
        when health.assessment_status = 'blocked_due_to_data_quality'
            then 'blocked_due_to_data_quality'
        when health.assessment_status = 'not_assessable'
            then health.assessment_reason_category
        when health.health_score is null
            then 'missing_health_score'
        when health.revenue_exposure_amount is null
            or health.revenue_exposure_amount <= 0
            then 'missing_supported_revenue_exposure'
        else null
    end as exclusion_reason,
    'synthetic_csm_priority_candidate' as synthetic_data_label,
    false as is_automated_action
from health
left join explanation_rollup
    on health.account_id = explanation_rollup.account_id
    and health.account_month = explanation_rollup.account_month
