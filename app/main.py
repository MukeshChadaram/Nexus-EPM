import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import uuid
import subprocess
import shutil
from datetime import date, datetime
import time
import numpy as np
from fpdf import FPDF 

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Nexus EPM", page_icon="🏦", layout="wide")

DB_PATH = '/usr/src/app/data/nexus_epm.duckdb'

USERS = {
    "admin": "admin123",
    "viewer": "view123"
}

# --- 2. AUTHENTICATION ---
def check_login(username, password):
    if username in USERS and USERS[username] == password:
        return True
    return False

def login_screen():
    st.markdown("## 🔒 Nexus EPM Login")
    with st.form("login_form"):
        username = st.text_input("Username").lower()
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log In")
        
        if submit:
            if check_login(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = 'admin' if username == 'admin' else 'viewer'
                st.success("Login Successful!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Invalid Credentials")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.session_state['role'] = None
    st.rerun()

# --- 3. BACKEND ENGINES ---
def trigger_dbt_update():
    dbt_executable = shutil.which("dbt") or "dbt"
    try:
        with st.spinner("🔄 Integrating Forecast into Financial Cube..."):
            result = subprocess.run(
                [dbt_executable, "run"], 
                cwd="/usr/src/app/dbt_project", 
                capture_output=True, text=True
            )
        return result.returncode == 0
    except Exception as e:
        return False

def save_forecast(account_id, budget_date, amount, username):
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

# --- 4. INTELLIGENCE LAYERS ---
def predict_forecast(account_id):
    try:
        query = f"""
            SELECT amount_signed FROM main.fact_financials 
            WHERE account_id = {account_id} AND scenario = 'Actual'
            ORDER BY posting_date DESC LIMIT 6
        """
        df = get_data(query)
        if df.empty: return 0.0
        return abs(df['amount_signed'].mean())
    except:
        return 0.0

def generate_pdf_report(kpi_data, chart_data):
    """Generates a PDF Board Pack"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Nexus EPM: Monthly Board Pack", ln=1, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1, align='C')
    pdf.ln(10)
    
    # KPI Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="1. Executive Summary (KPIs)", ln=1)
    pdf.set_font("Arial", size=12)
    
    if not kpi_data.empty:
        act = kpi_data['actual'][0]
        bud = kpi_data['budget'][0]
        fcst = kpi_data['forecast'][0]
        var = fcst - bud
        
        pdf.cell(0, 10, f"Actuals (YTD): ${act:,.0f}", ln=1)
        pdf.cell(0, 10, f"Annual Budget: ${bud:,.0f}", ln=1)
        pdf.cell(0, 10, f"Live Forecast: ${fcst:,.0f}", ln=1)
        pdf.set_text_color(255, 0, 0) if var < 0 else pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 10, f"Variance vs Plan: ${var:,.0f}", ln=1)
        pdf.set_text_color(0, 0, 0) # Reset color
        
    pdf.ln(10)
    
    # Detailed Data Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="2. Category Breakdown", ln=1)
    pdf.set_font("Arial", size=10)
    
    # Simple table from chart data
    for index, row in chart_data.iterrows():
        line = f"{row['account_name']} ({row['scenario']}): ${row['total']:,.0f}"
        pdf.cell(0, 8, line, ln=1)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 5. MAIN APPLICATION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        login_screen()
else:
    col_title, col_user = st.columns([8, 2])
    with col_title:
        st.title("🏦 Nexus EPM: Intelligent Planning")
    with col_user:
        st.write(f"👤 **{st.session_state['username'].upper()}**")
        if st.button("Log Out"):
            logout()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("📝 Forecast Adjustment")
        if st.session_state['role'] == 'admin':
            account = st.selectbox("Account", [(4200, "Fee Income"), (5200, "OpEx")], format_func=lambda x: x[1])
            b_date = st.date_input("Period", date(2026, 3, 1))
            
            st.markdown("---")
            if st.button("✨ Analyze Trends"):
                prediction = predict_forecast(account[0])
                st.session_state['ai_suggestion'] = prediction
                st.info(f"Trend: **${prediction:,.2f}**")
            
            default_val = st.session_state.get('ai_suggestion', 0.0)
            
            with st.form("forecast_form"):
                b_amount = st.number_input("Amount ($)", value=default_val, step=100.0)
                if st.form_submit_button("💾 Save & Process"):
                    final_amount = b_amount if account[0] != 4200 else b_amount * -1
                    if save_forecast(account[0], b_date, final_amount, st.session_state['username']):
                        if trigger_dbt_update():
                            st.toast("✅ Saved!", icon="🟢")
                            if 'ai_suggestion' in st.session_state: del st.session_state['ai_suggestion']
                            time.sleep(1)
                            st.rerun()
        else:
            st.info("🔒 Read-Only Mode")

    # --- DASHBOARD ---
    try:
        # 1. Fetch Data
        kpi_sql = """
            SELECT 
                SUM(CASE WHEN scenario = 'Actual' THEN amount_signed ELSE 0 END) as actual,
                SUM(CASE WHEN scenario = 'Budget' THEN amount_signed ELSE 0 END) as budget,
                SUM(CASE WHEN scenario = 'Forecast' THEN amount_signed ELSE 0 END) as forecast
            FROM main.fact_financials WHERE report_category = 'P&L'
        """
        kpi = get_data(kpi_sql)
        
        chart_sql = """
            SELECT account_name, scenario, SUM(amount_signed) as total
            FROM main.fact_financials GROUP BY account_name, scenario
        """
        chart_data = get_data(chart_sql)

        # 2. Render KPIs
        if not kpi.empty:
            act, bud, fcst = kpi['actual'][0], kpi['budget'][0], kpi['forecast'][0]
            var = fcst - bud
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Actuals", f"${act:,.0f}")
            col2.metric("Budget", f"${bud:,.0f}")
            col3.metric("Forecast", f"${fcst:,.0f}")
            col4.metric("Variance", f"${var:,.0f}", delta_color="normal" if var > 0 else "inverse")
            
            # --- PDF DOWNLOAD BUTTON ---
            st.markdown("---")
            pdf_bytes = generate_pdf_report(kpi, chart_data)
            st.download_button(
                label="📄 Download Board Pack (PDF)",
                data=pdf_bytes,
                file_name=f"Nexus_Board_Pack_{date.today()}.pdf",
                mime="application/pdf"
            )

        # 3. Render Charts
        st.markdown("---")
        col_chart, col_data = st.columns([2, 1])
        with col_chart:
            st.subheader("📉 Scenario Comparison")
            fig = px.bar(chart_data, x="account_name", y="total", color="scenario", barmode="group",
                         color_discrete_map={"Actual": "#2E86C1", "Budget": "#F39C12", "Forecast": "#E74C3C"})
            st.plotly_chart(fig, use_container_width=True)
            
        with col_data:
            st.subheader("📋 Audit Trail")
            st.dataframe(get_data("SELECT * FROM input_budget ORDER BY created_at DESC LIMIT 5"), hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")