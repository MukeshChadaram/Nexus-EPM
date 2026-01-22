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