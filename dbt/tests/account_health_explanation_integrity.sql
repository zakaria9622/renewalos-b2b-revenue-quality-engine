with required_components(component_name) as (
    values
        ('revenue'),
        ('renewal'),
        ('usage'),
        ('support'),
        ('customer_success')
),

scored_rows as (
    select account_id, account_month
    from {{ ref('mart_account_health') }}
    where health_score is not null
),

missing_component_explanations as (
    select
        scored_rows.account_id,
        scored_rows.account_month,
        required_components.component_name
    from scored_rows
    cross join required_components
    left join {{ ref('mart_account_health_explanations') }} as explanations
        on scored_rows.account_id = explanations.account_id
        and scored_rows.account_month = explanations.account_month
        and required_components.component_name = explanations.component_name
    where explanations.component_name is null
),

blank_explanations as (
    select
        account_id,
        account_month,
        component_name
    from {{ ref('mart_account_health_explanations') }}
    where plain_language_explanation is null
        or plain_language_explanation = ''
        or source_lineage_reference is null
        or source_lineage_reference = ''
)

select * from missing_component_explanations
union all
select * from blank_explanations
