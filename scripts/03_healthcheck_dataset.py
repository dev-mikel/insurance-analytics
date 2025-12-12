import os
import csv
import json
from datetime import datetime


CONFIG_PATH = "output/config.json"
RAW_DIR = "output/raw"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError("Config file missing. Run Module A first.")
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def load_csv(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing dataset: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def check_exists_and_non_empty(name, rows, min_expected=1):
    if rows is None:
        return f"[FAIL] {name}: file not loaded"
    if len(rows) < min_expected:
        return f"[FAIL] {name}: too few rows ({len(rows)})"
    return f"[OK] {name}: {len(rows)} rows"


def pct(n: float) -> str:
    return f"{n*100:.2f}%"


def run_healthcheck():
    print("\n=== Module B — HealthCheck v1.0 ===\n")

    cfg = load_config()

    # Expected values
    expected_policies = cfg["portfolio"]["expectedPolicies"]
    expected_quotes = cfg["portfolio"]["expectedQuotes"]
    expected_claims = cfg["portfolio"]["expectedClaims"]
    expected_customers = cfg["portfolio"]["numCustomers"]
    claim_rate_annual = cfg["portfolio"]["claimRateAnnual"]

    # Load datasets
    customers = load_csv(os.path.join(RAW_DIR, "customers.csv"))
    policies = load_csv(os.path.join(RAW_DIR, "policies.csv"))
    quotes = load_csv(os.path.join(RAW_DIR, "quotes.csv"))
    uw = load_csv(os.path.join(RAW_DIR, "uw_decisions.csv"))
    claims = load_csv(os.path.join(RAW_DIR, "claims.csv"))

    # -----------------------------------------------------
    # 1. Quick existence & row checks
    # -----------------------------------------------------
    print(check_exists_and_non_empty("Customers", customers, expected_customers))
    print(check_exists_and_non_empty("Policies", policies, expected_policies))
    print(check_exists_and_non_empty("Quotes", quotes, expected_quotes))
    print(check_exists_and_non_empty("UW Decisions", uw, expected_quotes))
    print(check_exists_and_non_empty("Claims", claims, 1))

    # -----------------------------------------------------
    # 2. POLICY COUNT CHECK
    # -----------------------------------------------------
    print("\n[CHECK] Policy count alignment")
    if len(policies) == expected_policies:
        print(f"[OK] Policies = expectedPolicies ({expected_policies})")
    else:
        print(f"[WARN] Policies mismatch: {len(policies)} vs {expected_policies}")

    # -----------------------------------------------------
    # 3. QUOTE COUNT CHECK
    # -----------------------------------------------------
    print("\n[CHECK] Quote count alignment")
    if len(quotes) == expected_quotes:
        print(f"[OK] Quotes = expectedQuotes ({expected_quotes})")
    else:
        print(f"[WARN] Quotes mismatch: {len(quotes)} vs {expected_quotes}")

    # -----------------------------------------------------
    # 4. CLAIM COUNT CHECK
    # -----------------------------------------------------
    print("\n[CHECK] Claim count statistical alignment")

    actual_claims = len(claims)
    expected_total = expected_claims

    lower = expected_total * 0.80
    upper = expected_total * 1.20

    print(f"Expected claims ≈ {expected_total}")
    print(f"Actual claims = {actual_claims}")

    if lower <= actual_claims <= upper:
        print("[OK] Claims within acceptable statistical range")
    else:
        print("[WARN] Claims out of expected range (±20%)")

    # -----------------------------------------------------
    # 5. CLAIM TIMELINE VALIDATION
    # -----------------------------------------------------
    print("\n[CHECK] Claims date integrity (occ ≤ report ≤ settlement)")
    invalid_dates = 0
    for cl in claims:
        occ = datetime.fromisoformat(cl["occurrence_date"])
        rep = datetime.fromisoformat(cl["report_date"])
        sett = datetime.fromisoformat(cl["settlement_date"])
        if not (occ <= rep <= sett):
            invalid_dates += 1

    if invalid_dates == 0:
        print("[OK] All claim timelines valid")
    else:
        print(f"[FAIL] {invalid_dates} claims have inconsistent dates")

    # -----------------------------------------------------
    # 6. REGION DISTRIBUTION CHECK
    # -----------------------------------------------------
    print("\n[CHECK] Region distribution vs config")
    region_cfg = cfg["geography"]["regionDistribution"]
    region_counts = {k: 0 for k in region_cfg.keys()}

    for c in customers:
        region_counts[c["region"]] += 1

    total = len(customers)
    for r, expected_pct in region_cfg.items():
        actual_pct = region_counts[r] / total
        print(f"  - {r}: actual={pct(actual_pct)}, expected={pct(expected_pct)}")
        if abs(actual_pct - expected_pct) < 0.03:  # 3% tolerance
            print("    [OK]")
        else:
            print("    [WARN] Outside tolerance")

    # -----------------------------------------------------
    # 7. PRODUCT MIX CHECK
    # -----------------------------------------------------
    print("\n[CHECK] Product mix vs config")
    mix_cfg = cfg["productMix"]
    mix_counts = {k: 0 for k in mix_cfg.keys()}

    for p in policies:
        mix_counts[p["product_line"]] += 1

    total = len(policies)

    for lob, expected_pct in mix_cfg.items():
        actual_pct = mix_counts[lob] / total
        print(f"  - {lob}: actual={pct(actual_pct)}, expected={pct(expected_pct)}")
        if abs(actual_pct - expected_pct) < 0.03:
            print("    [OK]")
        else:
            print("    [WARN] Outside tolerance")

    # -----------------------------------------------------
    # 8. FRAUD SCORE RANGE CHECK
    # -----------------------------------------------------
    print("\n[CHECK] Fraud score range")
    invalid_fraud = sum(1 for cl in claims if not (0 <= float(cl["fraud_score"]) <= 100))
    if invalid_fraud == 0:
        print("[OK] Fraud scores within [0, 100]")
    else:
        print(f"[FAIL] {invalid_fraud} invalid fraud scores")

    # -----------------------------------------------------
    # 9. UW FUNNEL CONSISTENCY
    # -----------------------------------------------------
    print("\n[CHECK] UW funnel consistency (bound ≤ accepted ≤ quoted)")

    quoted = sum(1 for q in quotes if q["quote_status"] in ("QUOTED", "ACCEPTED", "BOUND"))
    accepted = sum(1 for q in quotes if q["quote_status"] in ("ACCEPTED", "BOUND"))
    bound = sum(1 for q in quotes if q["quote_status"] == "BOUND")

    print(f"Quoted:   {quoted}")
    print(f"Accepted: {accepted}")
    print(f"Bound:    {bound}")

    if bound <= accepted <= quoted:
        print("[OK] Funnel mass preserved")
    else:
        print("[FAIL] Funnel hierarchy broken")

    # -----------------------------------------------------
    # 10. PREMIUM & COVERAGE SANITY
    # -----------------------------------------------------
    print("\n[CHECK] Coverage and premium sanity")

    bad_cov = sum(1 for p in policies if int(p["coverage_amount"]) <= 0)
    bad_prem = sum(1 for p in policies if float(p["premium_annual"]) <= 0)

    if bad_cov == 0 and bad_prem == 0:
        print("[OK] No non-positive coverage or premiums")
    else:
        print(f"[FAIL] coverage_errors={bad_cov}, premium_errors={bad_prem}")

    print("\n=== HealthCheck Completed ===\n")


if __name__ == "__main__":
    run_healthcheck()

