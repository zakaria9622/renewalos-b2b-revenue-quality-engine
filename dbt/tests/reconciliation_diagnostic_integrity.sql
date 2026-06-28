with stats as (
    select
        count(*) filter (
            where reconciliation_gap_amount is not null
                and abs(reconciliation_gap_amount) > 0.01
        ) as nonzero_gap_count,
        count(*) filter (
            where reconciliation_status = 'gap_observed'
        ) as gap_status_count
    from {{ ref('mart_revenue_reconciliation_diagnostics') }}
)

select *
from stats
where nonzero_gap_count = 0
    or gap_status_count = 0
