with spine as (
    select * from {{ ref('int_account_month_spine') }}
),

contract_exposure as (
    select
        spine.account_id,
        spine.account_month,
        count(contract_timeline.contract_id) as active_contract_record_count,
        sum(contract_timeline.arr_amount) as observed_closing_balance_amount,
        max(case when contract_timeline.has_overlapping_contract_period then 1 else 0 end) = 1
            as has_overlapping_contract_period,
        max(case when contract_timeline.has_active_status_after_observed_end then 1 else 0 end) = 1
            as has_active_status_after_observed_end,
        max(case when contract_timeline.has_missing_renewal_date then 1 else 0 end) = 1
            as has_missing_renewal_date,
        max(case when contract_timeline.has_injected_quality_issue then 1 else 0 end) = 1
            as has_contract_incident_marker
    from spine
    left join {{ ref('int_contract_timeline') }} as contract_timeline
        on spine.account_id = contract_timeline.account_id
        and spine.account_month between
            cast(date_trunc('month', contract_timeline.contract_start_date) as date)
            and cast(date_trunc('month', contract_timeline.contract_end_date) as date)
    group by spine.account_id, spine.account_month
),

revenue as (
    select * from {{ ref('mart_account_month_revenue') }}
),

quality_status as (
    select * from {{ ref('dq_account_month_quality_status') }}
),

movement_balances as (
    select
        revenue.*,
        coalesce(
            sum(revenue.supported_revenue_movement_amount) over (
                partition by revenue.account_id
                order by revenue.account_month
                rows between unbounded preceding and 1 preceding
            ),
            0
        ) as opening_balance_amount
    from revenue
),

calculated as (
    select
        movement_balances.account_id,
        movement_balances.account_month,
        movement_balances.billing_event_count,
        movement_balances.opening_balance_amount,
        movement_balances.opening_arr_movement,
        movement_balances.new_arr_movement,
        movement_balances.expansion_arr_movement,
        movement_balances.contraction_arr_movement,
        movement_balances.churned_arr_movement,
        movement_balances.supported_revenue_movement_amount,
        movement_balances.manual_adjustment_amount,
        movement_balances.opening_balance_amount
            + movement_balances.supported_revenue_movement_amount
            as expected_closing_balance_amount,
        contract_exposure.observed_closing_balance_amount,
        case
            when contract_exposure.observed_closing_balance_amount is null
                then null
            else contract_exposure.observed_closing_balance_amount
                - (
                    movement_balances.opening_balance_amount
                    + movement_balances.supported_revenue_movement_amount
                )
        end as reconciliation_gap_amount,
        coalesce(contract_exposure.active_contract_record_count, 0) as active_contract_record_count,
        coalesce(contract_exposure.has_overlapping_contract_period, false)
            as has_overlapping_contract_period,
        coalesce(contract_exposure.has_active_status_after_observed_end, false)
            as has_active_status_after_observed_end,
        coalesce(contract_exposure.has_missing_renewal_date, false) as has_missing_renewal_date,
        coalesce(contract_exposure.has_contract_incident_marker, false)
            as has_contract_incident_marker,
        movement_balances.has_late_arrival,
        movement_balances.has_orphaned_billing_reference,
        movement_balances.has_invalid_negative_arr_movement,
        movement_balances.has_injected_quality_issue as has_billing_incident_marker,
        quality_status.quality_status,
        quality_status.critical_exception_count,
        quality_status.warning_exception_count,
        quality_status.detected_rule_ids,
        quality_status.quality_status_reason
    from movement_balances
    left join contract_exposure
        on movement_balances.account_id = contract_exposure.account_id
        and movement_balances.account_month = contract_exposure.account_month
    left join quality_status
        on movement_balances.account_id = quality_status.account_id
        and movement_balances.account_month = quality_status.account_month
)

select
    account_id,
    account_month,
    billing_event_count,
    opening_balance_amount,
    opening_arr_movement,
    new_arr_movement,
    expansion_arr_movement,
    contraction_arr_movement,
    churned_arr_movement,
    supported_revenue_movement_amount,
    manual_adjustment_amount,
    expected_closing_balance_amount,
    observed_closing_balance_amount,
    reconciliation_gap_amount,
    reconciliation_gap_amount as preliminary_contract_vs_billing_difference_amount,
    active_contract_record_count,
    has_overlapping_contract_period,
    has_active_status_after_observed_end,
    has_missing_renewal_date,
    has_contract_incident_marker,
    has_late_arrival,
    has_orphaned_billing_reference,
    has_invalid_negative_arr_movement,
    has_billing_incident_marker,
    quality_status,
    critical_exception_count,
    warning_exception_count,
    detected_rule_ids,
    case
        when quality_status = 'blocked'
            then 'blocked_by_quality_exception'
        when observed_closing_balance_amount is null
            then 'not_assessable_no_observed_contract_balance'
        when abs(reconciliation_gap_amount) > 0.01
            then 'gap_observed'
        when quality_status = 'warning'
            then 'eligible_with_caveat_quality_warning'
        else 'no_gap_observed_preliminary'
    end as reconciliation_status,
    case
        when quality_status = 'blocked'
            then quality_status_reason
        when quality_status = 'warning'
            then quality_status_reason
        else null
    end as quality_blocker,
    case
        when quality_status = 'blocked'
            then 'Critical quality exception prevents management KPI use.'
        when observed_closing_balance_amount is null
            then 'Observed contract closing balance is not derivable for this account-month.'
        when abs(reconciliation_gap_amount) > 0.01
            then 'Expected closing balance and observed contract balance do not reconcile.'
        when quality_status = 'warning'
            then 'No nonzero reconciliation gap is observed, but warning exceptions require caveated review.'
        else 'No nonzero gap is observed in the preliminary diagnostic comparison.'
    end as reconciliation_explanation,
    false as is_kpi_eligible,
    case
        when quality_status = 'blocked'
            then 'blocked_by_quality_exception'
        when observed_closing_balance_amount is null
            then 'not_assessable_no_observed_contract_balance'
        when abs(reconciliation_gap_amount) > 0.01
            then 'gap_observed'
        when quality_status = 'warning'
            then 'eligible_with_caveat_quality_warning'
        else 'no_gap_observed_preliminary'
    end as diagnostic_status,
    'diagnostic reconciliation only; management KPI reporting remains gated'
        as diagnostic_note
from calculated
