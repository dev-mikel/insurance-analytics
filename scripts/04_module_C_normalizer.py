import os
import json
import pandas as pd
import numpy as np

CONFIG_PATH = "output/config.json"
RAW_DIR = "output/raw"
OUT_DIR = "output/normalized"


# ============================================================
# Helpers
# ============================================================

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_config(path: str = CONFIG_PATH) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found at {path}. Run Module A first.")
    with open(path, "r") as f:
        return json.load(f)


def load_csv(name: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_csv(path)


def clean_empty(df: pd.DataFrame) -> pd.DataFrame:
    """Convert blanks and null-like strings into proper NaN."""
    return df.replace({
        "": np.nan,
        " ": np.nan,
        "null": np.nan,
        "NULL": np.nan
    })


def strip_all(df: pd.DataFrame) -> pd.DataFrame:
    """Remove whitespace from all object columns."""
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
    return df


def save_csv(df: pd.DataFrame, filename: str):
    path = os.path.join(OUT_DIR, filename)
    df.to_csv(path, index=False)
    print(f"✔ Saved {filename} ({len(df)} rows)")


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes", "y"])


# ============================================================
# Bucket functions (age, income, BMI)
# ============================================================

def age_to_bucket(age: float) -> str:
    if pd.isna(age):
        return "UNKNOWN"
    age = float(age)
    if age < 25: return "18-24"
    if age < 35: return "25-34"
    if age < 45: return "35-44"
    if age < 55: return "45-54"
    if age < 65: return "55-64"
    return "65+"


def income_to_bucket(x: float) -> str:
    if pd.isna(x):
        return "UNKNOWN"
    x = float(x)
    if x < 30000: return "0-30k"
    if x < 60000: return "30k-60k"
    if x < 100000: return "60k-100k"
    if x < 150000: return "100k-150k"
    return "150k+"


def bmi_to_bucket(b: float) -> str:
    if pd.isna(b):
        return "UNKNOWN"
    b = float(b)
    if b < 18.5: return "Underweight"
    if b < 25: return "Normal"
    if b < 30: return "Overweight"
    return "Obese"


# ============================================================
# DIM: REGIONS / STATES / CUSTOMERS
# ============================================================

def build_dim_regions(cfg: dict) -> pd.DataFrame:
    regions = cfg["geography"]["regions"]
    rows = []
    for region_name, states in regions.items():
        rows.append({
            "region": region_name,
            "num_states": len(states)
        })
    df = pd.DataFrame(rows)
    return strip_all(clean_empty(df))


def build_dim_states(cfg: dict) -> pd.DataFrame:
    regions = cfg["geography"]["regions"]
    rows = []
    for region_name, states in regions.items():
        for st in states:
            rows.append({
                "state": st,
                "region": region_name
            })
    df = pd.DataFrame(rows)
    return strip_all(clean_empty(df))


def normalize_dim_customers() -> pd.DataFrame:
    df = load_csv("customers.csv")
    df = strip_all(clean_empty(df))

    # Esperado desde Module B v2:
    # customer_id, age, gender, occupation, marital_status,
    # income, bmi, region, state, acquisition_channel

    # Tipos
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["income"] = pd.to_numeric(df["income"], errors="coerce")
    df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce")

    # Buckets
    df["age_group"] = df["age"].apply(age_to_bucket)
    df["income_bucket"] = df["income"].apply(income_to_bucket)
    df["bmi_bucket"] = df["bmi"].apply(bmi_to_bucket)

    # Mantener columnas clave para dim_customers;
    # puedes extender si quieres incluir gender, occupation, etc.
    dim = df[[
        "customer_id",
        "age",
        "income",
        "bmi",
        "age_group",
        "income_bucket",
        "bmi_bucket",
        "region",
        "state"
    ]].copy()

    return dim


# ============================================================
# FACT: POLICIES
# ============================================================

def normalize_fact_policies() -> pd.DataFrame:
    df = load_csv("policies.csv")
    df = strip_all(clean_empty(df))

    # Esperado desde Module B v2:
    # policy_id, customer_id, product_line, coverage_amount,
    # deductible, premium_annual, payment_frequency,
    # start_date, end_date, region, state, tenure_years

    # Tipos numéricos
    for col in ["coverage_amount", "deductible", "premium_annual", "tenure_years"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fechas
    # No necesitamos convertir a datetime para CSV final, pero
    # sí asegurarnos que exista y sea tipo string ISO.
    df["start_date"] = df["start_date"].astype(str)
    df["end_date"] = df["end_date"].astype(str)

    fact = df[[
        "policy_id",
        "customer_id",
        "product_line",
        "coverage_amount",
        "deductible",
        "premium_annual",
        "payment_frequency",
        "start_date",
        "end_date",
        "region",
        "state",
        "tenure_years"
    ]].copy()

    return fact


# ============================================================
# FACT: CLAIMS
# ============================================================

def normalize_fact_claims() -> pd.DataFrame:
    df = load_csv("claims.csv")
    df = strip_all(clean_empty(df))

    # Esperado desde Module B v2:
    # claim_id, policy_id, customer_id, product_line,
    # coverage_amount, claim_amount, deductible, net_paid,
    # occurrence_date, report_date, settlement_date,
    # region, state, fraud_score, legal_rep_flag

    numeric_cols = [
        "coverage_amount", "claim_amount", "deductible",
        "net_paid", "fraud_score"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # fechas como string ISO
    df["occurrence_date"] = df["occurrence_date"].astype(str)
    df["report_date"] = df["report_date"].astype(str)
    df["settlement_date"] = df["settlement_date"].astype(str)

    # legal_rep_flag → bool
    df["legal_rep_flag"] = to_bool(df["legal_rep_flag"])

    fact = df[[
        "claim_id",
        "policy_id",
        "customer_id",
        "product_line",
        "coverage_amount",
        "claim_amount",
        "deductible",
        "net_paid",
        "occurrence_date",
        "report_date",
        "settlement_date",
        "region",
        "state",
        "fraud_score",
        "legal_rep_flag"
    ]].copy()

    return fact


# ============================================================
# FACT: QUOTES
# ============================================================

def normalize_fact_quotes() -> pd.DataFrame:
    df = load_csv("quotes.csv")
    df = strip_all(clean_empty(df))

    # Esperado:
    # quote_id, customer_id, product_line, policy_id_target,
    # request_date, quote_date, quote_status, region, state

    df["request_date"] = df["request_date"].astype(str)
    df["quote_date"] = df["quote_date"].astype(str)

    fact = df[[
        "quote_id",
        "customer_id",
        "product_line",
        "policy_id_target",
        "request_date",
        "quote_date",
        "quote_status",
        "region",
        "state"
    ]].copy()

    return fact


# ============================================================
# FACT: UW DECISIONS
# ============================================================

def normalize_fact_uw_decisions() -> pd.DataFrame:
    df = load_csv("uw_decisions.csv")
    df = strip_all(clean_empty(df))

    # Esperado:
    # quote_id, stp_flag, accepted_flag, bound_flag,
    # expired_flag, decline_reason

    for col in ["stp_flag", "accepted_flag", "bound_flag", "expired_flag"]:
        df[col] = to_bool(df[col])

    fact = df[[
        "quote_id",
        "stp_flag",
        "accepted_flag",
        "bound_flag",
        "expired_flag",
        "decline_reason"
    ]].copy()

    return fact


# ============================================================
# FACT: RETENTION
# ============================================================

def normalize_fact_retention() -> pd.DataFrame:
    df = load_csv("retention.csv")
    df = strip_all(clean_empty(df))

    # Esperado:
    # customer_id, status, churn_flag, churn_reason,
    # churn_date, campaign_executed, campaign_type,
    # responded_flag, retained_after_campaign,
    # engagement_score, nps_score

    # Convertir flags a booleanos
    bool_cols = [
        "churn_flag", "campaign_executed",
        "responded_flag", "retained_after_campaign"
    ]
    for col in bool_cols:
        df[col] = to_bool(df[col])

    # Normalizar status: convertir todo a string, limpiar espacios y minúsculas
    df["status"] = df["status"].astype(str).str.strip().str.lower()

    # Regla de consistencia:
    # Si churn_flag == True, el status *debe* ser de un estado de cancelación.
    mask_churn = df["churn_flag"] == True
    df.loc[mask_churn, "status"] = "churned"

    # Regresar status a Title Case (estético, no obligatorio)
    df["status"] = df["status"].str.title()

    # Cast numéricos
    df["engagement_score"] = pd.to_numeric(df["engagement_score"], errors="coerce")
    df["nps_score"] = pd.to_numeric(df["nps_score"], errors="coerce")

    # churn_date se deja como string para que Supabase lo procese con formato compatible
    df["churn_date"] = df["churn_date"].astype(str)

    # Selección final de columnas
    fact = df[[
        "customer_id",
        "status",
        "churn_flag",
        "churn_reason",
        "churn_date",
        "campaign_executed",
        "campaign_type",
        "responded_flag",
        "retained_after_campaign",
        "engagement_score",
        "nps_score"
    ]].copy()

    return fact

# ============================================================
# FACT: PRICING SEGMENTS
# ============================================================

def normalize_fact_pricing_segments() -> pd.DataFrame:
    df = load_csv("pricing_segments.csv")
    df = strip_all(clean_empty(df))

    # Esperado:
    # segment_id, product_line, state,
    # technically_required_premium, our_average_premium,
    # market_average_premium, exposure_count

    num_cols = [
        "technically_required_premium",
        "our_average_premium",
        "market_average_premium",
        "exposure_count"
    ]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    fact = df[[
        "segment_id",
        "product_line",
        "state",
        "technically_required_premium",
        "our_average_premium",
        "market_average_premium",
        "exposure_count"
    ]].copy()

    return fact


# ============================================================
# FACT: LOSS DEVELOPMENT
# ============================================================

def normalize_fact_loss_development() -> pd.DataFrame:
    df = load_csv("loss_development.csv")
    df = strip_all(clean_empty(df))

    # Esperado:
    # claim_id, product_line, state,
    # development_month, incurred_losses, paid_losses

    df["development_month"] = pd.to_numeric(df["development_month"], errors="coerce")
    df["incurred_losses"] = pd.to_numeric(df["incurred_losses"], errors="coerce")
    df["paid_losses"] = pd.to_numeric(df["paid_losses"], errors="coerce")

    fact = df[[
        "claim_id",
        "product_line",
        "state",
        "development_month",
        "incurred_losses",
        "paid_losses"
    ]].copy()

    return fact


# ============================================================
# MAIN PIPELINE
# ============================================================

def run():
    print("\n=== MODULE C — NORMALIZER (RAW → NORMALIZED) ===\n")
    ensure_dir(OUT_DIR)

    cfg = load_config()

    # DIMs derivados de config
    dim_regions = build_dim_regions(cfg)
    dim_states = build_dim_states(cfg)
    dim_customers = normalize_dim_customers()

    # FACTs derivados de raw CSVs
    fact_policies = normalize_fact_policies()
    fact_claims = normalize_fact_claims()
    fact_quotes = normalize_fact_quotes()
    fact_uw = normalize_fact_uw_decisions()
    fact_retention = normalize_fact_retention()
    fact_pricing = normalize_fact_pricing_segments()
    fact_lossdev = normalize_fact_loss_development()

    # SAVE
    save_csv(dim_regions, "dim_regions.csv")
    save_csv(dim_states, "dim_states.csv")
    save_csv(dim_customers, "dim_customers.csv")

    save_csv(fact_policies, "fact_policies.csv")
    save_csv(fact_claims, "fact_claims.csv")
    save_csv(fact_quotes, "fact_quotes.csv")
    save_csv(fact_uw, "fact_uw_decisions.csv")
    save_csv(fact_retention, "fact_retention.csv")
    save_csv(fact_pricing, "fact_pricing_segments.csv")
    save_csv(fact_lossdev, "fact_loss_development.csv")

    print("\n=== NORMALIZATION COMPLETE — READY FOR HEALTHCHECK ===\n")


if __name__ == "__main__":
    run()

