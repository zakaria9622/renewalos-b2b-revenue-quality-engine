with source as (
    select * from {{ source('raw', 'cs_interactions') }}
)

select
    interaction_id as raw_interaction_id,
    upper(trim(interaction_id)) as interaction_id,
    account_id as raw_account_id,
    upper(trim(account_id)) as account_id,
    interaction_date as raw_interaction_date,
    try_cast(nullif(interaction_date, '') as date) as interaction_date,
    interaction_type,
    sentiment,
    csm_owner_id,
    notes_category,
    synthetic_data_label,
    scenario_version,
    generation_layer,
    nullif(quality_issue_type, '') as quality_issue_type,
    source_file_name,
    loaded_at,
    source_row_number,
    source_row_identifier,
    interaction_date <> '' and try_cast(interaction_date as date) is null
        as has_interaction_date_parse_failure,
    generation_layer = 'incident_injection' or nullif(quality_issue_type, '') is not null
        as has_injected_quality_issue
from source
