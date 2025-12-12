"""
data_checker.py
Basic data quality checker for Supabase tables.

Checks:
1. Row counts
2. Null values in key fields
3. Basic foreign key relationships
4. Simple logical rules
"""

import os
import psycopg2

DB_URL = os.getenv("SUPABASE_DB_URL")

if not DB_URL:
    raise Exception("Missing SUPABASE_DB_URL environment variable.")


# ============================
# TABLE CONFIG
# ============================

TABLES = {
    "dim_regions": ["region"],
    "dim_states": ["state", "region"],
    "dim_customers": ["customer_id", "region", "state"],
    "fact_policies": ["policy_id", "customer_id", "product_line"],
    "fact_claims": ["claim_id", "policy_id", "occurrence_date"],
    "fact_quotes": ["quote_id", "customer_id", "product_line"],
    "fact_uw_decisions": ["quote_id"],
    "fact_retention": ["customer_id"],
    "fact_pricing_segments": ["segment_id", "state"],
    "fact_loss_development": ["claim_id", "development_month"]
}


# ============================
# HELPER FUNCTIONS
# ============================

def run_query(sql):
    """Executes a SQL query and returns the results."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(sql)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


def check_row_count(table):
    sql = f"SELECT COUNT(*) FROM {table};"
    return run_query(sql)[0][0]


def check_nulls(table, columns):
    """Return a dict: column → number of NULL values."""
    results = {}
    for col in columns:
        sql = f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL;"
        results[col] = run_query(sql)[0][0]
    return results


def fk_check(child_table, child_col, parent_table, parent_col):
    """
    Return number of orphan rows.
    Example:
    Policies customer_id should match customers customer_id
    """
    sql = f"""
        SELECT COUNT(*)
        FROM {child_table} c
        LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col}
        WHERE p.{parent_col} IS NULL;
    """
    return run_query(sql)[0][0]


# ============================
# MAIN CHECKER LOGIC
# ============================

def main():
    print("\n=== DATA CHECKER REPORT ===\n")

    # 1. Row Count Check
    print("1) ROW COUNTS")
    for table in TABLES:
        count = check_row_count(table)
        print(f"{table:<25} rows = {count}")
    print("")

    # 2. Null Checks
    print("2) NULL CHECKS (critical columns)")
    for table, cols in TABLES.items():
        nulls = check_nulls(table, cols)
        for col, n in nulls.items():
            status = "OK" if n == 0 else f"NULLS={n}"
            print(f"{table:<25} {col:<25} {status}")
    print("")

    # 3. Foreign Key Checks
    print("3) FOREIGN KEY CHECKS")

    checks = [
        ("fact_policies", "customer_id", "dim_customers", "customer_id"),
        ("fact_claims", "policy_id", "fact_policies", "policy_id"),
        ("fact_quotes", "customer_id", "dim_customers", "customer_id"),
        ("fact_uw_decisions", "quote_id", "fact_quotes", "quote_id"),
        ("fact_loss_development", "claim_id", "fact_claims", "claim_id"),
    ]

    for child, child_col, parent, parent_col in checks:
        missing = fk_check(child, child_col, parent, parent_col)
        status = "OK" if missing == 0 else f"ORPHANS={missing}"
        print(f"{child:<22} → {parent:<22} {status}")
    print("")

    # 4. Logical Rules
    print("4) BASIC LOGICAL CHECKS")

    # claims: occurrence <= report <= settlement
    logical_claims_sql = """
        SELECT COUNT(*)
        FROM fact_claims
        WHERE occurrence_date > report_date
           OR report_date > settlement_date;
    """
    invalid_claim_dates = run_query(logical_claims_sql)[0][0]
    print(f"fact_claims date logic: {'OK' if invalid_claim_dates == 0 else f'INVALID={invalid_claim_dates}'}")

    print("\n=== DATA CHECKER COMPLETE ===\n")


if __name__ == "__main__":
    main()

