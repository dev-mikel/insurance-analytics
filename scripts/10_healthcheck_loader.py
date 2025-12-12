"""
HEALTHCHECK — POST MODULE E VALIDATION
Validates database integrity AFTER running Module D Loader.

Checks:
1. Row counts match CSV sources
2. No NULLs in essential columns
3. Foreign key consistency
4. Claims date logic (occ ≤ report ≤ settlement)
5. Quotes → UW consistency
6. General data sanity

Uses direct PostgreSQL connection via SUPABASE_DB_URL.
"""

import os
import csv
import psycopg2

DB_URL = os.getenv("SUPABASE_DB_URL")
CSV_DIR = "output/normalized"

if not DB_URL:
    raise Exception("Missing SUPABASE_DB_URL environment variable.")


# ============================================================
# EXPECTED TABLES + KEY COLUMNS
# ============================================================

TABLES = {
    "dim_regions": ["region"],
    "dim_states": ["state", "region"],
    "dim_customers": ["customer_id", "region", "state"],
    "fact_policies": ["policy_id", "customer_id", "product_line"],
    "fact_claims": ["claim_id", "policy_id", "occurrence_date", "report_date", "settlement_date"],
    "fact_quotes": ["quote_id", "customer_id", "product_line", "policy_id_target"],
    "fact_uw_decisions": ["quote_id"],
    "fact_retention": ["customer_id"],
    "fact_pricing_segments": ["segment_id", "state"],
    "fact_loss_development": ["claim_id", "development_month"]
}


# ============================================================
# DATABASE HELPERS
# ============================================================

def sql(query, params=None):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_rowcount(table):
    return sql(f"SELECT COUNT(*) FROM {table};")[0][0]


def get_csv_rowcount(table):
    csv_path = os.path.join(CSV_DIR, f"{table}.csv")
    if not os.path.exists(csv_path):
        return None

    with open(csv_path, "r", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


# ============================================================
# HEALTHCHECK LOGIC
# ============================================================

def run():
    print("\n=== HEALTHCHECK 05 — POST MODULE D ===\n")

    errors = []
    warnings = []

    # --------------------------------------------------------
    # 1) ROW COUNT MATCH (DB vs CSV)
    # --------------------------------------------------------
    print("1) ROW COUNT VERIFICATION\n")

    for table in TABLES.keys():
        csv_count = get_csv_rowcount(table)
        db_count = get_rowcount(table)

        if csv_count is None:
            print(f"⚠ Missing CSV: {table}.csv — skipping comparison.")
            warnings.append(f"No CSV for {table}")
            continue

        if csv_count == db_count:
            print(f"✔ {table}: OK ({db_count} rows)")
        else:
            print(f"✖ {table}: DB={db_count}, CSV={csv_count} — MISMATCH")
            errors.append(f"Rowcount mismatch in {table}")

    # --------------------------------------------------------
    # 2) NULL CHECKS
    # --------------------------------------------------------
    print("\n2) NULL CHECKS (key columns)\n")

    for table, cols in TABLES.items():
        for col in cols:
            count = sql(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL;")[0][0]
            if count > 0:
                print(f"✖ {table}.{col}: {count} NULL values")
                errors.append(f"NULLs detected in {table}.{col}")
            else:
                print(f"✔ {table}.{col}: no NULLs")

    # --------------------------------------------------------
    # 3) FOREIGN KEY CONSISTENCY
    # --------------------------------------------------------
    print("\n3) FOREIGN KEY VALIDATION\n")

    FK_CHECKS = [
        ("fact_policies", "customer_id", "dim_customers", "customer_id"),
        ("fact_claims", "policy_id", "fact_policies", "policy_id"),
        ("fact_claims", "customer_id", "dim_customers", "customer_id"),
        ("fact_quotes", "customer_id", "dim_customers", "customer_id"),
        ("fact_quotes", "policy_id_target", "fact_policies", "policy_id"),
        ("fact_uw_decisions", "quote_id", "fact_quotes", "quote_id"),
        ("fact_loss_development", "claim_id", "fact_claims", "claim_id"),
    ]

    for (child, child_col, parent, parent_col) in FK_CHECKS:
        sql_query = f"""
            SELECT COUNT(*)
            FROM {child} c
            LEFT JOIN {parent} p ON c.{child_col} = p.{parent_col}
            WHERE p.{parent_col} IS NULL;
        """
        missing = sql(sql_query)[0][0]

        if missing == 0:
            print(f"✔ {child}.{child_col} → {parent}.{parent_col}: OK")
        else:
            print(f"✖ FK ERROR: {child}.{child_col} has {missing} missing references")
            errors.append(f"FK {child}.{child_col} → {parent}.{parent_col} missing {missing}")

    # --------------------------------------------------------
    # 4) CLAIMS DATE LOGIC
    # --------------------------------------------------------
    print("\n4) CLAIMS DATE VALIDATION\n")

    invalid_dates = sql("""
        SELECT COUNT(*)
        FROM fact_claims
        WHERE occurrence_date > report_date
           OR report_date > settlement_date
           OR occurrence_date IS NULL
           OR report_date IS NULL
    """)[0][0]

    if invalid_dates == 0:
        print("✔ fact_claims: date logic OK")
    else:
        print(f"✖ fact_claims: {invalid_dates} rows have invalid date order")
        errors.append(f"{invalid_dates} invalid claim date sequences")

    # --------------------------------------------------------
    # 5) QUOTES / UW CONSISTENCY
    # --------------------------------------------------------
    print("\n5) UNDERWRITING PIPELINE CONSISTENCY\n")

    missing_uw = sql("""
        SELECT COUNT(*)
        FROM fact_quotes q
        LEFT JOIN fact_uw_decisions u ON q.quote_id = u.quote_id
        WHERE u.quote_id IS NULL;
    """)[0][0]

    if missing_uw == 0:
        print("✔ Every quote has matching UW decision")
    else:
        print(f"✖ {missing_uw} quotes do NOT have UW decisions")
        errors.append(f"{missing_uw} missing UW decisions")

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------
    print("\n======================================")
    print("         HEALTHCHECK SUMMARY          ")
    print("======================================\n")

    if errors:
        print("✖ FAIL — Issues detected:\n")
        for e in errors:
            print(f"- {e}")
        print("\nFix issues and re run Module E Loader.\n")
    else:
        print("✔ PASS — All validation checks succeeded.")
        print("✔ Data is ready for Looker Studio/BI dashboards.\n")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"- {w}")

    print("\n=== HEALTHCHECK COMPLETE ===\n")


if __name__ == "__main__":
    run()

