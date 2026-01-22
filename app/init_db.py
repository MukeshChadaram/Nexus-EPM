import duckdb

# Connect to the Brain
con = duckdb.connect('/usr/src/app/data/nexus_epm.duckdb')

# Create the Input Table if it doesn't exist
# Note: We use the 'main' schema so dbt can see it later
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