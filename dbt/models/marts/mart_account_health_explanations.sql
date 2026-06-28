with health as (
    select * from {{ ref('mart_account_health') }}
)

select
    account_id,
    account_month,
    'data_quality_gate' as component_name,
    quality_status as component_value,
    case
        when assessment_status = 'blocked_due_to_data_quality' then 'negative'
        when assessment_status = 'eligible_with_caveat' then 'neutral'
        else 'positive'
    end as impact_direction,
    case
        when assessment_status = 'blocked_due_to_data_quality' then 'high'
        when quality_status = 'warning' then 'medium'
        else 'none'
    end as severity,
    case
        when assessment_status = 'blocked_due_to_data_quality'
            then 'Critical data-quality exceptions block diagnostic health scoring.'
        when quality_status = 'warning'
            then 'Warning quality exceptions require caveated interpretation.'
        else 'No critical quality exception is mapped to this account-month.'
    end as plain_language_explanation,
    'dq_account_month_quality_status' as source_lineage_reference,
    synthetic_data_label
from health

union all

select
    account_id,
    account_month,
    'revenue' as component_name,
    coalesce(cast(revenue_component_score as varchar), 'not_scored') as component_value,
    case
        when revenue_or_billing_status_concern <> 'none' then 'negative'
        else 'positive'
    end as impact_direction,
    case
        when revenue_or_billing_status_concern = 'high' then 'high'
        when revenue_or_billing_status_concern = 'medium' then 'medium'
        else 'none'
    end as severity,
    case
        when health_score is null
            then 'Revenue component is not scored because the account-month is blocked or not assessable.'
        when revenue_or_billing_status_concern <> 'none'
            then 'Revenue evidence has a billing or reconciliation caveat; the component score is reduced.'
        else 'No supported revenue or billing concern is observed for this component.'
    end as plain_language_explanation,
    'mart_revenue_reconciliation_diagnostics' as source_lineage_reference,
    synthetic_data_label
from health

union all

select
    account_id,
    account_month,
    'renewal' as component_name,
    coalesce(cast(renewal_component_score as varchar), 'not_scored') as component_value,
    case
        when renewal_urgency in ('past_due_or_current', 'high', 'unknown_missing_renewal_date')
            then 'negative'
        when renewal_urgency in ('medium', 'low')
            then 'neutral'
        else 'positive'
    end as impact_direction,
    case
        when renewal_urgency in ('past_due_or_current', 'high', 'unknown_missing_renewal_date')
            then 'high'
        when renewal_urgency = 'medium'
            then 'medium'
        when renewal_urgency = 'low'
            then 'low'
        else 'none'
    end as severity,
    case
        when health_score is null
            then 'Renewal component is not scored because the account-month is blocked or not assessable.'
        when renewal_urgency = 'unknown_missing_renewal_date'
            then 'Renewal timing is missing, so the renewal component receives a high concern score.'
        when renewal_urgency in ('past_due_or_current', 'high')
            then 'Renewal or contract end timing is within 30 days or already current.'
        when renewal_urgency = 'medium'
            then 'Renewal or contract end timing is within 31 to 90 days.'
        when renewal_urgency = 'low'
            then 'Renewal or contract end timing is within 91 to 180 days.'
        else 'No near-term renewal timing concern is observed.'
    end as plain_language_explanation,
    'int_account_month_renewal_signals' as source_lineage_reference,
    synthetic_data_label
from health

union all

select
    account_id,
    account_month,
    'usage' as component_name,
    coalesce(cast(usage_component_score as varchar), 'not_scored') as component_value,
    case
        when usage_concern in ('high', 'medium') then 'negative'
        else 'positive'
    end as impact_direction,
    case
        when usage_concern = 'high' then 'high'
        when usage_concern = 'medium' then 'medium'
        else 'none'
    end as severity,
    case
        when health_score is null
            then 'Usage component is not scored because the account-month is blocked or not assessable.'
        when usage_concern = 'high'
            then 'Usage is inactive, zero, or declined by at least 50 percent under simulated thresholds.'
        when usage_concern = 'medium'
            then 'Usage is very low or declined by at least 25 percent under simulated thresholds.'
        else 'No supported usage concern is observed for this component.'
    end as plain_language_explanation,
    'stg_usage_events' as source_lineage_reference,
    synthetic_data_label
from health

union all

select
    account_id,
    account_month,
    'support' as component_name,
    coalesce(cast(support_component_score as varchar), 'not_scored') as component_value,
    case
        when support_concern in ('high', 'medium') then 'negative'
        else 'positive'
    end as impact_direction,
    case
        when support_concern = 'high' then 'high'
        when support_concern = 'medium' then 'medium'
        else 'none'
    end as severity,
    case
        when health_score is null
            then 'Support component is not scored because the account-month is blocked or not assessable.'
        when support_concern = 'high'
            then 'Recent support burden includes high severity, heavy open burden, or four or more tickets.'
        when support_concern = 'medium'
            then 'Recent support burden includes open or multiple tickets.'
        else 'No supported support-ticket concern is observed for this component.'
    end as plain_language_explanation,
    'stg_support_tickets' as source_lineage_reference,
    synthetic_data_label
from health

union all

select
    account_id,
    account_month,
    'customer_success' as component_name,
    coalesce(cast(customer_success_component_score as varchar), 'not_scored') as component_value,
    case
        when customer_success_engagement_concern in ('high', 'medium') then 'negative'
        else 'positive'
    end as impact_direction,
    case
        when customer_success_engagement_concern = 'high' then 'high'
        when customer_success_engagement_concern = 'medium' then 'medium'
        else 'none'
    end as severity,
    case
        when health_score is null
            then 'Customer Success component is not scored because the account-month is blocked or not assessable.'
        when customer_success_engagement_concern = 'high'
            then 'Recent Customer Success interactions include concerned sentiment.'
        when customer_success_engagement_concern = 'medium'
            then 'No Customer Success interaction is observed in the 90-day lookback window.'
        else 'Recent Customer Success coverage has no supported concern signal.'
    end as plain_language_explanation,
    'stg_cs_interactions' as source_lineage_reference,
    synthetic_data_label
from health
