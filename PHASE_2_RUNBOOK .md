**Phase 2, Step 1: The Budget Loader**.

This update marks the transition of your system from a "Simple Ledger" (Recording History) to a "Performance Engine" (Analyzing Strategy).

---

# 📘 Part 1: Confluence Page Update

**Title:** Phase 2.1: The Planning Engine (Static Budgeting)
**Status:** ✅ Complete | **Date:** 2026-01-22

### 1. Executive Summary

We have successfully upgraded the Nexus EPM "Brain" to handle **multidimensional data**. The system can now compare "What Happened" (Actuals) against "What Should Have Happened" (Budget). This unlocks the ability for the CFO to instantly visualize performance gaps (Variance) without manual Excel reconciliation.

### 2. New Capabilities Delivered

| Feature | Description | Business Value |
| --- | --- | --- |
| **The "Multiverse" Database** | The database now stores multiple scenarios (Actual, Budget) in a single unified structure. | Allows for "apples-to-apples" comparison of any financial metric. |
| **Variance Calculation** | Automated math: `(Budget - Actual)`. | Instantly highlights overspending or revenue shortfalls. |
| **Performance Dashboard** | Visual Bar Charts comparing Blue Bars (Reality) vs. Orange Bars (Plan). | Provides immediate visual feedback on the health of the bank. |

### 3. Architecture Change

* **Before:** The system was a single pipe reading from the Bank Core.
* **After:** The system is now a **Funnel**. It merges data from the Bank Core and the Budget CSV into a single "Financial Cube."

---

# 🛠️ Part 2: Technical Runbook (Phase 2.1)

**Filename:** `PHASE_2_STEP_1_RUNBOOK.md`
**Description:** Technical log of the "Union Architecture" implementation.

## 1. The Concept: "UNION ALL"

*For the Beginner:*
Imagine you have two stacks of receipts. One stack is "Receipts from the Bank" (Actuals). The other stack is "Receipts I Wrote Myself" (Budget). To analyze your total financial picture, you don't want two separate piles. You want to stack them into **one single pile**, but you write "Budget" or "Actual" on the back of each receipt so you can tell them apart later.
In SQL, this stacking process is called `UNION ALL`.

## 2. File Changes

### A. The Input (The Plan)

**File:** `dbt_project/seeds/budget_2026.csv`
**Purpose:** Defines the targets.

```csv
account_id,budget_month,amount_signed,scenario
4200,2026-01-01,-3000.00,Budget
5200,2026-01-01,2000.00,Budget

```

### B. The Staging Layer (The Cleaner)

**File:** `dbt_project/models/staging/stg_budget.sql`
**Purpose:** Formats the Budget CSV to look exactly like the Bank Data (same column names).

```sql
with source as ( select * from {{ ref('budget_2026') }} )
select
    'BUDGET-' || account_id || '-' || budget_month as txn_id,
    cast(budget_month as date) as posting_date,
    account_id,
    cast(amount_signed as decimal(18,2)) as amount_signed,
    'Budget' as scenario
from source

```

### C. The Mart Layer (The Cube)

**File:** `dbt_project/models/marts/fact_financials.sql`
**Purpose:** The "Funnel." Merges the two streams using `UNION ALL`.

```sql
with actuals as (
    -- Logic to pull from stg_gl and label as 'Actual'
    -- (Remember to flip signs for CR/DR here)
),
budget as (
    -- Logic to pull from stg_budget
),
unioned as (
    select * from actuals
    union all
    select * from budget
)
-- Join with Chart of Accounts and output final table

```

### D. The Dashboard (The Eyes)

**File:** `app/main.py`
**Key Update:** Added `plotly.express` for Bar Charts and updated queries to group by `scenario`.

## 3. Common Pitfalls & Solutions

During this phase, we encountered and solved the following issues:

1. **The "Zombie" Lock:**
* *Issue:* `dbt run` failed because Streamlit was holding the database file open.
* *Fix:* `docker restart nexus-epm-core` to kill the process, then run dbt, then restart Streamlit.


2. **The "Ghost" Port:**
* *Issue:* Dashboard moved to port 8503 because 8501/8502 were occupied by crashed processes.
* *Fix:* `docker-compose down` followed by `docker-compose up -d`.


3. **The Nested Folder Trap:**
* *Issue:* `fact_financials.sql` was accidentally placed inside `models/staging/marts`.
* *Fix:* Moved `marts` to be a sibling of `staging` (`models/marts`).



## 4. Execution Log

Commands required to reproduce this state:

```powershell
# 1. Load the new Budget CSV into the database
docker exec -w /usr/src/app/dbt_project nexus-epm-core dbt seed

# 2. Build the new Union Model (Must show "Found 3 models")
docker exec -w /usr/src/app/dbt_project nexus-epm-core dbt run

# 3. Launch the upgraded Dashboard
docker exec nexus-epm-core streamlit run app/main.py

```

---

✅ Next Step: Phase 2.2 - The "Write-Back"

Currently, to change the budget, we have to edit a CSV file and run 3 commands. 

Objective: Build a form in the dashboard to let the user update the budget instantly from the browser.

Description: Technical log of the Write-Back logic, database schema updates, and integration pipeline.

1. Infrastructure: The "Sidecar" TableTo allow writes without locking the main warehouse, we created a dedicated table for user inputs.Script: app/init_db.py

Purpose: One-time setup to create the storage bucket for user inputs.

Python

import duckdb
con = duckdb.connect('/usr/src/app/data/nexus_epm.duckdb')
con.execute("""
    CREATE TABLE IF NOT EXISTS input_budget (
        entry_id VARCHAR,
        account_id INTEGER,
        budget_month DATE,
        amount DECIMAL(18,2),
        scenario VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("✅ 'input_budget' table created successfully!")
con.close()


2. Application Logic: The "Walkie-Talkie" ProtocolFile: app/main.pyChallenge: DuckDB is a file-based database. It cannot handle simultaneous "Read" and "Write" locks.Solution: We implemented a strict "Connect $\rightarrow$ Execute $\rightarrow$ Close" pattern. We removed @st.cache_resource to ensure the connection is dropped immediately after every query, preventing Resource temporarily unavailable errors.Key Code Snippet (Writer):Pythondef save_budget_entry(...):
    con = duckdb.connect(DB_PATH) # Open
    con.execute("INSERT INTO ...") # Write
    con.close()                    # Close (Hang Up)
	
	
3. Data Pipeline: The Integration (dbt)We updated the transformation layer to ingest the new user data.A. 

Staging Layer (The Cleaner)File: dbt_project/models/staging/stg_forecast.sql

Purpose: Reads raw user inputs and formats them to match the GL structure.

SQL

with source as ( select * from input_budget ),
renamed as (
    select
        'FORECAST-' || entry_id as txn_id,
        cast(budget_month as date) as posting_date,
        account_id,
        cast(amount as decimal(18,2)) as amount_signed,
        'Forecast' as scenario
    from source
)

select * from renamed

B. The Mart Layer (The 3-Way Union)File: dbt_project/models/marts/fact_financials.sqlPurpose: Merges all three data streams.SQLwith actuals as ( ... ),
budget as ( ... ),


forecast as ( select * from {{ ref('stg_forecast') }} ), -- New Stream

unioned as (
    select * from actuals
    union all
    select * from budget
    union all
    select * from forecast -- Merging the 3rd reality
)
select * from unioned ...


4. Execution LogTo reproduce the current state from scratch:

Step 1: Initialize Database

PowerShell# Create the input table
docker exec nexus-epm-core python app/init_db.py

Step 2: Build the Brain (Including Forecast)PowerShell# Compile all 4 models (stg_gl, stg_budget, stg_forecast, fact_financials)
docker exec -w /usr/src/app/dbt_project nexus-epm-core dbt run

Success Criteria: Output must show Found 4 models and OK created ....

Step 3: Launch DashboardPowerShell# Start the server (ensure no other python processes are running)
docker exec nexus-epm-core streamlit run app/main.py

5. Usage Procedure (How to Test)Open Dashboard: Go to localhost:8502.Input: Use sidebar to add 500 for Operating Expense. 
Click Save.
Verify Write: "View Recent Forecast Inputs" table updates instantly.
Verify Integration: (Currently requires manual dbt run) The "Trend Analysis" chart shows a Red Bar for the Forecast scenario.





# 📘 Phase 2 Master Runbook: The Planning Engine

**Version:** 1.0 | **Date:** 2026-01-22
**Objective:** Enable multidimensional analysis (Actual vs. Budget) and interactive forecasting.

---

## 1. Data Ingestion (Static Budget)

**Change:** Added a CSV file containing the 2026 budget targets.

**File:** `dbt_project/seeds/budget_2026.csv`
**(Save this exact content)**

```csv
account_id,budget_month,amount_signed,scenario
4200,2026-01-01,-3000.00,Budget
4200,2026-02-01,-3000.00,Budget
4200,2026-03-01,-3000.00,Budget
5200,2026-01-01,2000.00,Budget
5200,2026-02-01,2000.00,Budget
5200,2026-03-01,2000.00,Budget

```

---

## 2. Infrastructure Setup (The "Sidecar" Table)

**Change:** Created a Python script to initialize the separate table for user inputs, preventing "dirty writes" to the core warehouse.

**File:** `app/init_db.py`
**(Save this exact code)**

```python
import duckdb

# Connect to the Brain
con = duckdb.connect('/usr/src/app/data/nexus_epm.duckdb')

# Create the Input Table if it doesn't exist
con.execute("""
    CREATE TABLE IF NOT EXISTS input_budget (
        entry_id VARCHAR,
        account_id INTEGER,
        budget_month DATE,
        amount DECIMAL(18,2),
        scenario VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("✅ 'input_budget' table created successfully!")
con.close()

```

---

## 3. Transformation Layer (dbt Models)

**Change:** Created 3 distinct models to clean and merge the data streams.

### A. Staging: Budget (The Static Plan)

**File:** `dbt_project/models/staging/stg_budget.sql`

```sql
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

```

### B. Staging: Forecast (The User Input)

**File:** `dbt_project/models/staging/stg_forecast.sql`

```sql
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

```

### C. Marts: The Cube (The 3-Way Union)

**File:** `dbt_project/models/marts/fact_financials.sql`
**Note:** This file REPLACES the Phase 1 version entirely.

```sql
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
    union all
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

```

---

## 4. Application Logic (The "Write-Back" Dashboard)

**Change:** This was the intermediate dashboard used in Phase 2. It had the "Save" button but **NOT** the automation. It required manual terminal runs.
*(Note: Phase 3 superseded this file, but this is the record of Phase 2 logic).*

**File:** `app/main.py` (Phase 2 Snapshot)

```python
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import uuid
from datetime import date

st.set_page_config(page_title="Nexus EPM", page_icon="🏦", layout="wide")
st.title("🏦 Nexus EPM: Planning & Variance")

DB_PATH = '/usr/src/app/data/nexus_epm.duckdb'

# --- 1. THE WRITE-BACK ENGINE ---
def save_budget_entry(account_id, budget_date, amount):
    try:
        # Connect -> Write -> Close (The "Walkie-Talkie" method)
        con = duckdb.connect(DB_PATH)
        entry_id = str(uuid.uuid4())
        query = """
            INSERT INTO input_budget (entry_id, account_id, budget_month, amount, scenario)
            VALUES (?, ?, ?, ?, 'Forecast')
        """
        con.execute(query, [entry_id, account_id, budget_date, amount])
        con.close() 
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

# --- 2. THE READ ENGINE ---
def run_query(sql_query):
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute(sql_query).df()
    con.close() 
    return df

# --- 3. DASHBOARD UI ---
with st.sidebar:
    st.header("✏️ Update Forecast")
    with st.form("budget_form"):
        account = st.selectbox("Account", [
            (4200, "Fee Income (Revenue)"),
            (5200, "Operating Expense")
        ], format_func=lambda x: x[1])
        b_date = st.date_input("Month", date(2026, 3, 1))
        b_amount = st.number_input("Amount ($)", value=0.0, step=100.0)
        submit = st.form_submit_button("💾 Save to Database")
        
        if submit:
            final_amount = b_amount if account[0] != 4200 else b_amount * -1
            if save_budget_entry(account[0], b_date, final_amount):
                st.success("Saved! (Run 'dbt run' in terminal to update charts)")
                st.rerun()

# --- 4. VISUALS (Standard View) ---
# ... (Charts logic similar to Phase 3)

```

---

## 5. Execution & Verification Steps

To rebuild Phase 2 from scratch, you run these commands:

1. **Initialize Sidecar:** `docker exec nexus-epm-core python app/init_db.py`
2. **Load Budget:** `docker exec -w /usr/src/app/dbt_project nexus-epm-core dbt seed`
3. **Build Models:** `docker exec -w /usr/src/app/dbt_project nexus-epm-core dbt run`
* *Must confirm:* "Found 4 models" (stg_gl, stg_budget, stg_forecast, fact_financials).


4. **Run App:** `docker exec nexus-epm-core streamlit run app/main.py`

---
