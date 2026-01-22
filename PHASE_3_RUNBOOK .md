Automation Logic and Process Control.

1. The Concept: "The Robot Arm"
For the Executive: Imagine your database is a vault. In Phase 2, you wrote a note and slipped it under the door, but you had to call a security guard (the Engineer) to go inside and file it. In Phase 3, we built a robotic arm inside the vault. When you slip the note under the door, the robot arm automatically wakes up, grabs the note, files it, and flashes a green light.

For the Engineer: We used Python's subprocess library to execute shell commands. This allows the Streamlit container to run dbt run as a child process.

2. Technical Implementation
A. The Trigger Function
File: app/main.py Logic:

Locate: Find where the dbt program is installed using shutil.which.

Execute: Run subprocess.run(["dbt", "run"], ...) to trigger the transformation.

Capture: Record stdout (logs) and stderr (errors) to display on the UI if needed.

Python

def trigger_dbt_update():
    dbt_exec = shutil.which("dbt") or "dbt"
    # The 'Spinner' blocks the UI so the user knows to wait
    with st.spinner("Processing..."):
        result = subprocess.run(
            [dbt_exec, "run"],
            cwd="/usr/src/app/dbt_project", # Run inside the project folder
            capture_output=True,
            text=True
        )
    return result.returncode == 0
B. The Integration Point
We hooked the trigger directly into the "Save" button workflow:

Python

if submit_button:
    save_to_db()        # Step 1: Write raw data
    trigger_dbt_update() # Step 2: Trigger the robot arm
    st.rerun()          # Step 3: Refresh the screen
3. Troubleshooting & Debugging
If the automation fails, check these common culprits:

Error: "dbt not found"

Cause: The Python environment path is different from the Terminal path.

Fix: Use shutil.which("dbt") to dynamically find the executable path, or hardcode it (e.g., /usr/local/bin/dbt).

Error: "Spinner spins forever"

Cause: The dbt run command is hanging or waiting for input.

Fix: Check the Docker logs (docker logs nexus-epm-core) to see if dbt is asking for a password or stuck on a lock.

4. Full System Architecture (Final State)

Frontend: Streamlit (User Interface)

Orchestrator: Python Subprocess (The Automation Link)

Compute: dbt (The Logic Engine)

Storage: DuckDB (The Database)

Source: CSV + User Inputs





# 📘 Phase 3 Master Runbook: Automation & Polish

**Version:** 1.0 | **Date:** 2026-01-22
**Objective:** Upgrade Nexus EPM from "Manual Terminal Execution" to "Self-Service Application."

---

## 1. Core Application Update (`app/main.py`)

**Change:** Replaced the entire dashboard code to include the `subprocess` automation engine and the "Spinners/Toasts" for user feedback.

**File:** `app/main.py`
**(Save this exact code)**

```python
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import uuid
import subprocess
import shutil
from datetime import date

# 1. Configuration & Title
st.set_page_config(page_title="Nexus EPM", page_icon="🏦", layout="wide")
st.title("🏦 Nexus EPM: Intelligent Planning")

DB_PATH = '/usr/src/app/data/nexus_epm.duckdb'

# --- 2. THE AUTOMATION ENGINE (Production Mode) ---
def trigger_dbt_update():
    """
    Executes dbt run silently and returns status.
    """
    dbt_executable = shutil.which("dbt") or "dbt"
    try:
        # The Spinner gives the user visual feedback while the backend works
        with st.spinner("🔄 Integrating Forecast into Financial Cube..."):
            result = subprocess.run(
                [dbt_executable, "run"], 
                cwd="/usr/src/app/dbt_project", 
                capture_output=True, 
                text=True
            )
            
        if result.returncode == 0:
            return True
        else:
            st.error("🚨 Transformation Failed")
            with st.expander("Error Log"):
                st.code(result.stderr)
            return False
    except Exception as e:
        st.error(f"System Error: {e}")
        return False

# --- 3. DATABASE FUNCTIONS ---
def save_forecast(account_id, budget_date, amount):
    try:
        con = duckdb.connect(DB_PATH)
        entry_id = str(uuid.uuid4())
        con.execute("""
            INSERT INTO input_budget (entry_id, account_id, budget_month, amount, scenario)
            VALUES (?, ?, ?, ?, 'Forecast')
        """, [entry_id, account_id, budget_date, amount])
        con.close()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def get_data(query):
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute(query).df()
    con.close()
    return df

# --- 4. SIDEBAR (Input) ---
with st.sidebar:
    st.header("📝 Forecast Adjustment")
    with st.form("forecast_form"):
        account = st.selectbox("Account", [
            (4200, "Fee Income (Revenue)"), 
            (5200, "Operating Expense")
        ], format_func=lambda x: x[1])
        
        b_date = st.date_input("Period", date(2026, 3, 1))
        b_amount = st.number_input("Adjustment ($)", value=0.0, step=100.0)
        
        submitted = st.form_submit_button("💾 Save & Process")
        
        if submitted:
            # 1. Adjust Signage
            final_amount = b_amount if account[0] != 4200 else b_amount * -1
            
            # 2. Save
            if save_forecast(account[0], b_date, final_amount):
                # 3. Trigger Automation
                if trigger_dbt_update():
                    st.toast("✅ Forecast Integrated Successfully!", icon="🟢")
                    st.rerun()

# --- 5. MAIN DASHBOARD ---
try:
    # A. KPI Section
    st.subheader("📊 Corporate Performance")
    kpi_sql = """
        SELECT 
            SUM(CASE WHEN scenario = 'Actual' THEN amount_signed ELSE 0 END) as actual,
            SUM(CASE WHEN scenario = 'Budget' THEN amount_signed ELSE 0 END) as budget,
            SUM(CASE WHEN scenario = 'Forecast' THEN amount_signed ELSE 0 END) as forecast
        FROM main.fact_financials
        WHERE report_category = 'P&L'
    """
    kpi = get_data(kpi_sql)
    
    if not kpi.empty:
        # Calculate Variances
        act = kpi['actual'][0]
        bud = kpi['budget'][0]
        fcst = kpi['forecast'][0]
        var_vs_plan = fcst - bud
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Actuals (YTD)", f"${act:,.0f}")
        col2.metric("Annual Budget", f"${bud:,.0f}")
        col3.metric("Live Forecast", f"${fcst:,.0f}")
        col4.metric("Proj. Variance", f"${var_vs_plan:,.0f}", 
                    delta_color="normal" if var_vs_plan > 0 else "inverse")

    st.markdown("---")

    # B. Visualization Section
    col_chart, col_data = st.columns([2, 1])
    
    with col_chart:
        st.subheader("📉 Scenario Comparison")
        chart_data = get_data("""
            SELECT account_name, scenario, SUM(amount_signed) as total
            FROM main.fact_financials
            GROUP BY account_name, scenario
        """)
        
        fig = px.bar(
            chart_data, x="account_name", y="total", 
            color="scenario", barmode="group",
            color_discrete_map={"Actual": "#2E86C1", "Budget": "#F39C12", "Forecast": "#E74C3C"},
            title="Actuals vs Budget vs Forecast"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col_data:
        st.subheader("📋 Recent Entries")
        recent_inputs = get_data("SELECT * FROM input_budget ORDER BY created_at DESC LIMIT 10")
        st.dataframe(recent_inputs, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Application Error: {e}")

```

---

## 2. Diagnostic Tool (`app/debug.py`)

**Change:** Added a script to troubleshoot path issues if the automation fails silently.

**File:** `app/debug.py`
**(Save this for future maintenance)**

```python
import shutil
import subprocess

print("🔍 DIAGNOSTIC REPORT")
print("--------------------")

# 1. Find the executable
dbt_path = shutil.which("dbt")
if dbt_path:
    print(f"✅ dbt found at: {dbt_path}")
else:
    print("❌ dbt NOT found in PATH")

# 2. Try to run it
try:
    print("🔄 Attempting to run 'dbt --version'...")
    result = subprocess.run(
        ["dbt", "--version"], 
        capture_output=True, 
        text=True
    )
    print(f"Output: {result.stdout}")
    print(f"Errors: {result.stderr}")
except Exception as e:
    print(f"🚨 Crash: {e}")

```

---

## 3. Project Documentation (`README.md`)

**Change:** Created the root documentation file for project handoff.

**File:** `README.md`
**(Save in the root `nexus-epm` folder)**

```markdown
# 🏦 Nexus EPM (Enterprise Performance Management)

## Overview
Nexus EPM is a Dockerized financial planning application that allows users to compare Actuals (from General Ledger) vs. Budget (Static) vs. Forecast (Dynamic).

**Status:** Phase 3 Complete (Automated Self-Service)
**Date:** January 22, 2026

## Features
* **Multi-Scenario Data Cube:** Combines Actuals, Budgets, and Forecasts.
* **Interactive Write-Back:** Users can input forecast adjustments via Streamlit.
* **Automated Pipeline:** Python automatically triggers `dbt` transformations upon save.
* **Visualization:** Real-time variance analysis using Plotly.

## Quick Start
1.  **Prerequisites:** Docker Desktop installed.
2.  **Start Application:**
    ```bash
    docker-compose up -d
    ```
3.  **Access Dashboard:** Open http://localhost:8502
4.  **Stop Application:**
    ```bash
    docker-compose down
    ```

## Technology Stack
* **Frontend:** Streamlit (Python)
* **Database:** DuckDB (OLAP)
* **Transformation:** dbt (Data Build Tool)
* **Infrastructure:** Docker & Docker Compose

```

---

## 4. Packaging Procedure

**Change:** Instructions for creating the "Golden Copy" zip file.

**Steps:**

1. **Stop Containers:** `docker-compose down` (Crucial to release database locks).
2. **Verify Stop:** `docker ps` (Ensure list is empty).
3. **Zip Folder:**
* **Windows:** Right-click folder  Send to  Compressed (zipped) folder.
* **Mac/Linux:** `zip -r Nexus_EPM_Phase3.zip nexus-epm/`

