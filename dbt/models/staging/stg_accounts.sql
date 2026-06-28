with source as (
    select * from {{ source('raw', 'accounts') }}
)

select
    account_id as raw_account_id,
    upper(trim(account_id)) as account_id,
    account_name,
    nullif(trim(segment), '') as segment,
    region,
    industry,
    created_date as raw_created_date,
    try_cast(nullif(created_date, '') as date) as created_date,
    lifecycle_status,
    crm_renewal_status,
    nullif(trim(owner_id), '') as owner_id,
    churn_date as raw_churn_date,
    try_cast(nullif(churn_date, '') as date) as churn_date,
    synthetic_data_label,
    scenario_version,
    generation_layer,
    nullif(quality_issue_type, '') as quality_issue_type,
    source_file_name,
    loaded_at,
    source_row_number,
    source_row_identifier,
    created_date <> '' and try_cast(created_date as date) is null
        as has_created_date_parse_failure,
    churn_date <> '' and try_cast(churn_date as date) is null
        as has_churn_date_parse_failure,
    nullif(trim(segment), '') is null or nullif(trim(owner_id), '') is null
        as has_missing_segment_or_owner,
    generation_layer = 'incident_injection' or nullif(quality_issue_type, '') is not null
        as has_injected_quality_issue
from source
