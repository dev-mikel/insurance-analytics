# ============================================================
# MODULE C — HEALTHCHECK (NORMALIZED DATA)
# File: 05_healthcheck_normalized.py
# Version: FINAL v3 (Contract-aligned)
#
# Purpose:
#   Validate BI-ready normalized datasets produced by Module C
#   Enforces star-schema integrity and dimensional consistency
# ============================================================

import os
import sys
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

NORM_DIR = "output/normalized"

EXPECTED_FILES = {
    "dim_time.csv",
    "dim_state.csv",
    "dim_clients.csv",
    "dim_products.csv",
    "dim_policies.csv",
    "fact_policies.csv",
    "fact_claims.csv",
    "fact_expenses.csv",
    "fact_taxes.csv",
}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def fail(msg: str):
    print(f"[FAIL] {msg}")
    sys.exit(1)

def warn(msg: str):
    print(f"[WARN] {msg}")

def ok(msg: str):
    print(f"[OK] {msg}")

def load_csv(name: str) -> pd.DataFrame:
    path = os.path.join(NORM_DIR, name)
    if not os.path.exists(path):
        fail(f"Missing file: {name}")

    df = pd.read_csv(path)
    if df.empty:
        fail(f"{name} is empty")

    ok(f"{name}: loaded ({len(df)} rows)")
    return df

# ============================================================
# FILE PRESENCE CHECK
# ============================================================

def check_files():
    files = set(os.listdir(NORM_DIR))
    missing = EXPECTED_FILES - files
    if missing:
        fail(f"Missing normalized files: {missing}")

    ok("All normalized files present")

# ============================================================
# DIMENSION CHECKS
# ============================================================

def check_dim_time(df: pd.DataFrame):
    required = {
        "date_key",
        "full_date",
        "year",
        "month",
        "month_name",
        "quarter",
        "year_month",
        "day_of_week",
        "is_weekend",
    }

    if not required.issubset(df.columns):
        fail("dim_time missing required columns")

    if df["date_key"].duplicated().any():
        fail("dim_time date_key is not unique")

    ok("dim_time validation passed")


def check_dim_state(df: pd.DataFrame):
    required = {"state_code", "region_code", "market_tier"}

    if not required.issubset(df.columns):
        fail("dim_state missing required columns")

    if df["state_code"].duplicated().any():
        fail("Duplicate state_code in dim_state")

    ok("dim_state validation passed")


def check_dim_clients(df: pd.DataFrame, dim_state: pd.DataFrame):
    if df["client_id"].duplicated().any():
        fail("Duplicate client_id in dim_clients")

    if set(df["state_code"]) - set(dim_state["state_code"]):
        fail("dim_clients references unknown state_code")

    ok("dim_clients validation passed")


def check_dim_products(df: pd.DataFrame):
    if df["product_key"].duplicated().any():
        fail("Duplicate product_key in dim_products")

    ok("dim_products validation passed")


def check_dim_policies(
    df: pd.DataFrame,
    dim_clients: pd.DataFrame,
    dim_state: pd.DataFrame,
):
    if df["policy_id"].duplicated().any():
        fail("Duplicate policy_id in dim_policies")

    if set(df["client_id"]) - set(dim_clients["client_id"]):
        fail("dim_policies references unknown client_id")

    if set(df["state_code"]) - set(dim_state["state_code"]):
        fail("dim_policies references unknown state_code")

    ok("dim_policies validation passed")

# ============================================================
# FACT CHECKS
# ============================================================

def check_fact_policies(
    df: pd.DataFrame,
    dim_time: pd.DataFrame,
    dim_policies: pd.DataFrame,
    dim_products: pd.DataFrame,
    dim_state: pd.DataFrame,
):
    if set(df["policy_id"]) - set(dim_policies["policy_id"]):
        fail("fact_policies references unknown policy_id")

    if set(df["product_key"]) - set(dim_products["product_key"]):
        fail("fact_policies references unknown product_key")

    if set(df["state_code"]) - set(dim_state["state_code"]):
        fail("fact_policies references unknown state_code")

    if set(df["effective_date_key"]) - set(dim_time["date_key"]):
        fail("fact_policies has invalid effective_date_key")

    # Expiration date may exceed dim_time (allowed long-tail)
    missing_exp = set(df["expiration_date_key"]) - set(dim_time["date_key"])
    if missing_exp:
        warn(
            f"{len(missing_exp)} expiration_date_key outside dim_time range (allowed)"
        )

    ok("fact_policies validation passed")


def check_fact_claims(
    df: pd.DataFrame,
    dim_policies: pd.DataFrame,
    dim_products: pd.DataFrame,
    dim_state: pd.DataFrame,
    dim_time: pd.DataFrame,
):
    if set(df["policy_id"]) - set(dim_policies["policy_id"]):
        fail("fact_claims references unknown policy_id")

    if set(df["product_key"]) - set(dim_products["product_key"]):
        fail("fact_claims references unknown product_key")

    if set(df["state_code"]) - set(dim_state["state_code"]):
        fail("fact_claims references unknown state_code")

    for col in ["incident_date_key", "report_date_key"]:
        if set(df[col]) - set(dim_time["date_key"]):
            fail(f"fact_claims has invalid {col}")

    # Settlement date intentionally nullable / future-proof
    valid = df["settlement_date_key"].dropna().astype(int)
    missing = set(valid) - set(dim_time["date_key"])
    if missing:
        warn(
            f"{len(missing)} settlement_date_key outside dim_time (allowed)"
        )

    ok("fact_claims validation passed")


def check_fact_expenses(
    df: pd.DataFrame,
    dim_time: pd.DataFrame,
    dim_state: pd.DataFrame,
):
    if set(df["date_key"]) - set(dim_time["date_key"]):
        fail("fact_expenses has invalid date_key")

    if set(df["state_code"]) - set(dim_state["state_code"]):
        fail("fact_expenses references unknown state_code")

    if (df["expense_amount"] < 0).any():
        fail("Negative expense_amount in fact_expenses")

    ok("fact_expenses validation passed")


def check_fact_taxes(
    df: pd.DataFrame,
    dim_policies: pd.DataFrame,
    dim_state: pd.DataFrame,
):
    """
    fact_taxes:
    - policy-grained
    - date_key intentionally NULL
    """

    if set(df["policy_id"]) - set(dim_policies["policy_id"]):
        fail("fact_taxes references unknown policy_id")

    if set(df["state_code"]) - set(dim_state["state_code"]):
        fail("fact_taxes references unknown state_code")

    if (df["tax_amount"] < 0).any():
        fail("Negative tax_amount in fact_taxes")

    ok("fact_taxes validation passed")

# ============================================================
# SANITY CHECKS
# ============================================================

def sanity_checks(
    fact_policies: pd.DataFrame,
    fact_claims: pd.DataFrame,
):
    ratio = len(fact_claims) / max(len(fact_policies), 1)

    if ratio < 0.03 or ratio > 0.80:
        warn(f"Claims / Policies ratio unusual: {ratio:.2f}")

    ok("Sanity checks completed")

# ============================================================
# MAIN
# ============================================================

def main():
    print("HealthCheck Module C — START")

    if not os.path.exists(NORM_DIR):
        fail("output/normalized directory not found")

    check_files()

    dim_time = load_csv("dim_time.csv")
    dim_state = load_csv("dim_state.csv")
    dim_clients = load_csv("dim_clients.csv")
    dim_products = load_csv("dim_products.csv")
    dim_policies = load_csv("dim_policies.csv")

    fact_policies = load_csv("fact_policies.csv")
    fact_claims = load_csv("fact_claims.csv")
    fact_expenses = load_csv("fact_expenses.csv")
    fact_taxes = load_csv("fact_taxes.csv")

    check_dim_time(dim_time)
    check_dim_state(dim_state)
    check_dim_clients(dim_clients, dim_state)
    check_dim_products(dim_products)
    check_dim_policies(dim_policies, dim_clients, dim_state)

    check_fact_policies(
        fact_policies,
        dim_time,
        dim_policies,
        dim_products,
        dim_state,
    )
    check_fact_claims(
        fact_claims,
        dim_policies,
        dim_products,
        dim_state,
        dim_time,
    )
    check_fact_expenses(fact_expenses, dim_time, dim_state)
    check_fact_taxes(fact_taxes, dim_policies, dim_state)

    sanity_checks(fact_policies, fact_claims)

    print("HealthCheck Module C — PASSED")

if __name__ == "__main__":
    main()
