# ============================================================
# MODULE D — SCHEMA HEALTHCHECK (SUPABASE)
# File: 08_healthcheck_schema.py
# Version: v5 FINAL (VIEW NAMES ALIGNED TO SQL)
# ============================================================

import os
import sys
import psycopg2
import requests

# ============================================================
# ENV
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
DB_URL = os.getenv("SUPABASE_DB_URL")

if not all([SUPABASE_URL, SERVICE_ROLE_KEY, ANON_KEY, DB_URL]):
    print("FAIL: Missing required environment variables")
    sys.exit(1)

SCHEMA = "public"

# ============================================================
# EXPECTED STRUCTURE (ALIGNED TO MODULE C + SQL VIEWS)
# ============================================================

EXPECTED_TABLES = {
    "dim_time",
    "dim_state",
    "dim_clients",
    "dim_products",
    "dim_policies",
    "fact_policies",
    "fact_claims",
    "fact_expenses",
    "fact_taxes",
}

# NOTE: names corrected to match actual SQL contracts
REQUIRED_VIEWS = {
    "vw_dash_exec_portfolio",
    "vw_dash_claims_loss",
    "vw_dash_operations_daily",
    "vw_dash_risk_daily"
}

# ============================================================
# UTILITIES
# ============================================================

def fail(msg: str):
    print(f"[FAIL] {msg}")
    sys.exit(1)

def ok(msg: str):
    print(f"[OK] {msg}")

def db_connect():
    try:
        return psycopg2.connect(DB_URL)
    except Exception as e:
        fail(f"DB connection failed: {e}")

def rest_check(view: str, api_key: str) -> int:
    url = f"{SUPABASE_URL}/rest/v1/{view}?select=*&limit=1"
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
    }
    r = requests.get(url, headers=headers)
    return r.status_code

# ============================================================
# CHECKS
# ============================================================

def check_tables(cur):
    print("\n=== 1) POSTGRES TABLES ===\n")

    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        """,
        (SCHEMA,),
    )
    existing = {r[0] for r in cur.fetchall()}

    missing = EXPECTED_TABLES - existing
    if missing:
        fail(f"Missing tables: {missing}")

    for t in sorted(EXPECTED_TABLES):
        ok(f"Table exists: {SCHEMA}.{t}")

def check_views(cur):
    print("\n=== 2) POSTGRES VIEWS ===\n")

    cur.execute(
        """
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = %s
        """,
        (SCHEMA,),
    )
    existing = {r[0] for r in cur.fetchall()}

    missing = REQUIRED_VIEWS - existing
    if missing:
        fail(f"Missing required views: {missing}")

    for v in sorted(REQUIRED_VIEWS):
        ok(f"View exists: {SCHEMA}.{v}")

def check_rest_service_role():
    print("\n=== 3) REST ACCESS (service_role) ===\n")

    for v in sorted(REQUIRED_VIEWS):
        code = rest_check(v, SERVICE_ROLE_KEY)
        if code == 200:
            ok(f"service_role CAN access {v}")
        else:
            fail(f"service_role CANNOT access {v} (HTTP {code})")

def check_rest_anon():
    print("\n=== 4) REST ACCESS (anon — MUST be blocked) ===\n")

    for v in sorted(REQUIRED_VIEWS):
        code = rest_check(v, ANON_KEY)
        if code in (401, 403):
            ok(f"anon blocked from {v}")
        else:
            fail(f"anon SHOULD NOT access {v} (HTTP {code})")

# ============================================================
# MAIN
# ============================================================

def main():
    print("\nMODULE D — SCHEMA HEALTHCHECK (SUPABASE v5)")
    print("======================================")

    conn = db_connect()
    cur = conn.cursor()

    check_tables(cur)
    check_views(cur)
    check_rest_service_role()
    check_rest_anon()

    cur.close()
    conn.close()

    print("\n======================================")
    print("SCHEMA HEALTHCHECK — PASSED")
    print("======================================\n")

if __name__ == "__main__":
    main()
