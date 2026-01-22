# Technical Runbook (Phase 1)

**Filename:** `PHASE_1_RUNBOOK.md`
**Description:** A complete log of all code, files, and commands used to build the Nexus EPM Foundation.

## 1. Directory Structure Setup

We created a clean, isolated repository parallel to the banking core.

```text
nexus-epm/                  # Root Project Folder
├── app/                    # Frontend Application
│   └── main.py             # Streamlit Dashboard Logic
├── data/                   # Persisted Storage (Volume Mapped)
│   └── nexus_epm.duckdb    # The "Brain" (Database File)
├── dbt_project/            # Transformation Logic
│   ├── dbt_project.yml     # Project Config
│   ├── profiles.yml        # Connection Credentials
│   ├── models/             # SQL Logic
│   │   ├── staging/        # Cleaning Layer
│   │   └── marts/          # Cube Layer
│   └── seeds/              # CSV Data Files
├── Dockerfile              # Environment Definition
└── docker-compose.yml      # Service Orchestration

```

## 2. Infrastructure Configuration

### `Dockerfile`

*Purpose: Defines the OS, installs Python, dbt, and DuckDB.*

```dockerfile
FROM python:3.11-slim
WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y git libpq-dev gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /root/.dbt
COPY . .
EXPOSE 8502
CMD ["tail", "-f", "/dev/null"]

```

### `docker-compose.yml`

*Purpose: Spins up the container and maps port 8502.*

```yaml
version: '3.8'
services:
  nexus-epm-core:
    build: .
    container_name: nexus-epm-core
    ports:
      - "8502:8501"
    volumes:
      - .:/usr/src/app
      - epm_data:/usr/src/app/data
    environment:
      - DBT_PROFILES_DIR=/usr/src/app/dbt_project
volumes:
  epm_data:

```

## 3. The "Brain" Configuration (dbt)

### `dbt_project/profiles.yml`

*Purpose: Tells dbt to save data to our local DuckDB file.*

```yaml
nexus_finance:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: '/usr/src/app/data/nexus_epm.duckdb'
      extensions:
        - parquet

```

### `dbt_project/models/staging/src_nexus_core.yml`

*Purpose: The Data Contract (The Treaty).*

```yaml
version: 2
sources:
  - name: nexus_core
    schema: main
    tables:
      - name: general_ledger
        identifier: nexus_core_gl_dump
        columns:
          - name: transaction_ref
            tests: [unique, not_null]
          - name: dr_cr_indicator
            tests:
              - accepted_values: {values: ['DR', 'CR']}

```

## 4. Business Logic (SQL Models)

### `dbt_project/models/staging/stg_gl.sql`

*Purpose: Standardize types and clean raw names.*

```sql
with source as ( select * from {{ source('nexus_core', 'general_ledger') }} )
select
    transaction_ref as txn_id,
    account_number as account_id,
    cast(post_date as date) as posting_date,
    cast(amount as decimal(18,2)) as amount,
    dr_cr_indicator
from source

```

### `dbt_project/models/marts/fact_financials.sql`

*Purpose: The Financial Cube. Applies the "Signed Amount" rule.*

```sql
with gl as ( select * from {{ ref('stg_gl') }} ),
accounts as ( select * from {{ ref('chart_of_accounts') }} )
select
    gl.txn_id,
    gl.posting_date,
    a.account_name,
    a.account_type,
    case
        when gl.dr_cr_indicator = 'DR' then gl.amount
        when gl.dr_cr_indicator = 'CR' then gl.amount * -1
    end as amount_signed
from gl
left join accounts a on gl.account_id = a.account_id

```

## 5. Visualization (Streamlit)

### `app/main.py`

*Purpose: Connects to DuckDB and renders the KPIs.*
*Key Functionality:*

* Connects in `read_only=True` mode.
* Calculates `Net Equity` (Sum of all signed amounts).
* Displays a filtered grid of transactions.

## 6. Execution Log (CLI Commands)

These are the commands we ran to build the system:

**1. Start the Environment**

```powershell
docker-compose up -d --build

```

**2. Initialize dbt (One time setup)**

```powershell
docker exec -it nexus-epm-core dbt init nexus_finance
# (Selected '1' for DuckDB)
# Cleaned up folders:
docker exec nexus-epm-core bash -c "cp -r nexus_finance/* dbt_project/ && rm -rf nexus_finance"

```

**3. Ingest Data (The Seed)**

```powershell
docker exec -w /usr/src/app/dbt_project nexus-epm-core dbt seed

```

*Result:* `OK=2` (Loaded GL Dump and Chart of Accounts).

**4. Validate Contract (The Test)**

```powershell
docker exec -w /usr/src/app/dbt_project nexus-epm-core dbt test

```

*Result:* `PASS=4` (Data integrity confirmed).

**5. Build the Cube (The Run)**

```powershell
docker exec -w /usr/src/app/dbt_project nexus-epm-core dbt run

```

*Result:* Created `fact_financials` table.

**6. Launch Dashboard**

```powershell
docker exec nexus-epm-core streamlit run app/main.py

```

*Result:* Dashboard accessible at `http://localhost:8502`.