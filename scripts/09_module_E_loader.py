"""
MODULE E — LOADER WITH ERROR TRACKING + 5000 BATCH + PROGRESS

Features:
- Converts 'nan' strings into None automatically
- Tracks errors per table
- Stops final success message if anything failed
"""

import os
import csv
from math import ceil
from supabase import create_client


# =======================================================
# ENVIRONMENT
# =======================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SERVICE_ROLE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY.")

supabase = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

CSV_FOLDER = "output/normalized"

TABLES = {
    "dim_regions": "dim_regions.csv",
    "dim_states": "dim_states.csv",
    "dim_customers": "dim_customers.csv",
    "fact_policies": "fact_policies.csv",
    "fact_claims": "fact_claims.csv",
    "fact_quotes": "fact_quotes.csv",
    "fact_uw_decisions": "fact_uw_decisions.csv",
    "fact_retention": "fact_retention.csv",
    "fact_pricing_segments": "fact_pricing_segments.csv",
    "fact_loss_development": "fact_loss_development.csv"
}

BATCH_SIZE = 5000
errors = {}  # table_name → error_message


# =======================================================
# HELPERS
# =======================================================

def clean_nan(row):
    """Convert 'nan', 'NaN', '', 'None' into proper Python None."""
    return {k: (None if str(v).lower() in ("nan", "none", "") else v)
            for k, v in row.items()}


def read_csv(path):
    """Reads CSV file into list of dicts and cleans nan."""
    with open(path, mode="r", encoding="utf-8") as f:
        return [clean_nan(r) for r in csv.DictReader(f)]


def insert_batches(table, rows):
    total = len(rows)
    num_batches = ceil(total / BATCH_SIZE)

    print(f"\nLoading {table} ({total} rows)...")

    for batch_idx in range(num_batches):
        start = batch_idx * BATCH_SIZE
        end = min(start + BATCH_SIZE, total)
        batch = rows[start:end]

        try:
            supabase.table(table).insert(batch).execute()
        except Exception as e:
            err_msg = f"Batch {batch_idx+1}/{num_batches} failed: {e}"
            errors[table] = err_msg
            print(f"\n✖ ERROR: {err_msg}")
            print("Example rows:", batch[:2])
            return False

        print(f"Batch {batch_idx+1}/{num_batches} inserted "
              f"({end}/{total} rows)")

    print(f"✔ Finished loading: {table}")
    return True


# =======================================================
# MAIN
# =======================================================

def main():
    print("\n=== MODULE E LOADER (Improved Error Handling) ===\n")

    for table, filename in TABLES.items():
        path = os.path.join(CSV_FOLDER, filename)

        if not os.path.exists(path):
            errors[table] = "CSV file not found"
            print(f"✖ MISSING FILE: {path}")
            continue

        rows = read_csv(path)
        print(f"\nTable: {table} | Rows detected: {len(rows)}")

        success = insert_batches(table, rows)
        if not success:
            print(f"✖ FAILED to load table: {table}")

    # ===================================================
    # SUMMARY
    # ===================================================
    print("\n=================================")
    print("          LOAD SUMMARY           ")
    print("=================================\n")

    if errors:
        print("✖ LOADING FAILED — ERRORS FOUND:\n")
        for table, msg in errors.items():
            print(f"- {table}: {msg}")
        print("\n=== FIX ERRORS BEFORE CONTINUING ===\n")
    else:
        print("✔ ALL TABLES LOADED SUCCESSFULLY")
        print("\n=== DATA LOAD COMPLETE ===\n")


if __name__ == "__main__":
    main()

