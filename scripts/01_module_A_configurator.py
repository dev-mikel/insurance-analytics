import json
import os
import hashlib
import random
from datetime import datetime, timezone

# =====================================================
# CLI Helper Functions
# =====================================================

def ask_integer(message, default=None, min_value=None, max_value=None):
    """Ask for an integer with optional min/max and default."""
    while True:
        raw = input(f"{message} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            value = int(raw)
            if min_value is not None and value < min_value:
                print(f"Value must be >= {min_value}")
                continue
            if max_value is not None and value > max_value:
                print(f"Value must be <= {max_value}")
                continue
            return value
        except ValueError:
            print("Invalid integer value.")


def ask_float(message, default=None, min_value=None, max_value=None):
    """Ask for a float with optional min/max and default."""
    while True:
        raw = input(f"{message} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            value = float(raw)
            if min_value is not None and value < min_value:
                print(f"Value must be >= {min_value}")
                continue
            if max_value is not None and value > max_value:
                print(f"Value must be <= {max_value}")
                continue
            return value
        except ValueError:
            print("Invalid numeric value.")


def ask_probability(message, default=None):
    """Ask for a probability between 0 and 1."""
    return ask_float(message, default, 0.0, 1.0)


def load_last_config(path="output/config.json"):
    """Load last configuration if available (used as defaults)."""
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


# =====================================================
# CONFIG GENERATOR v3.0 (Actuarial strict defaults)
# =====================================================

def generate_configuration_v3():
    print("\n=== Insurance Config Generator — v3.0 (Actuarial strict defaults) ===\n")

    last = load_last_config()
    system_year = datetime.now().year

    # -------------------------------------------------
    # PORTFOLIO (core inputs)
    # -------------------------------------------------
    num_customers = ask_integer(
        "Number of customers",
        last.get("portfolio", {}).get("numCustomers", 20000),
        1000, 1_000_000
    )

    avg_policies_per_customer = ask_float(
        "Average policies per customer",
        last.get("portfolio", {}).get("avgPoliciesPerCustomer", 1.6),
        0.1, 10.0
    )

    quote_multiplier = ask_float(
        "Quote multiplier (quotes per policy)",
        last.get("portfolio", {}).get("quoteMultiplier", 4.0),
        0.5, 20.0
    )

    claim_rate_annual = ask_probability(
        "Annual claim rate per policy (0–1)",
        last.get("portfolio", {}).get("claimRateAnnual", 0.10)
    )

    history_years = ask_integer(
        "Years of historical data",
        last.get("portfolio", {}).get("historyYears", 3),
        1, 10
    )

    expected_policies = int(num_customers * avg_policies_per_customer)
    expected_quotes = int(expected_policies * quote_multiplier)
    expected_claims = int(expected_policies * claim_rate_annual * history_years)

    # -------------------------------------------------
    # RANDOM SEED
    # -------------------------------------------------
    default_seed = last.get("randomSeed", random.randint(1, 10_000_000))
    random_seed = ask_integer(
        "Random seed",
        default_seed,
        1, None
    )

    # -------------------------------------------------
    # EFFECTIVE DATES
    # -------------------------------------------------
    start_year_default = last.get("policyModel", {}).get("effectiveDateRange", {}).get(
        "startYear", system_year - history_years
    )
    end_year_default = last.get("policyModel", {}).get("effectiveDateRange", {}).get(
        "endYear", system_year
    )

    start_year = ask_integer(
        "Policy effective start year",
        start_year_default,
        1900, system_year + 10
    )
    end_year = ask_integer(
        "Policy effective end year",
        end_year_default,
        start_year, system_year + 10
    )

    # -------------------------------------------------
    # GEOGRAPHY (fixed for this portfolio)
    # -------------------------------------------------
    regions = {
        "north_east": ["NY", "MA"],
        "mid_west": ["IL", "OH"],
        "south": ["TX", "FL"],
        "west": ["CA", "WA"]
    }

    region_distribution = {
        "north_east": 0.25,
        "mid_west": 0.25,
        "south": 0.30,
        "west": 0.20
    }

    if abs(sum(region_distribution.values()) - 1.0) > 0.0001:
        raise ValueError("Region distribution must sum to 1.0")

    # =================================================
    # BUILD FULL CONFIG OBJECT (defaults = v2.4 strict)
    # =================================================

    config = {
        "version": "2.4",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "randomSeed": random_seed,

        "portfolio": {
            "numCustomers": num_customers,
            "avgPoliciesPerCustomer": avg_policies_per_customer,
            "quoteMultiplier": quote_multiplier,
            "claimRateAnnual": claim_rate_annual,
            "historyYears": history_years,
            "expectedPolicies": expected_policies,
            "expectedQuotes": expected_quotes,
            "expectedClaims": expected_claims
        },

        "geography": {
            "regions": regions,
            "regionDistribution": region_distribution
        },

        "customerModel": {
            "age": { "min": 18, "max": 85 },

            "genderDistribution": {
                "Male": 0.48,
                "Female": 0.48,
                "Other": 0.04
            },

            "occupationDistribution": {
                "Office": 0.30,
                "Manual": 0.25,
                "SelfEmployed": 0.20,
                "Professional": 0.15,
                "Unemployed": 0.10
            },

            "maritalStatusDistribution": {
                "Single": 0.40,
                "Married": 0.45,
                "Divorced": 0.10,
                "Widowed": 0.05
            },

            "income": { "min": 45000, "max": 250000 },
            "bmi": { "min": 18.5, "max": 40.0 },

            "acquisitionChannels": {
                "Agent": 0.40,
                "Broker": 0.25,
                "Digital": 0.25,
                "Referral": 0.10
            },

            "churn": {
                "baseProbability": 0.085,
                "churnReasons": {
                    "Price": 0.30,
                    "Service": 0.25,
                    "Competitor": 0.20,
                    "LifeChange": 0.15,
                    "PaymentIssues": 0.10
                }
            }
        },

        "productMix": {
            "Auto": 0.40,
            "Health": 0.20,
            "Life": 0.20,
            "Property": 0.20
        },

        "policyModel": {
            "tenureYearsDefault": 1,

            "effectiveDateRange": {
                "startYear": start_year,
                "endYear": end_year
            },

            "paymentFrequencyDistribution": {
                "Monthly": 0.60,
                "Quarterly": 0.25,
                "Annual": 0.15
            },

            "coverageRanges": {
                "Auto":      { "min": 6000,   "max": 50000 },
                "Health":    { "min": 2500,   "max": 20000 },
                "Life":      { "min": 15000,  "max": 250000 },
                "Property":  { "min": 20000,  "max": 250000 }
            },

            "deductibleRanges": {
                "Auto":      { "min": 900,  "max": 3000 },
                "Health":    { "min": 200,  "max": 800 },
                "Property":  { "min": 2500, "max": 7000 },
                "Life":      { "min": 0,    "max": 0 }
            },

            "riskScoreRules": {
                "min": 0,
                "max": 100,
                "auto_weight": {
                    "claims_history": 0.25,
                    "age": 0.20,
                    "income": 0.15,
                    "region": 0.10,
                    "product_features": 0.30
                }
            }
        },

        "claimsModel": {
            "frequency": {
                "Auto": 0.15,
                "Health": 0.10,
                "Property": 0.05,
                "Life": 0.02
            },

            "severityCurves": {
                "Auto": {
                    "distribution": "lognormal",
                    "mu": 7.00,
                    "sigma": 0.35
                },
                "Health": {
                    "distribution": "gamma",
                    "shape": 2.3,
                    "scale": 550
                },
                "Property": {
                    "distribution": "lognormal",
                    "mu": 7.20,
                    "sigma": 0.42
                },
                "Life": {
                    "distribution": "fixed",
                    "value": 15000
                }
            },

            "reportingDelay": {
                "meanDays": 3,
                "stdDays": 2
            },

            "settlementDelay": {
                "meanDays": 30,
                "stdDays": 15
            },

            "fraudScoreRules": {
                "weights": {
                    "reportDelay": 0.30,
                    "severityDeviation": 0.30,
                    "legalRepFlag": 0.25,
                    "priorClaims": 0.15
                }
            }
        },

        "underwriting": {
            "funnelProbabilities": {
                "Requested_to_Quoted": 0.95,
                "Quoted_to_Accepted": 0.40,
                "Accepted_to_Bound": 0.65,
                "Quoted_to_Declined": 0.15,
                "Accepted_to_Expired": 0.05
            },
            "stpThreshold": 30,

            "riskClassRules": {
                "Preferred":   { "min": 0,  "max": 20 },
                "Standard":    { "min": 21, "max": 60 },
                "Substandard": { "min": 61, "max": 85 },
                "Declined":    { "min": 86, "max": 100 }
            }
        },

        "pricingModel": {
            "lossDevelopment": {
                "periods": [12, 24, 36],
                "incurredGrowthRate": 0.15,
                "paidGrowthRate": 0.20
            },

            "technicallyRequiredPremium": {
                "Auto": {
                    "baseRate": 0.060,
                    "baseFactor": 2.00
                },
                "Health": {
                    "baseRate": 0.065,
                    "baseFactor": 1.60
                },
                "Property": {
                    "baseRate": 0.045,
                    "baseFactor": 2.30
                },
                "Life": {
                    "baseRate": 0.016,
                    "baseFactor": 1.35
                }
            },

            "marketPremiumVariation": {
                "minPercent": -0.20,
                "maxPercent": 0.20
            },

            "expenseStructure": {
                "Commission": 0.15,
                "Salary": 0.20,
                "IT": 0.10,
                "Marketing": 0.10,
                "Overhead": 0.15,
                "Other": 0.05
            },

            "capitalAllocation": {
                "Auto": 0.25,
                "Health": 0.25,
                "Life": 0.30,
                "Property": 0.20
            }
        },

        "retentionModel": {
            "campaignProbability": 0.10,
            "campaignTypes": {
                "Win-back": 0.40,
                "Cross-sell": 0.30,
                "Renewal": 0.30
            },
            "engagementScoreDistribution": {
                "min": 0,
                "max": 100
            },
            "npsDistribution": {
                "min": 0,
                "max": 10
            }
        },

        "output": {
            "directory": "output/",
            "exportParquet": True,
            "exportCSV": True,
            "schemaVersion": "v2",
            "partitioning": {
                "claimsByYear": True,
                "policiesByYear": True,
                "quotesByYear": True
            }
        },

        "hashSignature": ""  # filled after computing hash
    }

    # -------------------------------------------------
    # HASH SIGNATURE (deterministic)
    # -------------------------------------------------
    # Build a canonical representation (sorted keys) for the hash
    canonical = json.dumps(config, sort_keys=True).encode("utf-8")
    hash_sig = hashlib.sha256(canonical).hexdigest()
    config["hashSignature"] = hash_sig

    return config


# =====================================================
# SAVE CONFIG
# =====================================================

def save_configuration(config, filename="config.json"):
    out_dir = config.get("output", {}).get("directory", "output")
    os.makedirs(out_dir, exist_ok=True)
    full_path = os.path.join(out_dir, filename)

    with open(full_path, "w") as f:
        json.dump(config, f, indent=4)

    print(f"\nConfiguration saved to: {full_path}\n")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    cfg = generate_configuration_v3()
    save_configuration(cfg)
    print("Configurator file generated.\n")

