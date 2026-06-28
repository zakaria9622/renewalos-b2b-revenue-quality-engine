with source as (
    select * from {{ source('raw', 'support_tickets') }}
)

select
    ticket_id as raw_ticket_id,
    upper(trim(ticket_id)) as ticket_id,
    account_id as raw_account_id,
    upper(trim(account_id)) as account_id,
    created_at as raw_created_at,
    try_cast(nullif(created_at, '') as date) as created_at,
    status as ticket_status,
    severity,
    category,
    synthetic_data_label,
    scenario_version,
    generation_layer,
    nullif(quality_issue_type, '') as quality_issue_type,
    source_file_name,
    loaded_at,
    source_row_number,
    source_row_identifier,
    created_at <> '' and try_cast(created_at as date) is null
        as has_created_at_parse_failure,
    generation_layer = 'incident_injection' or nullif(quality_issue_type, '') is not null
        as has_injected_quality_issue
from source
