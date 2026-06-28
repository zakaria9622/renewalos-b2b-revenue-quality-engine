with reconciliation as (
    select * from {{ ref('mart_revenue_reconciliation_diagnostics') }}
),

quality_status as (
    select * from {{ ref('dq_account_month_quality_status') }}
)

select
    reconciliation.account_id,
    reconciliation.account_month,
    quality_status.quality_status as account_month_quality_status,
    quality_status.critical_exception_count,
    quality_status.warning_exception_count,
    reconciliation.reconciliation_status,
    reconciliation.reconciliation_gap_amount,
    case
        when quality_status.quality_status = 'blocked'
            or reconciliation.reconciliation_status = 'blocked_by_quality_exception'
            then 'blocked'
        when reconciliation.reconciliation_status = 'gap_observed'
            then 'blocked'
        when reconciliation.reconciliation_status = 'not_assessable_no_observed_contract_balance'
            then 'not_assessable'
        when quality_status.quality_status in ('warning', 'eligible_with_caveat')
            then 'eligible_with_caveat'
        when reconciliation.reconciliation_status = 'no_gap_observed_preliminary'
            then 'eligible_with_caveat'
        else 'not_assessable'
    end as revenue_metric_gate_status,
    case
        when quality_status.quality_status = 'blocked'
            or reconciliation.reconciliation_status = 'blocked_by_quality_exception'
            then 'Revenue metrics are blocked by critical source-quality exceptions.'
        when reconciliation.reconciliation_status = 'gap_observed'
            then 'Revenue metrics are blocked because expected and observed balances do not reconcile.'
        when reconciliation.reconciliation_status = 'not_assessable_no_observed_contract_balance'
            then 'Revenue metrics are not assessable because observed contract balance is absent.'
        when quality_status.quality_status = 'warning'
            then 'Revenue metrics may be reviewed only with caveats because warning exceptions exist.'
        when reconciliation.reconciliation_status = 'no_gap_observed_preliminary'
            then 'No gap is observed, but output remains synthetic and preliminary.'
        else 'Revenue metric gate status is not assessable from current diagnostic fields.'
    end as management_kpi_gate_reason,
    false as is_management_kpi_reporting_approved
from reconciliation
left join quality_status
    on reconciliation.account_id = quality_status.account_id
    and reconciliation.account_month = quality_status.account_month
