"""
HEALTHCHECK 07 — BI VIEW PERFORMANCE BENCHMARK
Evaluates performance of BI views used by Looker Studio.

Metrics collected:
1. Execution time (ms)
2. Row count
3. Column count
4. Approx result set size (rows × columns)
5. Query plan cost (from EXPLAIN ANALYZE)
6. Pass/Fail threshold for slow views

Uses direct PostgreSQL connection via SUPABASE_DB_URL.
"""

import os
import psycopg2
import time

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    raise Exception("Missing SUPABASE_DB_URL environment variable.")


# ============================================================
# CONFIGURATION
# ============================================================

BI_VIEWS = [
    "vw_loss_ratio",
    "vw_underwriting_funnel",
    "vw_churn"
]

# Thresholds (tune for portfolio)
MAX_EXECUTION_MS = 500       # ideal < 500ms per view
MAX_EXPLAIN_COST = 50000     # threshold for heavy execution plans


# ============================================================
# HELPERS
# ============================================================

def run_sql(query):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def execute_timed(query):
    """Runs a query and measures execution time in milliseconds."""
    start = time.time()
    rows = run_sql(query)
    end = time.time()
    elapsed_ms = round((end - start) * 1000, 2)
    return rows, elapsed_ms


def explain_analyze_cost(view):
    """Reads the cost from EXPLAIN ANALYZE output."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(f"EXPLAIN ANALYZE SELECT * FROM {view} LIMIT 5000;")
    plan = cur.fetchall()
    cur.close()
    conn.close()

    # Extract cost from first line
    first_line = plan[0][0] if plan else ""
    # Example: "Limit  (cost=0.00..123.45 rows=5000 width=50)"
    cost_value = None
    import re
    match = re.search(r"cost=\d+\.\d+\.\.(\d+\.\d+)", first_line)
    if match:
        cost_value = float(match.group(1))
    return cost_value, plan


# ============================================================
# MAIN HEALTHCHECK
# ============================================================

def run():
    print("\n=== HEALTHCHECK 07 — BI VIEW PERFORMANCE ===\n")

    results = []
    errors = []

    for view in BI_VIEWS:
        print(f"Evaluating view: {view}\n")

        # ----------------------------------------------------
        # 1. Count rows
        # ----------------------------------------------------
        try:
            rowcount = run_sql(f"SELECT COUNT(*) FROM {view};")[0][0]
            print(f"✔ Rowcount: {rowcount}")
        except Exception as e:
            print(f"✖ Failed to count rows for {view}: {e}")
            errors.append(f"{view} - rowcount failure")
            continue

        # ----------------------------------------------------
        # 2. Measure execution time
        # ----------------------------------------------------
        try:
            _, exec_ms = execute_timed(f"SELECT * FROM {view} LIMIT 5000;")
            print(f"✔ Execution time: {exec_ms} ms")
        except Exception as e:
            print(f"✖ Error measuring execution time for {view}: {e}")
            errors.append(f"{view} - execution failure")
            continue

        # ----------------------------------------------------
        # 3. Column count
        # ----------------------------------------------------
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {view} LIMIT 1;")
        col_count = len(cur.description)
        cur.close()
        conn.close()
        print(f"✔ Column count: {col_count}")

        # ----------------------------------------------------
        # 4. Approx data footprint
        # ----------------------------------------------------
        footprint = rowcount * col_count
        print(f"✔ Approx view footprint: {footprint} cell-values")

        # ----------------------------------------------------
        # 5. EXPLAIN ANALYZE cost
        # ----------------------------------------------------
        try:
            cost, plan = explain_analyze_cost(view)
            if cost:
                print(f"✔ Query cost (EXPLAIN ANALYZE): {cost}")
            else:
                print("⚠ Could not extract cost from execution plan.")
        except Exception as e:
            print(f"✖ Error analyzing query plan for {view}: {e}")
            errors.append(f"{view} - explain failure")
            continue

        # ----------------------------------------------------
        # 6. Save results
        # ----------------------------------------------------
        results.append({
            "view": view,
            "rows": rowcount,
            "columns": col_count,
            "exec_ms": exec_ms,
            "footprint": footprint,
            "cost": cost
        })

        print("\n-----------------------------------\n")

    # =======================================================
    # SUMMARY
    # =======================================================

    print("\n====================================")
    print("       BI VIEW PERFORMANCE SUMMARY  ")
    print("====================================\n")

    slow_views = [
        r for r in results
        if r["exec_ms"] > MAX_EXECUTION_MS or (r["cost"] and r["cost"] > MAX_EXPLAIN_COST)
    ]

    if errors:
        print("✖ FAIL — Errors occurred during the performance test:\n")
        for e in errors:
            print(f"- {e}")
    elif slow_views:
        print("⚠ WARNING — Some views are slow or heavy:\n")
        for v in slow_views:
            print(f"- {v['view']}: {v['exec_ms']} ms, cost={v['cost']}")
        print("\nRecommendation: Consider adding indexes or optimizing join logic.")
    else:
        print("✔ PASS — All views meet performance standards.\n")

    print("\n=== HEALTHCHECK 07 COMPLETE ===\n")


if __name__ == "__main__":
    run()

