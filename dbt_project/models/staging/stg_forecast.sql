with source as (
    -- We read directly from the table you created with Python
    select * from input_budget
),

renamed as (
    select
        'FORECAST-' || entry_id as txn_id,
        cast(budget_month as date) as posting_date,
        account_id,
        cast(amount as decimal(18,2)) as amount_signed,
        'Forecast' as scenario -- This is the new tag!
    from source
)

select * from renamed