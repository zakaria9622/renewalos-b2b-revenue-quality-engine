with source as (
    select * from {{ source('raw', 'billing_events') }}
)

select
    billing_event_id as raw_billing_event_id,
    upper(trim(billing_event_id)) as billing_event_id,
    account_id as raw_account_id,
    upper(trim(account_id)) as account_id,
    contract_id as raw_contract_id,
    upper(trim(contract_id)) as contract_id,
    event_date as raw_event_date,
    try_cast(nullif(event_date, '') as date) as event_date,
    effective_date as raw_effective_date,
    try_cast(nullif(effective_date, '') as date) as effective_date,
    received_at as raw_received_at,
    try_cast(nullif(received_at, '') as date) as received_at,
    event_type,
    arr_delta as raw_arr_delta,
    try_cast(nullif(arr_delta, '') as decimal(18, 2)) as arr_delta,
    amount as raw_amount,
    try_cast(nullif(amount, '') as decimal(18, 2)) as amount,
    billing_status,
    synthetic_data_label,
    scenario_version,
    generation_layer,
    nullif(quality_issue_type, '') as quality_issue_type,
    source_file_name,
    loaded_at,
    source_row_number,
    source_row_identifier,
    event_date <> '' and try_cast(event_date as date) is null
        as has_event_date_parse_failure,
    effective_date <> '' and try_cast(effective_date as date) is null
        as has_effective_date_parse_failure,
    received_at <> '' and try_cast(received_at as date) is null
        as has_received_at_parse_failure,
    arr_delta <> '' and try_cast(arr_delta as decimal(18, 2)) is null
        as has_arr_delta_parse_failure,
    amount <> '' and try_cast(amount as decimal(18, 2)) is null
        as has_amount_parse_failure,
    date_diff(
        'day',
        try_cast(nullif(effective_date, '') as date),
        try_cast(nullif(received_at, '') as date)
    ) > 30 as has_late_arrival,
    try_cast(nullif(arr_delta, '') as decimal(18, 2)) < 0
        and event_type not in ('contraction_arr', 'churned_arr')
        as has_invalid_negative_arr_movement,
    generation_layer = 'incident_injection' or nullif(quality_issue_type, '') is not null
        as has_injected_quality_issue
from source
