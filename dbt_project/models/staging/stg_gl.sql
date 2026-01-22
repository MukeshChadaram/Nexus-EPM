with source as (
    select * from {{ source('nexus_core', 'general_ledger') }}
),

renamed as (
    select
        transaction_ref as txn_id,
        account_number as account_id,
        -- Correct the date type
        cast(post_date as date) as posting_date,
        -- Standardize amount to always be positive initially
        cast(amount as decimal(18,2)) as amount,
        dr_cr_indicator
    from source
)

select * from renamed