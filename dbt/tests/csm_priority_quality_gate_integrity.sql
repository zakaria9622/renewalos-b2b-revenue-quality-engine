select
    account_id,
    account_month,
    assessment_status,
    quality_status,
    is_eligible_candidate,
    exclusion_reason
from {{ ref('mart_csm_priority_candidates') }}
where (
        assessment_status in ('blocked_due_to_data_quality', 'not_assessable')
        and is_eligible_candidate
    )
    or (
        quality_status = 'blocked'
        and is_eligible_candidate
    )
    or (
        not is_eligible_candidate
        and exclusion_reason is null
    )
    or (
        is_eligible_candidate
        and (
            health_score is null
            or revenue_exposure_amount is null
            or revenue_exposure_amount <= 0
            or explanation_drivers is null
            or explanation_drivers = ''
        )
    )
