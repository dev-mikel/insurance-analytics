import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

CONFIG_PATH = "output/config.json"
NORMALIZED_DIR = "output/normalized"


# ============================================================
# Helpers
# ============================================================

def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    with open(path, "r") as f:
        return json.load(f)


def load_csv(name):
    path = os.path.join(NORMALIZED_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing normalized dataset: {path}")
    return pd.read_csv(path)


def pct(v):
    return f"{v*100:.2f}%"


# ============================================================
# HIGH-LEVEL CHECK PRINTER
# ============================================================

def print_section(title):
    print(f"\n=== {title.upper()} ===")


def warn(msg):
    print(f"[WARN] {msg}")


def fail(msg):
    print(f"[FAIL] {msg}")


def ok(msg):
    print(f"[OK] {msg}")


# ============================================================
# MODULE C HEALTHCHECK
# ============================================================

def run():
    print("\n=== MODULE C – HEALTHCHECK v2 (ENTERPRISE) ===\n")

    cfg = load_json(CONFIG_PATH)

    # --- LOAD DIM / FACT TABLES ---
    dim_regions = load_csv("dim_regions.csv")
    dim_states = load_csv("dim_states.csv")
    dim_customers = load_csv("dim_customers.csv")
    fact_policies = load_csv("fact_policies.csv")
    fact_claims = load_csv("fact_claims.csv")
    fact_quotes = load_csv("fact_quotes.csv")
    fact_uw = load_csv("fact_uw_decisions.csv")
    fact_retention = load_csv("fact_retention.csv")
    fact_pricing = load_csv("fact_pricing_segments.csv")
    fact_lossdev = load_csv("fact_loss_development.csv")

    # ------------------------------------------------------------
    # 1. BASIC DIM/FACT INTEGRITY
    # ------------------------------------------------------------
    print_section("ROW COUNTS")

    if len(dim_customers) == cfg["portfolio"]["numCustomers"]:
        ok(f"dim_customers row count correct ({len(dim_customers)})")
    else:
        warn(f"dim_customers mismatch: {len(dim_customers)} vs {cfg['portfolio']['numCustomers']}")

    if len(fact_policies) == cfg["portfolio"]["expectedPolicies"]:
        ok(f"fact_policies row count correct ({len(fact_policies)})")
    else:
        warn(f"fact_policies mismatch: {len(fact_policies)} vs {cfg['portfolio']['expectedPolicies']}")

    if len(fact_quotes) == cfg["portfolio"]["expectedQuotes"]:
        ok("fact_quotes row count correct")
    else:
        warn(f"fact_quotes mismatch: {len(fact_quotes)} vs {cfg['portfolio']['expectedQuotes']}")

    # Claims tolerancia ±20%
    expected_claims = cfg["portfolio"]["expectedClaims"]
    actual_claims = len(fact_claims)
    if expected_claims * 0.80 <= actual_claims <= expected_claims * 1.20:
        ok(f"fact_claims ~ aligned ({actual_claims} rows)")
    else:
        warn(f"fact_claims out of range: expected~{expected_claims}, actual={actual_claims}")

    # ------------------------------------------------------------
    # 2. DUPLICATES / PRIMARY KEYS
    # ------------------------------------------------------------
    print_section("PRIMARY KEYS & DUPLICATES")

    if dim_customers["customer_id"].is_unique:
        ok("PK: customer_id unique")
    else:
        fail("Duplicate customer_id")

    if fact_policies["policy_id"].is_unique:
        ok("PK: policy_id unique")
    else:
        fail("Duplicate policy_id")

    if not fact_claims["claim_id"].is_unique:
        fail("Duplicate claim_id")

    if not fact_quotes["quote_id"].is_unique:
        warn("Duplicate quote_id — may indicate generation error")

    # ------------------------------------------------------------
    # 3. FOREIGN KEY INTEGRITY
    # ------------------------------------------------------------
    print_section("FOREIGN KEY INTEGRITY")

    cust_set = set(dim_customers["customer_id"])
    pol_set = set(fact_policies["policy_id"])

    # Policies → Customers
    bad_fk = fact_policies[~fact_policies["customer_id"].isin(cust_set)]
    if len(bad_fk) == 0:
        ok("Policies.customer_id → dim_customers OK")
    else:
        fail(f"Policies with invalid FK: {len(bad_fk)}")

    # Claims → Policies
    bad_fk = fact_claims[~fact_claims["policy_id"].isin(pol_set)]
    if len(bad_fk) == 0:
        ok("Claims.policy_id → fact_policies OK")
    else:
        fail(f"Claims with invalid FK: {len(bad_fk)}")

    # Quotes → Customers
    bad_fk = fact_quotes[~fact_quotes["customer_id"].isin(cust_set)]
    if len(bad_fk) == 0:
        ok("Quotes.customer_id → dim_customers OK")
    else:
        fail(f"Quotes with invalid FK: {len(bad_fk)}")

    # Quotes → Policies (target link)
    bad_fk = fact_quotes[~fact_quotes["policy_id_target"].isin(pol_set)]
    if len(bad_fk) == 0:
        ok("Quotes.policy_id_target → fact_policies OK")
    else:
        warn(f"Quotes with invalid target FK: {len(bad_fk)} (non-critical)")

    # UW Decisions → Quotes
    quote_set = set(fact_quotes["quote_id"])
    bad_fk = fact_uw[~fact_uw["quote_id"].isin(quote_set)]
    if len(bad_fk) == 0:
        ok("UW.quote_id → fact_quotes OK")
    else:
        fail(f"Invalid FK in UW decisions: {len(bad_fk)}")

    # ------------------------------------------------------------
    # 4. DATE INTEGRITY (CLAIMS)
    # ------------------------------------------------------------
    print_section("CLAIMS DATE INTEGRITY")

    def parse_date(s):
        try:
            return datetime.fromisoformat(str(s))
        except:
            return None

    invalid_count = 0
    for _, row in fact_claims.iterrows():
        occ = parse_date(row["occurrence_date"])
        rep = parse_date(row["report_date"])
        sett = parse_date(row["settlement_date"])
        if occ is None or rep is None or sett is None or not (occ <= rep <= sett):
            invalid_count += 1

    if invalid_count == 0:
        ok("All claim timelines valid")
    else:
        fail(f"{invalid_count} claims with invalid timelines")

    # ------------------------------------------------------------
    # 5. GEOGRAPHY MATCH (Region/state coherence)
    # ------------------------------------------------------------
    print_section("GEOGRAPHY CHECK")

    dim_states_map = dict(zip(dim_states["state"], dim_states["region"]))

    invalid_geo = 0
    for _, row in fact_policies.iterrows():
        st = row["state"]
        reg = row["region"]
        expected = dim_states_map.get(st)
        if expected != reg:
            invalid_geo += 1

    if invalid_geo == 0:
        ok("Region ↔ State mapping correct")
    else:
        fail(f"{invalid_geo} region/state mismatches in policies")

    # ------------------------------------------------------------
    # 6. PRODUCT MIX VALIDATION
    # ------------------------------------------------------------
    print_section("PRODUCT MIX CHECK")

    mix_cfg = cfg["productMix"]
    total = len(fact_policies)
    counts = fact_policies["product_line"].value_counts(normalize=True).to_dict()

    for lob, pct_expected in mix_cfg.items():
        actual = counts.get(lob, 0)
        print(f"LOB: {lob} → actual={pct(actual)}, expected={pct(pct_expected)}")
        if abs(actual - pct_expected) < 0.03:
            ok("Within tolerance")
        else:
            warn("Outside tolerance")

    # ------------------------------------------------------------
    # 7. CLAIMS ACTUARIAL SANITY (freq/sev)
    # ------------------------------------------------------------
    print_section("CLAIMS ACTUARIAL SANITY")

    # Frequency by policy_id
    freq = fact_claims.groupby("policy_id").size()
    avg_freq = freq.mean() if len(freq) > 0 else 0

    ok(f"Avg claims per policy: {avg_freq:.3f}")

    sev = fact_claims["claim_amount"].mean() if len(fact_claims) > 0 else 0
    ok(f"Avg severity: {sev:.2f}")

    # Negative or impossible values
    if (fact_claims["net_paid"] < 0).any():
        fail("Negative net_paid detected")
    else:
        ok("No negative net_paid")

    # Fraud score range
    invalid_fraud = fact_claims[(fact_claims["fraud_score"] < 0) | (fact_claims["fraud_score"] > 100)]
    if len(invalid_fraud) == 0:
        ok("Fraud score within [0,100]")
    else:
        fail(f"{len(invalid_fraud)} invalid fraud scores")

    # ------------------------------------------------------------
    # 8. UNDERWRITING FUNNEL
    # ------------------------------------------------------------
    print_section("UNDERWRITING FUNNEL")

    # Link quotes + UW
    df_merged = fact_quotes.merge(fact_uw, on="quote_id", how="left")

    quoted = (df_merged["quote_status"].isin(["QUOTED", "ACCEPTED", "BOUND"])).sum()
    accepted = (df_merged["quote_status"].isin(["ACCEPTED", "BOUND"])).sum()
    bound = (df_merged["quote_status"] == "BOUND").sum()

    print(f"quoted={quoted}, accepted={accepted}, bound={bound}")

    if bound <= accepted <= quoted:
        ok("Funnel mass preserved")
    else:
        fail("Funnel hierarchy broken")

    # ------------------------------------------------------------
    # 9. RETENTION SANITY
    # ------------------------------------------------------------
    print_section("RETENTION / CHURN")

    churn_rate = fact_retention["churn_flag"].mean()
    ok(f"Churn rate observed: {pct(churn_rate)}")

    # Should roughly align with baseProbability 8% (0.08) ± tolerance
    expected_churn = cfg["customerModel"]["churn"]["baseProbability"]
    if abs(churn_rate - expected_churn) < 0.03:
        ok("Churn rate within tolerance")
    else:
        warn("Churn rate outside expected window")

    # ------------------------------------------------------------
    # 10. PRICING SANITY
    # ------------------------------------------------------------
    print_section("PRICING CHECK")

    if (fact_pricing["our_average_premium"] <= 0).any():
        fail("Zero or negative premiums in pricing table")
    else:
        ok("Premiums > 0")

    if (fact_pricing["technically_required_premium"] <= 0).any():
        warn("Technically required premium <=0 (unexpected)")

    # Exposure sanity
    if fact_pricing["exposure_count"].min() <= 0:
        fail("Exposure_count <= 0 in pricing table")
    else:
        ok("Exposure_count > 0")

    # ------------------------------------------------------------
    # 11. LOSS DEVELOPMENT TRIANGLE SANITY
    # ------------------------------------------------------------
    print_section("LOSS DEVELOPMENT CHECK")

    if (fact_lossdev["incurred_losses"] < 0).any():
        fail("Negative incurred losses")
    else:
        ok("incurred_losses >= 0")

    if (fact_lossdev["paid_losses"] < 0).any():
        fail("Negative paid losses")
    else:
        ok("paid_losses >= 0")

    if (fact_lossdev["development_month"] < 0).any():
        fail("Negative development_month")
    else:
        ok("development_month >= 0")

    print("\n=== HEALTHCHECK NORMALIZER COMPLETE ===\n")


if __name__ == "__main__":
    run()

