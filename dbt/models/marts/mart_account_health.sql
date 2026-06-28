with operational as (
    select * from {{ ref('int_account_month_operational_signals') }}
),

renewal as (
    select * from {{ ref('int_account_month_renewal_signals') }}
),

base as (
    select
        operational.account_id,
        operational.account_month,
        operational.quality_status,
        operational.quality_status_reason,
        operational.critical_exception_count,
        operational.warning_exception_count,
        operational.lifecycle_status,
        operational.crm_renewal_status,
        operational.has_current_usage_record,
        operational.usage_status,
        operational.active_users,
        operational.previous_active_users,
        operational.active_user_change_pct,
        operational.usage_concern,
        operational.support_ticket_count_90d,
        operational.high_support_ticket_count_90d,
        operational.open_support_ticket_count_90d,
        operational.days_since_last_support_ticket,
        operational.support_concern,
        operational.cs_interaction_count_90d,
        operational.concerned_cs_interaction_count_90d,
        operational.days_since_last_cs_interaction,
        operational.customer_success_engagement_concern,
        operational.active_contract_record_count,
        operational.revenue_exposure_amount,
        operational.has_active_contract,
        renewal.nearest_renewal_date,
        renewal.nearest_contract_end_date,
        renewal.days_to_renewal,
        renewal.days_to_contract_end,
        renewal.renewal_urgency,
        renewal.has_missing_renewal_date,
        renewal.has_active_contract_contradiction,
        renewal.has_renewal_status_disagreement,
        renewal.revenue_or_billing_status_concern,
        renewal.reconciliation_status,
        renewal.reconciliation_gap_amount,
        renewal.observed_closing_balance_amount,
        case
            when operational.quality_status = 'blocked'
                then 'blocked_due_to_data_quality'
            when not operational.has_current_usage_record
                or operational.active_contract_record_count = 0
                or renewal.observed_closing_balance_amount is null
                then 'not_assessable'
            when operational.quality_status = 'warning'
                or renewal.reconciliation_status = 'gap_observed'
                or renewal.revenue_or_billing_status_concern <> 'none'
                or renewal.has_renewal_status_disagreement
                or renewal.has_missing_renewal_date
                then 'eligible_with_caveat'
            else 'eligible'
        end as assessment_status,
        case
            when operational.quality_status = 'blocked'
                then 'critical_quality_exception'
            when not operational.has_current_usage_record
                then 'missing_current_usage_record'
            when operational.active_contract_record_count = 0
                then 'no_active_contract_exposure'
            when renewal.observed_closing_balance_amount is null
                then 'observed_revenue_balance_not_derivable'
            when operational.quality_status = 'warning'
                then 'warning_quality_exception'
            when renewal.reconciliation_status = 'gap_observed'
                then 'reconciliation_gap_caveat'
            when renewal.revenue_or_billing_status_concern <> 'none'
                then 'billing_or_revenue_caveat'
            when renewal.has_renewal_status_disagreement
                then 'renewal_status_disagreement_caveat'
            when renewal.has_missing_renewal_date
                then 'missing_renewal_date_caveat'
            else 'scored_without_observed_gate_exception'
        end as assessment_reason_category
    from operational
    left join renewal
        on operational.account_id = renewal.account_id
        and operational.account_month = renewal.account_month
),

component_scores as (
    select
        *,
        case
            when assessment_status in ('blocked_due_to_data_quality', 'not_assessable')
                then null
            when revenue_or_billing_status_concern = 'none'
                then 15
            else 8
        end as revenue_component_score,
        case
            when assessment_status in ('blocked_due_to_data_quality', 'not_assessable')
                then null
            when renewal_urgency in ('past_due_or_current', 'high', 'unknown_missing_renewal_date')
                then 5
            when renewal_urgency = 'medium'
                then 10
            when renewal_urgency = 'low'
                then 15
            else 20
        end as renewal_component_score,
        case
            when assessment_status in ('blocked_due_to_data_quality', 'not_assessable')
                then null
            when usage_concern = 'high'
                then 5
            when usage_concern = 'medium'
                then 15
            else 30
        end as usage_component_score,
        case
            when assessment_status in ('blocked_due_to_data_quality', 'not_assessable')
                then null
            when support_concern = 'high'
                then 5
            when support_concern = 'medium'
                then 12
            else 20
        end as support_component_score,
        case
            when assessment_status in ('blocked_due_to_data_quality', 'not_assessable')
                then null
            when customer_success_engagement_concern = 'high'
                then 3
            when customer_success_engagement_concern = 'medium'
                then 8
            else 15
        end as customer_success_component_score
    from base
),

scored as (
    select
        *,
        case
            when assessment_status in ('blocked_due_to_data_quality', 'not_assessable')
                then null
            else
                revenue_component_score
                + renewal_component_score
                + usage_component_score
                + support_component_score
                + customer_success_component_score
        end as health_score
    from component_scores
)

select
    account_id,
    account_month,
    assessment_status,
    assessment_reason_category,
    quality_status,
    case
        when assessment_status = 'blocked_due_to_data_quality'
            then quality_status_reason
        else null
    end as data_quality_blocker,
    health_score,
    case
        when health_score is null
            then null
        when health_score <= 44
            then 'critical'
        when health_score <= 64
            then 'at_risk'
        when health_score <= 79
            then 'monitor'
        else 'stable'
    end as health_band,
    revenue_component_score,
    renewal_component_score,
    usage_component_score,
    support_component_score,
    customer_success_component_score,
    revenue_exposure_amount,
    renewal_urgency,
    usage_concern,
    support_concern,
    customer_success_engagement_concern,
    revenue_or_billing_status_concern,
    active_contract_record_count,
    observed_closing_balance_amount,
    reconciliation_status,
    reconciliation_gap_amount,
    nearest_renewal_date,
    nearest_contract_end_date,
    days_to_renewal,
    days_to_contract_end,
    has_current_usage_record,
    active_users,
    previous_active_users,
    active_user_change_pct,
    support_ticket_count_90d,
    high_support_ticket_count_90d,
    open_support_ticket_count_90d,
    days_since_last_support_ticket,
    cs_interaction_count_90d,
    concerned_cs_interaction_count_90d,
    days_since_last_cs_interaction,
    has_missing_renewal_date,
    has_active_contract_contradiction,
    has_renewal_status_disagreement,
    case
        when assessment_status = 'blocked_due_to_data_quality'
            then 'Health assessment is blocked because critical data-quality exceptions are present.'
        when assessment_status = 'not_assessable'
            then 'Health assessment is not assessable because a required current usage, contract, or revenue-balance signal is absent.'
        when assessment_status = 'eligible_with_caveat'
            then 'Diagnostic health score is available with caveats from quality, reconciliation, renewal, or billing signals.'
        else 'Diagnostic health score is available from supported usage, support, Customer Success, renewal, and revenue signals.'
    end as explanation_summary,
    'synthetic_diagnostic_account_health' as synthetic_data_label,
    'simulated_threshold_assumptions_v1' as scoring_assumption_version,
    false as is_predictive_model_output,
    false as is_automated_recommendation
from scored
