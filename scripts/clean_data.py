"""
clean_data.py
Clears all data from tables WITHOUT dropping the tables or views.
Uses TRUNCATE TABLE via PostgreSQL direct connection.
"""

import os
import psycopg2

# Supabase DB URL (must include password, host, etc.)
DB_URL = os.getenv("SUPABASE_DB_URL")

if not DB_URL:
    raise Exception("Missing env variable SUPABASE_DB_URL")

# List of tables in dependency-safe order
TABLES = [
    "fact_loss_development",
    "fact_pricing_segments",
    "fact_retention",
    "fact_uw_decisions",
    "fact_quotes",
    "fact_claims",
    "fact_policies",
    "dim_customers",
    "dim_states",
    "dim_regions"
]


def clear_all_data():
    print("\n=== CLEANING TABLE DATA (ONLY CONTENT) ===\n")

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # TRUNCATE preserves schema, views, indexes, RLS rules, policies
    for table in TABLES:
        try:
            cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            print(f"✔ Cleared data from: {table}")
        except Exception as e:
            print(f"✖ ERROR cleaning {table}: {e}")

    cur.close()
    conn.close()

    print("\n=== CLEANING COMPLETE ===\n")


if __name__ == "__main__":
    clear_all_data()

