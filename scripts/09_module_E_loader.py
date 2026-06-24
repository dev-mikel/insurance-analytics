"""
MODULE 09 — DATA LOADER (STAR SCHEMA) — v1 FINAL / HARD-BLINDED

Adds:
- Guarantees BOOLEAN compatibility with PostgreSQL
"""

import os
import psycopg2
import pandas as pd
import tempfile

# ============================================================
# ENV
# ============================================================

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    raise RuntimeError("Missing SUPABASE_DB_URL")

BASE_PATH = "output/normalized"

# ============================================================
# HELPERS
# ============================================================

def csv_path(table: str) -> str:
    path = os.path.join(BASE_PATH, f"{table}.csv")
    if not os.path.exists(path):
        raise RuntimeError(f"Missing CSV file: {path}")
    return path


def clean_fact_claims_csv(path: str) -> str:
    """
    Final defensive cleaning:
    - fraud_flag must be boolean-compatible
    """
    df = pd.read_csv(path)

    if "fraud_flag" in df.columns:
        df["fraud_flag"] = (
            df["fraud_flag"]
            .fillna(0)
            .apply(
                lambda x: 1
                if str(x).lower() in ("1", "true", "t", "yes")
                else 0
            )
            .astype(int)
        )

    tmp = tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False)
    df.to_csv(tmp.name, index=False)
    tmp.flush()
    return tmp.name


def copy(cur, sql: str, table: str):
    path = csv_path(table)

    # Special handling ONLY for fact_claims
    if table == "fact_claims":
        path = clean_fact_claims_csv(path)

    with open(path, "r", encoding="utf-8") as f:
        cur.copy_expert(sql, f)

# ============================================================
# MAIN LOAD
# ============================================================

def run():
    print("Module 09 v1 — START")

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    try:
        cur.execute("BEGIN;")

        print("Truncating fact tables...")
        cur.execute("""
            TRUNCATE
                public.fact_claims,
                public.fact_expenses,
                public.fact_taxes,
                public.fact_policies
            CASCADE;
        """)

        print("Truncating dimension tables...")
        cur.execute("""
            TRUNCATE
                public.dim_policies,
                public.dim_products,
                public.dim_clients,
                public.dim_state,
                public.dim_time
            CASCADE;
        """)

        print("Loading dimensions...")

        copy(cur, """
            COPY public.dim_time (
                date_key, full_date, year, month, month_name,
                quarter, year_month, day_of_week, is_weekend
            )
            FROM STDIN WITH CSV HEADER
        """, "dim_time")

        copy(cur, """
            COPY public.dim_state (
                state_code, region_code, market_tier
            )
            FROM STDIN WITH CSV HEADER
        """, "dim_state")

        copy(cur, """
            COPY public.dim_clients (
                client_id, registration_year, age, gender,
                customer_segment, state_code, region_code,
                market_tier, max_policies_allowed
            )
            FROM STDIN WITH CSV HEADER
        """, "dim_clients")

        copy(cur, """
            COPY public.dim_products (
                product_key, line_of_business, plan_name
            )
            FROM STDIN WITH CSV HEADER
        """, "dim_products")

        copy(cur, """
            COPY public.dim_policies (
                policy_id, policy_number, client_id,
                state_code, region_code, is_renewal
            )
            FROM STDIN WITH CSV HEADER
        """, "dim_policies")

        print("Loading fact tables...")

        copy(cur, """
            COPY public.fact_policies (
                policy_id, product_key, state_code, region_code,
                effective_date_key, expiration_date_key,
                policy_year, policy_month, status,
                risk_score, monthly_premium, annual_premium
            )
            FROM STDIN WITH CSV HEADER
        """, "fact_policies")

        copy(cur, """
            COPY public.fact_claims (
                claim_id, policy_id, product_key, line_of_business,
                state_code, region_code, claim_type, claim_status,
                fraud_flag, incident_date_key, report_date_key,
                settlement_date_key, days_to_settle,
                claim_amount_requested, claim_amount_approved,
                claim_amount_paid
            )
            FROM STDIN WITH CSV HEADER
        """, "fact_claims")

        copy(cur, """
            COPY public.fact_expenses (
                expense_id, expense_category, state_code,
                region_code, date_key, expense_amount
            )
            FROM STDIN WITH CSV HEADER
        """, "fact_expenses")

        copy(cur, """
    COPY public.fact_taxes (
        tax_id,
        policy_id,
        tax_type,
        state_code,
        date_key,
        tax_base,
        tax_rate,
        tax_amount
    )
    FROM STDIN WITH CSV HEADER
""", "fact_taxes")


        conn.commit()
        print("Module 09 v1 — COMPLETED SUCCESSFULLY")

    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Module 09 v1 FAILED: {e}")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run()
