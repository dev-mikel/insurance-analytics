"""
HEALTHCHECK — CONNECTION & BLANK PROJECT CHECKER
Objective:
1. Verify required environment variables for Supabase connection.
2. Verify PostgreSQL DB connection works.
3. Check if Supabase is EMPTY (no core tables exist yet).

This is used BEFORE running Module D.
"""

import os
import psycopg2


# ============================================================
# ENVIRONMENT CHECK
# ============================================================

def check_env_vars():
    print("1) Checking environment variables...")

    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_DB_URL"
    ]

    missing = []
    for var in required_vars:
        if os.getenv(var) is None:
            missing.append(var)

    if missing:
        print(f"✖ Missing environment variables: {missing}")
        return False

    print("✔ All required environment variables are present.")
    return True


# ============================================================
# POSTGRES CONNECTION CHECK
# ============================================================

def check_postgres_connection():
    print("\n2) Testing PostgreSQL connection (SUPABASE_DB_URL)...")

    try:
        conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        print("✔ PostgreSQL connection successful.")
        return True
    except Exception as e:
        print(f"✖ PostgreSQL connection failed: {e}")
        return False


# ============================================================
# CHECK IF SUPABASE IS EMPTY
# ============================================================

EXPECTED_TABLES = [
    "dim_regions",
    "dim_states",
    "dim_customers",
    "fact_policies",
    "fact_claims",
    "fact_quotes",
    "fact_uw_decisions",
    "fact_retention",
    "fact_pricing_segments",
    "fact_loss_development"
]

def table_exists(table):
    sql = """
        SELECT EXISTS(
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = %s
        );
    """
    conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
    cur = conn.cursor()
    cur.execute(sql, (table,))
    exists = cur.fetchone()[0]
    cur.close()
    conn.close()
    return exists


def check_if_database_is_empty():
    print("\n3) Checking if Supabase database is EMPTY...")

    existing = []

    for table in EXPECTED_TABLES:
        if table_exists(table):
            existing.append(table)

    if not existing:
        print("✔ Database is EMPTY — safe to run run_sql_table_schema.py")
        return True

    print(f"✖ Database already contains tables: {existing}")
    print("→ run_sql_table_schema.py should NOT be applied on a non-empty environment.")
    return False


# ============================================================
# MAIN EXECUTION
# ============================================================

def run():
    print("\n=== HEALTHCHECK 03 — MINIMAL STATE CHECK ===\n")

    env_ok = check_env_vars()
    if not env_ok:
        print("\n✖ FAIL — Fix environment variables before continuing.\n")
        return

    conn_ok = check_postgres_connection()
    if not conn_ok:
        print("\n✖ FAIL — Cannot connect to PostgreSQL.\n")
        return

    empty_ok = check_if_database_is_empty()

    print("\n=========================================")
    print("               SUMMARY                   ")
    print("=========================================\n")

    if env_ok and conn_ok and empty_ok:
        print("✔ PASS — Supabase for Module D DATA LOADER.")
    else:
        print("✖ FAIL — Environment not ready.")
        print("Fix issues above, then rerun this healthcheck.")

    print("\n=== HEALTHCHECK COMPLETE ===\n")


if __name__ == "__main__":
    run()

