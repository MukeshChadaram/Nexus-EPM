# 🏦 Nexus EPM (Enterprise Performance Management)

## Overview
Nexus EPM is a "Production-Grade" financial planning platform. It allows Finance teams to compare Actuals (GL), Budgets (Static), and Forecasts (Dynamic) in a secure, authenticated environment.

**Status:** Phase 4 Complete (Production Gold)
**Date:** January 22, 2026

## 🚀 Key Features
1.  **Secure Login (RBAC):**
    * **Admin:** Read/Write access (Can adjust Forecasts).
    * **Viewer:** Read-Only access (Dashboard only).
2.  **AI Intelligence:**
    * Uses Historical Moving Averages to predict future expenses automatically.
3.  **Board Reporting:**
    * Generates downloadable PDF "Board Packs" for executive meetings.
4.  **Automated ETL:**
    * Python automatically triggers `dbt` transformations upon every save.

## 🛠️ Quick Start
1.  **Prerequisites:** Docker Desktop installed.
2.  **Start Application:**
    ```bash
    docker-compose up -d
    ```
3.  **Access Dashboard:** Open http://localhost:8502
4.  **Credentials:**
    * **Admin:** `admin` / `admin123`
    * **Viewer:** `viewer` / `view123`

## ⚙️ Technology Stack
* **Frontend:** Streamlit (Python)
* **Database:** DuckDB (OLAP Cube)
* **Logic:** dbt (Data Build Tool)
* **Reporting:** FPDF (PDF Generation)