with source as (
    select * from {{ ref('budget_2026') }}
),

renamed as (
    select
        'BUDGET-' || account_id || '-' || budget_month as txn_id,
        cast(budget_month as date) as posting_date,
        account_id,
        cast(amount_signed as decimal(18,2)) as amount_signed,
        'Budget' as scenario
    from source
)

select * from renamed