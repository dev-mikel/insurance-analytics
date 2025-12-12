"""
08_healthcheck_schema.py

Validates:
- Required tables exist
- Required analytical views exist
- Views are accessible via Supabase REST
- Permissions (authenticated / service_role)
"""

import os
import sys
import requests
import psycopg2

# ============================================================
# ENV
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
DB_URL = os.getenv("SUPABASE_DB_URL")

if not all([SUPABASE_URL, SERVICE_ROLE_KEY, ANON_KEY, DB_URL]):
    print("❌ Missing environment variables")
    sys.exit(1)

# ============================================================
# EXPECTED OBJECTS
# ============================================================

TABLES = [
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

VIEWS = [
    "vw_loss_ratio",
    "vw_underwriting_funnel",
    "vw_churn",
    "vw_pricing_adequacy",
    "vw_policy_frequency",
    "vw_executive_portfolio"
]

# ============================================================
# HELPERS
# ============================================================

def hdr(key):
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Range": "0-1"
    }

def ok(msg):
    print(f"✔ OK: {msg}")

def fail(msg):
    print(f"❌ FAIL: {msg}")
    errors.append(msg)

errors = []

# ============================================================
# 1. POSTGRES OBJECT EXISTENCE
# ============================================================

print("\n=== 1) POSTGRES OBJECT EXISTENCE ===\n")

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Tables
    cur.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public';
    """)
    existing_tables = {r[0] for r in cur.fetchall()}

    for t in TABLES:
        if t in existing_tables:
            ok(f"Table exists: {t}")
        else:
            fail(f"Missing table: {t}")

    # Views
    cur.execute("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public';
    """)
    existing_views = {r[0] for r in cur.fetchall()}

    for v in VIEWS:
        if v in existing_views:
            ok(f"View exists: {v}")
        else:
            fail(f"Missing view: {v}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ PostgreSQL error: {e}")
    sys.exit(1)

# ============================================================
# 2. REST ACCESS — service_role
# ============================================================

print("\n=== 2) REST ACCESS — service_role ===\n")

for v in VIEWS:
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/{v}?select=*",
        headers=hdr(SERVICE_ROLE_KEY),
        timeout=10
    )

    if r.status_code in (200, 206):
        ok(f"service_role can read {v}")
    else:
        fail(f"service_role CANNOT read {v} (HTTP {r.status_code})")

# ============================================================
# 3. REST ACCESS — anon (MUST BE BLOCKED)
# ============================================================

print("\n=== 3) REST ACCESS — anon ===\n")

for v in VIEWS:
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/{v}?select=*",
        headers=hdr(ANON_KEY),
        timeout=10
    )

    if r.status_code in (401, 403):
        ok(f"anon blocked from {v}")
    else:
        fail(f"anon SHOULD NOT access {v} (HTTP {r.status_code})")

# ============================================================
# SUMMARY
# ============================================================

print("\n======================================")
print("        SCHEMA HEALTHCHECK SUMMARY     ")
print("======================================\n")

if errors:
    print("❌ FAIL — Issues detected:\n")
    for e in errors:
        print(f"- {e}")
    print("\nFix schema before proceeding.\n")
    sys.exit(1)
else:
    print("✔ PASS — Schema & BI views are valid.")
    print("✔ Ready for loaders, BI and dashboards.\n")
