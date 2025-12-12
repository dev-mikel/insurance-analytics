
"""
HEALTHCHECK — BUSINESS & ACTUARIAL KPI VALIDATION (v4)

GOAL:
Validate insurance data realism using ACTUARIAL sanity thresholds,
not rigid arbitrary values.

This healthcheck runs AFTER:
- Schema validation (HC #08)
- Loader validation (HC #10)
- Performance checks (HC #11)

This is a DEMO-oriented business sanity check.
Thresholds are indicative and documented as assumptions.

IMPORTANT:
- WARNINGS indicate unusual but possible scenarios
- ERRORS indicate highly improbable or impossible scenarios

Views used:
- vw_loss_ratio
- vw_underwriting_funnel
- vw_churn
- vw_pricing_adequacy
- vw_policy_frequency
- vw_executive_portfolio
"""

import os
import psycopg2

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    raise Exception("Missing SUPABASE_DB_URL environment variable")


# ============================================================
# Helper functions
# ============================================================

def run_sql_one(query):
    """Return first column of first row"""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(query)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def run_sql_row(query):
    """Return first row"""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(query)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def pct(part, total):
    """Safe percentage calculation"""
    if part is None or total is None or total == 0:
        return None
    return round(100.0 * part / total, 2)


def f2(x):
    """Format floats consistently (2 decimals)"""
    return "None" if x is None else format(float(x), ".2f")


# ============================================================
# MAIN HEALTHCHECK
# ============================================================

def run():
    print("\n=== HEALTHCHECK — BUSINESS & ACTUARIAL KPI SANITY (V4) ===\n")

    errors = []
    warnings = []

    # ========================================================
    # 1) LOSS RATIO — ACTUARIAL SANITY
    # ========================================================

    print("1) LOSS RATIO — ACTUARIAL SANITY\n")

    avg_lr = run_sql_one("""
        SELECT AVG(loss_ratio)
        FROM vw_loss_ratio
        WHERE loss_ratio IS NOT NULL;
    """)

    p90_lr = run_sql_one("""
        SELECT PERCENTILE_CONT(0.90)
        WITHIN GROUP (ORDER BY loss_ratio)
        FROM vw_loss_ratio
        WHERE loss_ratio IS NOT NULL;
    """)

    p99_lr = run_sql_one("""
        SELECT PERCENTILE_CONT(0.99)
        WITHIN GROUP (ORDER BY loss_ratio)
        FROM vw_loss_ratio
        WHERE loss_ratio IS NOT NULL;
    """)

    print(f"- Avg Loss Ratio: {f2(avg_lr)}")
    print(f"- P90 Loss Ratio: {f2(p90_lr)}")
    print(f"- P99 Loss Ratio: {f2(p99_lr)}")

    # --- Actuarial assumptions (DEMO) ---
    # Avg LR > 3.0  → unusual but possible → WARNING
    # P90 LR > 8.0  → heavy tail exposure → WARNING
    # P99 LR > 40.0 → extreme / data issue → ERROR

    if avg_lr is not None and avg_lr > 3.0:
        warnings.append("Avg Loss Ratio > 3.0 (unusual portfolio performance)")

    if p90_lr is not None and p90_lr > 8.0:
        warnings.append("P90 Loss Ratio > 8.0 (heavy tail risk detected)")

    if p99_lr is not None and p99_lr > 40.0:
        errors.append("P99 Loss Ratio > 40.0 (extreme outliers or data issue)")

    print("\n--------------------------------------------------\n")

    # ========================================================
    # 2) CLAIM FREQUENCY (POLICY LEVEL)
    # ========================================================

    print("2) CLAIM FREQUENCY — POLICY LEVEL\n")

    policy_count = run_sql_one("""
        SELECT COUNT(*) FROM vw_policy_frequency;
    """)

    policies_with_claims = run_sql_one("""
        SELECT COUNT(*) FROM vw_policy_frequency
        WHERE has_claim_flag = 1;
    """)

    freq = pct(policies_with_claims, policy_count)

    print(f"- Policies: {policy_count}")
    print(f"- Policies with claims: {policies_with_claims} ({freq}%)")

    if freq is not None and freq > 70:
        warnings.append("Claim frequency > 70% (very aggressive risk profile)")

    print("\n--------------------------------------------------\n")

    # ========================================================
    # 3) UNDERWRITING FUNNEL
    # ========================================================

    print("3) UNDERWRITING FUNNEL KPI\n")

    quoted = run_sql_one("""
        SELECT COUNT(*) FROM vw_underwriting_funnel
        WHERE quoted_flag = TRUE;
    """)

    bound = run_sql_one("""
        SELECT COUNT(*) FROM vw_underwriting_funnel
        WHERE bound_flag = TRUE;
    """)

    bind_rate = pct(bound, quoted)

    print(f"- Quoted: {quoted}")
    print(f"- Bound: {bound}")
    print(f"- Bind Rate: {bind_rate}%")

    if bind_rate is not None and bind_rate < 5:
        warnings.append("Bind rate < 5% (pricing or funnel friction)")

    if bind_rate is not None and bind_rate > 80:
        warnings.append("Bind rate > 80% (possible underpricing or selection bias)")

    print("\n--------------------------------------------------\n")

    # ========================================================
    # 4) CHURN & RETENTION (CUSTOMER LEVEL)
    # ========================================================

    print("4) CHURN & RETENTION KPI\n")

    total_customers = run_sql_one("""
        SELECT COUNT(DISTINCT customer_id) FROM vw_churn;
    """)

    churned_customers = run_sql_one("""
        SELECT COUNT(DISTINCT customer_id)
        FROM vw_churn
        WHERE churn_flag = TRUE;
    """)

    churn_rate = pct(churned_customers, total_customers)

    print(f"- Customers: {total_customers}")
    print(f"- Churned: {churned_customers}")
    print(f"- Churn Rate: {churn_rate}%")

    if churn_rate is not None and churn_rate > 40:
        warnings.append("Churn rate > 40% (retention issue or cohort effect)")

    print("\n--------------------------------------------------\n")

    # ========================================================
    # 5) PRICING ADEQUACY
    # ========================================================

    print("5) PRICING ADEQUACY KPI\n")

    avg_pricing_ratio = run_sql_one("""
        SELECT AVG(pricing_adequacy_ratio)
        FROM vw_pricing_adequacy
        WHERE pricing_adequacy_ratio IS NOT NULL;
    """)

    print(f"- Avg Pricing Adequacy Ratio: {f2(avg_pricing_ratio)}")

    if avg_pricing_ratio is None:
        warnings.append("Pricing adequacy ratio not computable (all NULL)")

    if avg_pricing_ratio is not None and avg_pricing_ratio < 0.7:
        warnings.append("Portfolio underpriced (avg < 0.7)")

    if avg_pricing_ratio is not None and avg_pricing_ratio > 1.5:
        warnings.append("Portfolio overpriced (avg > 1.5)")

    print("\n--------------------------------------------------\n")

    # ========================================================
    # 6) EXECUTIVE PORTFOLIO SANITY
    # ========================================================

    print("6) EXECUTIVE PORTFOLIO SANITY\n")

    negative_lr_cells = run_sql_one("""
        SELECT COUNT(*) FROM vw_executive_portfolio
        WHERE loss_ratio < 0;
    """)

    if negative_lr_cells and negative_lr_cells > 0:
        errors.append("Negative loss ratio detected in executive portfolio")

    print("- Executive portfolio checked")

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n==============================================")
    print("SUMMARY")
    print("==============================================\n")

    if errors:
        print("❌ ERRORS:")
        for e in errors:
            print(f"- {e}")

    if warnings:
        print("\n⚠ WARNINGS:")
        for w in warnings:
            print(f"- {w}")

    if not errors:
        print("\n✅ PASS — KPIs are actuarially sane and demo-ready")

    print("\n=== HEALTHCHECK COMPLETE ===\n")


if __name__ == "__main__":
    run()
