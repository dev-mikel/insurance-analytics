# ============================================================
# MODULE C — NORMALIZER / BI PREP LAYER
# File: 04_module_C_normalizer.py
# Version: v3 FINAL (Contract-aligned)
#
# Purpose:
#   Transform RAW datasets into BI-ready star schema
#   Aligned with Module B generator and Module C healthcheck
# ============================================================

import os
import sys
import pandas as pd

RAW_DIR = "output/raw"
OUT_DIR = "output/normalized"

# ============================================================
# UTILITIES
# ============================================================

def fail(msg: str):
    print(f"[FAIL] {msg}")
    sys.exit(1)

def ok(msg: str):
    print(f"[OK] {msg}")

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def load_csv(name: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, name)
    if not os.path.exists(path):
        fail(f"Missing raw file: {name}")

    df = pd.read_csv(path)
    if df.empty:
        fail(f"{name} is empty")

    return df

def save_csv(df: pd.DataFrame, name: str):
    ensure_dir(OUT_DIR)
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False)
    ok(f"Saved {name} ({len(df)} rows)")


# ============================================================
# DIMENSION: TIME
# ============================================================

def build_dim_time(
    policies: pd.DataFrame,
    claims: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a daily time dimension covering all policy and claim dates.
    """

    dates = []

    for col in ["effective_date", "expiration_date"]:
        dates.append(pd.to_datetime(policies[col], errors="coerce"))

    for col in ["incident_date", "report_date"]:
        dates.append(pd.to_datetime(claims[col], errors="coerce"))

    min_date = min(s.min() for s in dates).date()
    max_date = max(s.max() for s in dates).date()

    rng = pd.date_range(min_date, max_date, freq="D")

    return pd.DataFrame({
        "date_key": rng.strftime("%Y%m%d").astype(int),
        "full_date": rng.date,
        "year": rng.year,
        "month": rng.month,
        "month_name": rng.strftime("%B"),
        "quarter": rng.quarter,
        "year_month": rng.strftime("%Y-%m"),
        "day_of_week": rng.weekday + 1,
        "is_weekend": rng.weekday >= 5,
    })


# ============================================================
# DIMENSIONS
# ============================================================

def build_dim_state(clients: pd.DataFrame) -> pd.DataFrame:
    """State / region lookup."""
    return (
        clients[["state_code", "region_code", "market_tier"]]
        .drop_duplicates()
        .sort_values("state_code")
        .reset_index(drop=True)
    )


def build_dim_clients(clients: pd.DataFrame) -> pd.DataFrame:
    """Client master dimension."""
    return clients.drop_duplicates("client_id")[[
        "client_id",
        "registration_year",
        "age",
        "gender",
        "customer_segment",
        "state_code",
        "region_code",
        "market_tier",
        "max_policies_allowed",
    ]]


def build_dim_products(policies: pd.DataFrame) -> pd.DataFrame:
    """Product dimension (LOB + plan)."""
    df = policies[["line_of_business", "plan_name"]].drop_duplicates().copy()

    df["product_key"] = (
        df["line_of_business"] + "_" + df["plan_name"]
    ).str.upper().str.replace(" ", "_")

    return df[["product_key", "line_of_business", "plan_name"]]


def build_dim_policies(policies: pd.DataFrame) -> pd.DataFrame:
    """Policy header dimension."""
    return policies.drop_duplicates("policy_id")[[
        "policy_id",
        "policy_number",
        "client_id",
        "state_code",
        "region_code",
        "is_renewal",
    ]]


# ============================================================
# FACT: POLICIES
# ============================================================

def build_fact_policies(policies: pd.DataFrame) -> pd.DataFrame:
    """Policy lifecycle fact table."""

    df = policies.copy()

    df["effective_date"] = pd.to_datetime(df["effective_date"])
    df["expiration_date"] = pd.to_datetime(df["expiration_date"])

    df["effective_date_key"] = df["effective_date"].dt.strftime("%Y%m%d").astype(int)
    df["expiration_date_key"] = df["expiration_date"].dt.strftime("%Y%m%d").astype(int)

    df["policy_year"] = df["effective_date"].dt.year
    df["policy_month"] = df["effective_date"].dt.month

    df["product_key"] = (
        df["line_of_business"] + "_" + df["plan_name"]
    ).str.upper().str.replace(" ", "_")

    return df[[
        "policy_id",
        "product_key",
        "state_code",
        "region_code",
        "effective_date_key",
        "expiration_date_key",
        "policy_year",
        "policy_month",
        "status",
        "risk_score",
        "monthly_premium",
        "annual_premium",
    ]]


# ============================================================
# FACT: CLAIMS
# ============================================================

def build_fact_claims(
    claims: pd.DataFrame,
    policies: pd.DataFrame,
) -> pd.DataFrame:
    """
    Claims fact table.

    Notes:
    - policy-grained
    - supports optional fraud_flag
    - settlement fields reserved for future use
    """

    df = claims.merge(
        policies[
            [
                "policy_id",
                "state_code",
                "region_code",
                "line_of_business",
                "plan_name",
            ]
        ],
        on="policy_id",
        how="left",
    )

    df["incident_date"] = pd.to_datetime(df["incident_date"])
    df["report_date"] = pd.to_datetime(df["report_date"])

    df["incident_date_key"] = df["incident_date"].dt.strftime("%Y%m%d").astype(int)
    df["report_date_key"] = df["report_date"].dt.strftime("%Y%m%d").astype(int)

    df["settlement_date_key"] = pd.Series([None] * len(df), dtype="Int64")
    df["days_to_settle"] = pd.Series([None] * len(df), dtype="Int64")

    df["product_key"] = (
        df["line_of_business"] + "_" + df["plan_name"]
    ).str.upper().str.replace(" ", "_")

    # Fraud flag hardening
    if "fraud_flag" not in df.columns:
        df["fraud_flag"] = False
    else:
        df["fraud_flag"] = df["fraud_flag"].fillna(False).astype(bool)

    return df[[
        "claim_id",
        "policy_id",
        "product_key",
        "line_of_business",
        "state_code",
        "region_code",
        "claim_type",
        "claim_status",
        "fraud_flag",
        "incident_date_key",
        "report_date_key",
        "settlement_date_key",
        "days_to_settle",
        "claim_amount_requested",
        "claim_amount_approved",
        "claim_amount_paid",
    ]]


# ============================================================
# FACT: EXPENSES
# ============================================================

def build_fact_expenses(expenses: pd.DataFrame) -> pd.DataFrame:
    """
    Operating expenses fact.

    Note:
    - expense_month normalized to first day of month
    """

    df = expenses.copy()

    df["date_key"] = (
        pd.to_datetime(df["expense_month"])
        .dt.strftime("%Y%m01")
        .astype(int)
    )

    return df[[
        "expense_id",
        "expense_category",
        "state_code",
        "region_code",
        "date_key",
        "expense_amount",
    ]]


# ============================================================
# FACT: TAXES (POLICY-GRAINED — FIXED)
# ============================================================

def build_fact_taxes(taxes: pd.DataFrame) -> pd.DataFrame:
    """
    Premium taxes fact table.

    Grain:
    - Policy (policy_id)

    Notes:
    - Single tax type (PREMIUM_TAX)
    - date_key intentionally NULL (monthly / annual reporting)
    """

    df = taxes.copy()

    df["tax_type"] = "PREMIUM_TAX"

    if "tax_base" not in df.columns:
        df["tax_base"] = (
            df["tax_amount"] / df["tax_rate"]
        ).replace([float("inf"), -float("inf")], None)

    df["date_key"] = pd.Series([None] * len(df), dtype="Int64")

    return df[[
        "tax_id",
        "policy_id",
        "tax_type",
        "state_code",
        "date_key",
        "tax_base",
        "tax_rate",
        "tax_amount",
    ]]


# ============================================================
# RUN
# ============================================================

def main():
    print("Module C — START")

    clients = load_csv("clients.csv")
    policies = load_csv("policies.csv")
    claims = load_csv("claims.csv")
    expenses = load_csv("expenses.csv")
    taxes = load_csv("taxes.csv")

    save_csv(build_dim_time(policies, claims), "dim_time.csv")
    save_csv(build_dim_state(clients), "dim_state.csv")
    save_csv(build_dim_clients(clients), "dim_clients.csv")
    save_csv(build_dim_products(policies), "dim_products.csv")
    save_csv(build_dim_policies(policies), "dim_policies.csv")

    save_csv(build_fact_policies(policies), "fact_policies.csv")
    save_csv(build_fact_claims(claims, policies), "fact_claims.csv")
    save_csv(build_fact_expenses(expenses), "fact_expenses.csv")
    save_csv(build_fact_taxes(taxes), "fact_taxes.csv")

    print("Module C — COMPLETE")


if __name__ == "__main__":
    main()
