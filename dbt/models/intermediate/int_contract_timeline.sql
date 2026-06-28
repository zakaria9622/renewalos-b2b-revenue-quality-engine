with contracts as (
    select * from {{ ref('stg_contracts') }}
),

account_keys as (
    select account_id from {{ ref('stg_accounts') }}
),

latest_observed_month as (
    select max(account_month) as max_account_month
    from {{ ref('int_account_month_spine') }}
)

select
    contracts.*,
    account_keys.account_id is null as is_account_identifier_missing_from_accounts,
    exists (
        select 1
        from contracts as other_contract
        where other_contract.account_id = contracts.account_id
            and other_contract.source_row_identifier <> contracts.source_row_identifier
            and contracts.contract_start_date is not null
            and contracts.contract_end_date is not null
            and other_contract.contract_start_date is not null
            and other_contract.contract_end_date is not null
            and contracts.contract_start_date <= other_contract.contract_end_date
            and other_contract.contract_start_date <= contracts.contract_end_date
    ) as has_overlapping_contract_period,
    contracts.contract_status = 'active'
        and contracts.contract_end_date < latest_observed_month.max_account_month
        as has_active_status_after_observed_end,
    (
        contracts.has_missing_renewal_date
        or contracts.has_contract_end_before_start
        or contracts.has_injected_quality_issue
        or account_keys.account_id is null
        or (
            contracts.contract_status = 'active'
            and contracts.contract_end_date < latest_observed_month.max_account_month
        )
    ) as is_exception_ready
from contracts
left join account_keys
    on contracts.account_id = account_keys.account_id
cross join latest_observed_month
