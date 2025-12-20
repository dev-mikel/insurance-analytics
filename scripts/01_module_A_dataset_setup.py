#!/usr/bin/env python3
"""
MODULE A — CONFIGURATOR

Purpose:
- Generate a configuration file (config.json) used by Module B
- Models a startup insurance company starting operations in 2023
- Ensures positive ROI every year with realistic margins
- Does NOT modify schema or downstream logic

Audience:
- Junior / Mid-level developers
- Analytics & Data Engineering projects
"""

from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path
from typing import Dict, Any, List


# ============================================================
# CLI — SINGLE USER INPUT
# ============================================================
# We only ask ONE question:
# Total number of historical clients.
# This controls database size and dashboard performance.

def ask_total_clients() -> int:
    prompt = (
        "Total clientes históricos "
        "(recomendado 1,000 – 10,000) "
        "[default: 3000]: "
    )
    raw = input(prompt).strip()

    if not raw:
        return 3000

    value = int(raw)
    if value < 500 or value > 100_000:
        raise ValueError("Total de clientes fuera de rango razonable")

    return value


TOTAL_CLIENTS = ask_total_clients()


# ============================================================
# TIME WINDOW
# ============================================================
# Startup begins operations in 2023
# We simulate 3 years of history

# ============================================================
# TIME WINDOW — CONSOLIDATED COMPANY
# ============================================================

HISTORY_YEARS = 2
END_DATE = date(2025, 12, 31)
START_DATE = date(2024, 1, 1)

YEARS = [2024, 2025]


# ============================================================
# CLIENT DISTRIBUTION (CONSOLIDATED, STABLE GROWTH)
# ============================================================

GROWTH_RATE = 0.40  # YoY

active_clients_2024 = int(TOTAL_CLIENTS / (1 + GROWTH_RATE))
active_clients_2025 = TOTAL_CLIENTS

active_clients_by_year = {
    2024: active_clients_2024,
    2025: active_clients_2025,
}


# ============================================================
# ORGANIZATIONAL STRUCTURE
# ============================================================

REGIONS = [
    {"region_id": 1, "region_name": "Northeast", "region_code": "NE"},
    {"region_id": 2, "region_name": "Southeast", "region_code": "SE"},
    {"region_id": 3, "region_name": "Midwest",   "region_code": "MW"},
    {"region_id": 4, "region_name": "West",      "region_code": "W"},
]

STATES = [
    {"state_code": "NY", "region_code": "NE", "market_tier": "Tier 1"},
    {"state_code": "PA", "region_code": "NE", "market_tier": "Tier 2"},
    {"state_code": "MA", "region_code": "NE", "market_tier": "Tier 1"},
    {"state_code": "NJ", "region_code": "NE", "market_tier": "Tier 2"},
    {"state_code": "CT", "region_code": "NE", "market_tier": "Tier 2"},

    {"state_code": "FL", "region_code": "SE", "market_tier": "Tier 1"},
    {"state_code": "GA", "region_code": "SE", "market_tier": "Tier 2"},
    {"state_code": "NC", "region_code": "SE", "market_tier": "Tier 2"},
    {"state_code": "SC", "region_code": "SE", "market_tier": "Tier 3"},

    {"state_code": "IL", "region_code": "MW", "market_tier": "Tier 2"},
    {"state_code": "OH", "region_code": "MW", "market_tier": "Tier 2"},
    {"state_code": "MI", "region_code": "MW", "market_tier": "Tier 2"},
    {"state_code": "WI", "region_code": "MW", "market_tier": "Tier 3"},

    {"state_code": "CA", "region_code": "W", "market_tier": "Tier 1"},
    {"state_code": "TX", "region_code": "W", "market_tier": "Tier 2"},
    {"state_code": "WA", "region_code": "W", "market_tier": "Tier 1"},
    {"state_code": "OR", "region_code": "W", "market_tier": "Tier 2"},
    {"state_code": "AZ", "region_code": "W", "market_tier": "Tier 3"},
]


# ============================================================
# INSURANCE PRODUCTS
# ============================================================
# Pricing and target loss ratios are conservative to ensure
# profitability for a startup insurer.

INSURANCE_PLANS = {
    "Life": {
        "Basic":    {"base_monthly_premium": 55,  "target_loss_ratio": 0.48},
        "Standard": {"base_monthly_premium": 120, "target_loss_ratio": 0.50},
        "Premium":  {"base_monthly_premium": 310, "target_loss_ratio": 0.46},
    },
    "Health": {
        "Bronze": {"base_monthly_premium": 460,  "target_loss_ratio": 0.78},
        "Silver": {"base_monthly_premium": 690,  "target_loss_ratio": 0.77},
        "Gold":   {"base_monthly_premium": 1080, "target_loss_ratio": 0.74},
    },
    "Auto": {
        "Liability": {"base_monthly_premium": 105, "target_loss_ratio": 0.60},
        "Standard":  {"base_monthly_premium": 195, "target_loss_ratio": 0.65},
        "Full":      {"base_monthly_premium": 340, "target_loss_ratio": 0.70},
    },
}


# ============================================================
# PORTFOLIO ASSUMPTIONS
# ============================================================

AVG_POLICIES_PER_CLIENT = 1.75

PORTFOLIO_BY_YEAR = {
    year: {
        "active_clients": active_clients_by_year[year],
        "estimated_policies": int(active_clients_by_year[year] * AVG_POLICIES_PER_CLIENT),
    }
    for year in YEARS
}


# ============================================================
# CLAIMS MODEL (STARTUP UNDERWRITING)
# ============================================================
# Slightly lower claim frequency in early years
# due to stricter underwriting

CLAIMS_BASELINE_FREQUENCY = {
    "Life": 0.005,
    "Health": 0.25,
    "Auto": 0.10,
}

SEASONAL_FACTORS_BY_MONTH = {
    1: 0.90, 2: 0.92, 3: 0.96, 4: 1.00,
    5: 1.05, 6: 1.10, 7: 1.14, 8: 1.12,
    9: 1.08, 10: 1.00, 11: 0.95, 12: 0.92,
}

# Climate impact by state (used by Module B)
CLIMATE_SENSITIVITY_BY_STATE = {
    # NORTHEAST (NE)
    "NY": 1.03,
    "PA": 1.00,
    "MA": 0.98,
    "NJ": 1.01,
    "CT": 0.99,

    # SOUTHEAST (SE)
    "FL": 1.18,
    "GA": 1.05,
    "NC": 1.04,
    "SC": 1.06,

    # MIDWEST (MW)
    "IL": 0.97,
    "OH": 0.96,
    "MI": 0.95,
    "WI": 0.94,

    # WEST (W)
    "CA": 1.12,
    "TX": 1.10,
    "WA": 1.04,
    "OR": 1.02,
    "AZ": 1.08,
}

# ============================================================
# MACRO ENVIRONMENT (STABLE BUSINESS)
# ============================================================

MACRO_ENVIRONMENT = {
    "yearly_cycle": {
        2024: {
            "growth_factor": 1.00,
            "volatility_boost": 1.05,
            "target_roi": 0.8,
        },
        2025: {
            "growth_factor": 1.25,
            "volatility_boost": 1.05,
            "target_roi": 0.14,
            "is_cutoff": True,
        },
    }
}

# ============================================================
# STOCHASTIC / VOLATILITY MODEL (DASHBOARD-FRIENDLY)
# ============================================================

VOLATILITY_MODEL = {
    "risk_score_std_dev_range": [1.2, 1.8],
    "premium_noise_pct_range": [0.06, 0.12],
    "claim_frequency_noise_range": [0.92, 1.06],
    "claim_severity_noise_range": [0.97, 1.08],
    "expense_noise_pct_range": [0.05, 0.10],
}



# ============================================================
# FINAL CONFIG EXPORT
# ============================================================

CONFIG: Dict[str, Any] = {
	"meta": {
		"module": "Module A",
		"version": "4.0",
		"company_stage": "consolidated_insurer",
		"operations_start_year": 2020,
		"scenario": "Consolidated insurer, stable portfolio, 15% YoY growth",
	},


    "time": {
        "start_date": START_DATE.isoformat(),
        "end_date": END_DATE.isoformat(),
        "years": YEARS,
        "cutoff_year": 2025,
        "cutoff_type": "artificial_snapshot",
    },

    "portfolio": {
        "avg_policies_per_client": AVG_POLICIES_PER_CLIENT,
        "by_year": PORTFOLIO_BY_YEAR,
        "total_clients_historical": TOTAL_CLIENTS,
    },

    "organization": {
        "regions": REGIONS,
        "states": STATES,
    },

    "products": INSURANCE_PLANS,

    "claims": {
        "baseline_frequency": CLAIMS_BASELINE_FREQUENCY,
        "seasonality_by_month": SEASONAL_FACTORS_BY_MONTH,
        "climate_sensitivity_by_state": CLIMATE_SENSITIVITY_BY_STATE,
        "default_climate_factor": 1.0,
    },

    "macro_environment": MACRO_ENVIRONMENT,
    "volatility_model": VOLATILITY_MODEL,
}


# ============================================================
# WRITE OUTPUT FILE
# ============================================================

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

out_file = OUTPUT_DIR / "config.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(CONFIG, f, indent=2)

print("\n[OK] Module A configuration generated")
print(f"     Total clientes históricos: {TOTAL_CLIENTS:,}")
print(f"     Ventana: {START_DATE} → {END_DATE}")
print(f"     Output: {out_file}")
