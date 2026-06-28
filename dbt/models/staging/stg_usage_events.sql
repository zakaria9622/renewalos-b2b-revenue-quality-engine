with source as (
    select * from {{ source('raw', 'usage_events') }}
)

select
    usage_event_id as raw_usage_event_id,
    upper(trim(usage_event_id)) as usage_event_id,
    account_id as raw_account_id,
    upper(trim(account_id)) as account_id,
    activity_month as raw_activity_month,
    try_cast(nullif(activity_month, '') as date) as activity_month,
    active_users as raw_active_users,
    try_cast(nullif(active_users, '') as integer) as active_users,
    events_count as raw_events_count,
    try_cast(nullif(events_count, '') as integer) as events_count,
    usage_status,
    extract_date as raw_extract_date,
    try_cast(nullif(extract_date, '') as date) as extract_date,
    synthetic_data_label,
    scenario_version,
    generation_layer,
    nullif(quality_issue_type, '') as quality_issue_type,
    source_file_name,
    loaded_at,
    source_row_number,
    source_row_identifier,
    activity_month <> '' and try_cast(activity_month as date) is null
        as has_activity_month_parse_failure,
    active_users <> '' and try_cast(active_users as integer) is null
        as has_active_users_parse_failure,
    events_count <> '' and try_cast(events_count as integer) is null
        as has_events_count_parse_failure,
    extract_date <> '' and try_cast(extract_date as date) is null
        as has_extract_date_parse_failure,
    try_cast(nullif(extract_date, '') as date) < try_cast(nullif(activity_month, '') as date)
        as has_stale_extract_date,
    generation_layer = 'incident_injection' or nullif(quality_issue_type, '') is not null
        as has_injected_quality_issue
from source
