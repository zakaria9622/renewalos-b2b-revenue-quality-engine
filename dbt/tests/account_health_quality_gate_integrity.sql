select
    health.account_id,
    health.account_month,
    health.assessment_status,
    health.quality_status,
    quality_status.quality_status as expected_quality_status,
    health.health_score,
    health.health_band
from {{ ref('mart_account_health') }} as health
left join {{ ref('dq_account_month_quality_status') }} as quality_status
    on health.account_id = quality_status.account_id
    and health.account_month = quality_status.account_month
where quality_status.quality_status is null
    or health.quality_status <> quality_status.quality_status
    or (
        quality_status.quality_status = 'blocked'
        and (
            health.assessment_status <> 'blocked_due_to_data_quality'
            or health.health_score is not null
            or health.health_band is not null
        )
    )
    or (
        health.assessment_status in ('blocked_due_to_data_quality', 'not_assessable')
        and (
            health.health_score is not null
            or health.health_band is not null
        )
    )
    or (
        health.assessment_status in ('eligible', 'eligible_with_caveat')
        and (
            health.health_score is null
            or health.health_band not in ('critical', 'at_risk', 'monitor', 'stable')
        )
    )
    or health.assessment_status not in (
        'blocked_due_to_data_quality',
        'not_assessable',
        'eligible_with_caveat',
        'eligible'
    )
