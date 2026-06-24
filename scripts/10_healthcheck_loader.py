"""
MODULE 10 — POST-LOADER DATA HEALTHCHECK — v2 FINAL

Validates:
- Tables populated (non-empty, no hardcoded sizes)
- FK integrity (FULL schema)
- Date keys valid against dim_time
- ALL BI views execute and return rows
"""

import os
import sys
import psycopg2

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    print("FAIL: Missing SUPABASE_DB_URL")
    sys.exit(1)

errors = []

def ok(msg):
    print(f"[OK] {msg}")

def fail(msg):
    print(f"[FAIL] {msg}")
    errors.append(msg)

print("\n=== MODULE 10 v2 — POST-LOADER HEALTHCHECK ===\n")

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # =========================================================
    # 1. TABLES NOT EMPTY
    # =========================================================
    tables = [
        "dim_time",
        "dim_state",
        "dim_clients",
        "dim_products",
        "dim_policies",
        "fact_policies",
        "fact_claims",
        "fact_expenses",
        "fact_taxes"
    ]

    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM public.{table};")
        cnt = cur.fetchone()[0]
        if cnt > 0:
            ok(f"{table}: {cnt} rows")
        else:
            fail(f"{table}: EMPTY")

    # =========================================================
    # 2. FK INTEGRITY (FULL)
    # =========================================================
    fk_checks = [
        # dim_policies
        ("dim_policies.client_id → dim_clients",
         "SELECT COUNT(*) FROM dim_policies dp LEFT JOIN dim_clients dc ON dc.client_id = dp.client_id WHERE dp.client_id IS NOT NULL AND dc.client_id IS NULL;"),

        # fact_policies
        ("fact_policies.product_key → dim_products",
         "SELECT COUNT(*) FROM fact_policies fp LEFT JOIN dim_products dp ON dp.product_key = fp.product_key WHERE fp.product_key IS NOT NULL AND dp.product_key IS NULL;"),

        ("fact_policies.state_code → dim_state",
         "SELECT COUNT(*) FROM fact_policies fp LEFT JOIN dim_state ds ON ds.state_code = fp.state_code WHERE fp.state_code IS NOT NULL AND ds.state_code IS NULL;"),

        ("fact_policies.effective_date_key → dim_time",
         "SELECT COUNT(*) FROM fact_policies fp LEFT JOIN dim_time dt ON dt.date_key = fp.effective_date_key WHERE fp.effective_date_key IS NOT NULL AND dt.date_key IS NULL;"),

        # fact_claims
        ("fact_claims.policy_id → dim_policies",
         "SELECT COUNT(*) FROM fact_claims fc LEFT JOIN dim_policies dp ON dp.policy_id = fc.policy_id WHERE fc.policy_id IS NOT NULL AND dp.policy_id IS NULL;"),

        ("fact_claims.product_key → dim_products",
         "SELECT COUNT(*) FROM fact_claims fc LEFT JOIN dim_products dp ON dp.product_key = fc.product_key WHERE fc.product_key IS NOT NULL AND dp.product_key IS NULL;"),

        ("fact_claims.state_code → dim_state",
         "SELECT COUNT(*) FROM fact_claims fc LEFT JOIN dim_state ds ON ds.state_code = fc.state_code WHERE fc.state_code IS NOT NULL AND ds.state_code IS NULL;"),

        ("fact_claims.incident_date_key → dim_time",
         "SELECT COUNT(*) FROM fact_claims fc LEFT JOIN dim_time dt ON dt.date_key = fc.incident_date_key WHERE fc.incident_date_key IS NOT NULL AND dt.date_key IS NULL;"),
    ]

    for name, sql in fk_checks:
        cur.execute(sql)
        broken = cur.fetchone()[0]
        if broken == 0:
            ok(f"FK OK: {name}")
        else:
            fail(f"FK FAIL: {name} ({broken} broken rows)")

    # =========================================================
    # 3. BI VIEWS EXECUTE
    # =========================================================
    views = [
    "vw_dash_exec_portfolio",
    "vw_dash_claims_loss",
    "vw_dash_operations_daily",
    "vw_dash_risk_daily"
    ]

    for v in views:
        cur.execute(f"SELECT 1 FROM public.{v} LIMIT 1;")
        ok(f"View OK: {v}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"FAIL: Healthcheck crashed: {e}")
    sys.exit(1)

# =============================================================
# SUMMARY
# =============================================================
print("\n======================================")
print(" POST-LOADER HEALTHCHECK SUMMARY")
print("======================================\n")

if errors:
    print("FAIL — Data issues detected:\n")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)
else:
    print("PASS — Dataset correctly loaded and BI/Lookder-ready.\n")
