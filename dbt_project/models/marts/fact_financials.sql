with actuals as (
    select
        txn_id,
        posting_date,
        account_id,
        case
            when dr_cr_indicator = 'DR' then amount
            when dr_cr_indicator = 'CR' then amount * -1
        end as amount_signed,
        'Actual' as scenario
    from {{ ref('stg_gl') }}
),

budget as (
    select
        txn_id,
        posting_date,
        account_id,
        amount_signed,
        scenario
    from {{ ref('stg_budget') }}
),

-- NEW SECTION: The User Inputs
forecast as (
    select
        txn_id,
        posting_date,
        account_id,
        amount_signed,
        scenario
    from {{ ref('stg_forecast') }}
),

unioned as (
    select * from actuals
    union all
    select * from budget
    union all           -- <--- Adding the 3rd leg
    select * from forecast
),

accounts as (
    select * from {{ ref('chart_of_accounts') }}
)

select
    u.txn_id,
    u.posting_date,
    u.scenario,
    u.account_id,
    a.account_name,
    a.account_type,
    a.report_category,
    u.amount_signed
from unioned u
left join accounts a on u.account_id = a.account_id