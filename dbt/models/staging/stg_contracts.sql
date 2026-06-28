with source as (
    select * from {{ source('raw', 'contracts') }}
)

select
    contract_id as raw_contract_id,
    upper(trim(contract_id)) as contract_id,
    account_id as raw_account_id,
    upper(trim(account_id)) as account_id,
    contract_start_date as raw_contract_start_date,
    try_cast(nullif(contract_start_date, '') as date) as contract_start_date,
    contract_end_date as raw_contract_end_date,
    try_cast(nullif(contract_end_date, '') as date) as contract_end_date,
    renewal_date as raw_renewal_date,
    try_cast(nullif(renewal_date, '') as date) as renewal_date,
    status as contract_status,
    arr_amount as raw_arr_amount,
    try_cast(nullif(arr_amount, '') as decimal(18, 2)) as arr_amount,
    product_tier,
    period_number as raw_period_number,
    try_cast(nullif(period_number, '') as integer) as period_number,
    synthetic_data_label,
    scenario_version,
    generation_layer,
    nullif(quality_issue_type, '') as quality_issue_type,
    source_file_name,
    loaded_at,
    source_row_number,
    source_row_identifier,
    contract_start_date <> '' and try_cast(contract_start_date as date) is null
        as has_contract_start_parse_failure,
    contract_end_date <> '' and try_cast(contract_end_date as date) is null
        as has_contract_end_parse_failure,
    renewal_date <> '' and try_cast(renewal_date as date) is null
        as has_renewal_date_parse_failure,
    nullif(trim(coalesce(renewal_date, '')), '') is null as has_missing_renewal_date,
    arr_amount <> '' and try_cast(arr_amount as decimal(18, 2)) is null
        as has_arr_amount_parse_failure,
    try_cast(contract_start_date as date) > try_cast(contract_end_date as date)
        as has_contract_end_before_start,
    generation_layer = 'incident_injection' or nullif(quality_issue_type, '') is not null
        as has_injected_quality_issue
from source
