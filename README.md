# End-to-End Synthetic Insurance Data Pipeline (Data Engineering + Analytics)

A portfolio project simulating a full Insurance Analytics ecosystem: from synthetic data generation, through quality-controlled pipelines, to BI-ready datasets for Looker Studio.

---

# Table of Contents

1. Overview
2. Objectives & Value
3. Architecture Overview
4. Pipeline Stages (Modules A–E + HealthChecks)
5. Data Model Overview
6. Running the Project
7. CLI Output Gallery
8. Dashboards Gallery (Looker Studio)
9. Why This Project Matters
10. How to Reproduce Locally
11. Assets & Repository Structure
12. License & Disclaimers

---

# 1. Overview

## 1.1 Project Summary

This repository implements a complete **synthetic Insurance Data Engineering pipeline**, designed to showcase:

* **Data Engineering**: pipelines, normalization, schema management, loading.
* **Data Quality & Governance**: multiple HealthChecks across the lifecycle.
* **Data Analytics for Insurance**: claims, pricing, underwriting, retention.

The system simulates a realistic multi-line insurance portfolio and produces **BI-ready datasets** for building Looker Studio dashboards.

## 1.2 Scope in One Sentence

> From configuration and synthetic generation to Supabase warehouse and Looker Studio dashboards, with explicit HealthChecks at each critical stage.

---

# 2. Objectives & Value

## 2.1 Business & Analytical Goals

* Support **claims & loss analysis** (frequency, severity, loss ratio, development).
* Support **underwriting operations** (quote funnel, STP, hit ratio, time-to-quote / bind).
* Support **pricing & profitability** (rate adequacy, technical premium, exposure and development views).
* Support **retention & churn analytics** (churn flags, tenure, engagement, campaigns).

## 2.2 Technical Areas

This project best match with an **hybrid Data Engineer + Data Analytics profile** specifically oriented to:

* Insurance data modeling and lifecycle logic.
* Synthetic but **realistically-behaving** insurance portfolios.
* Data quality frameworks and HealthChecks.
* BI consumption contracts (Supabase + Looker Studio).

---

# 3. Architecture Overview

## 3.1 End-to-End Flow (High Level)

```text
Config → RAW Generation → Dataset HealthChecks → Normalization → Normalized HealthChecks
      → Connection & Schema Setup → Schema HealthChecks
      → Loader (Batch Import) → Loader / Performance / Business HealthChecks
      → Looker Studio Dashboards
```

## 3.2 Modules A–E (Conceptual)

* **Module A – Configuration**: defines portfolio size, mix, geography, risk behaviour.
* **Module B – RAW Generator**: creates synthetic operational-style data.
* **HealthChecks (early)**: validate that generated RAW is structurally sound and consistent.
* **Module C – Normalizer**: transforms RAW into clean BI-ready tables.
* **HealthChecks (normalized)**: enforce PK/FK rules, timelines, and data sanity.
* **Module D – Schema Layer**: creates tables, views, RLS and grants in Supabase.
* **HealthChecks (schema & connection)**: validate DB connectivity and DDL success.
* **Module E – Loader**: inserts normalized data into Supabase in batches.
* **HealthChecks (loader, performance, business)**: validate final DB state and performance for BI.

## 3.3 Tech Stack

* Python 3.x (Pandas, NumPy, CLI scripts).
* Supabase (PostgreSQL, RLS, views, grants).
* Looker Studio (free, cloud BI).
* Shell / CLI orchestrations.

---

# 4. Pipeline Stages (Modules A–E + HealthChecks)

This section documents the real modules of the project in order of execution.

---

## 4.1 Module A — Configuration Builder

**File:** `01_module_A_configurator.py`

Generates the core `config.json` that drives the entire simulation:

* Portfolio size and complexity (number of customers, policies per customer, claim rates).
* Product mix and geography distribution.
* Behaviour for claims, pricing, underwriting and retention.
* Deterministic random seed for reproducible runs.

**Output:**

```text
/output/config.json
```

---

## 4.2 Module B — Synthetic RAW Data Generator

**File:** `02_module_B_generator.py`

Creates **operational-style synthetic datasets**, including:

* Customers (demographics, geography, acquisition channel, income, BMI).
* Policies (coverage, deductibles, premium, dates, tenure).
* Claims (frequency/severity, occurrence/report/settlement dates, fraud score, legal rep).
* Loss development snapshots.
* Quotes and underwriting decisions (STP, accepted/bound/expired/declined).
* Retention / churn structures at customer level.
* Pricing segments by product line and state.

**Output (RAW):**

```text
/output/raw/*.csv
```

---

## 4.3 HealthCheck — RAW Dataset Validation

**File:** `03_healthcheck_dataset.py`

Executed **after** the RAW generator, this script validates that the generated datasets meet baseline expectations before any normalization:

* Presence of all required RAW CSV files.
* Row counts within expected ranges (vs. configuration).
* Mandatory columns present in each RAW file.
* Basic structural sanity (shapes, domains, non-empty key files).

If RAW data is structurally wrong, the pipeline stops here.

---

## 4.4 Module C — Normalizer & Enhancement

**File:** `04_module_C_normalizer.py`

Transforms RAW data into **BI-ready normalized tables**. Core responsibilities:

* Standardize data types (numerical, ISO date strings, booleans).
* Normalize null-like values (empty strings, "null", etc.).
* Build demographic and risk buckets (age, income, BMI).
* Enforce basic referential integrity (customers → policies → claims).
* Align geographies (state and region).
* Produce dim/fact-style outputs ready for loading.

**Output (normalized):**

```text
/output/normalized/*.csv
```

---

## 4.5 HealthCheck — Normalized Dataset Validation

**File:** `05_healthcheck_normalizer.py`

Runs domain-aware validations on the normalized layer, such as:

* Row counts vs configuration targets (customers, policies, quotes, claims, etc.).
* PK uniqueness (customer_id, policy_id, claim_id, quote_id).
* FK integrity (policies → customers, claims → policies, quotes/UW decisions → policies/customers).
* Claims lifecycle: `occurrence_date ≤ report_date ≤ settlement_date`.
* Pricing and loss development sanity (non-negative values, monotonic development).

Only if this healthcheck passes should the pipeline move on to DB loading.

---

## 4.6 HealthCheck — Connection & Environment

**File:** `06_healthcheck_connection.py`

Verifies that:

* Supabase connection is available.
* Mandatory env vars are set (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`).
* A basic DB connection can be opened and closed successfully.

This prevents running schema or loader modules with invalid or missing credentials.

---

## 4.7 Module D — Database Schema Creation Layer

**File:** `07_module_D_schema.py`

Applies all **DDL and security** logic to Supabase:

* Creates all target tables with the expected column definitions.
* Sets up primary keys and foreign keys.
* Creates analytical views for BI consumption.
* Applies Row-Level Security (RLS) policies and GRANTs.
* Executes SQL in blocks to clearly identify any failing statement.

This module defines the **warehouse contract** for Looker Studio and other consumers.

---

## 4.8 HealthCheck — Schema Validation

**File:** `08_healthcheck_schema.py`

Confirms that the schema in Supabase matches what the pipeline expects:

* Required tables exist.
* Required columns exist with correct data types.
* Views compile and can be queried.
* RLS and permissions are aligned with the intended design.

If schema validation fails, the pipeline must not proceed to data loading.

---

## 4.9 Module E — Data Loader (Batch Import)

**File:** `09_module_E_loader.py`

Loads the normalized CSVs into the Supabase warehouse. Features:

* Reads normalized files from `/output/normalized`.
* Inserts data table-by-table into Supabase.
* Uses batched inserts (e.g. 5000-row chunks) to avoid timeouts and huge single payloads.
* Tracks errors per table; if any table fails, a clear summary is printed.
* Converts common null markers from CSV into DB `NULL`.

Once this module completes successfully, Supabase contains a full analytical dataset ready for BI.

---

## 4.10 HealthCheck — Loader-Level Database Integrity

**File:** `10_healthcheck_loader.py`

Runs **post-load integrity checks** directly against the warehouse:

* Compares DB row counts vs normalized CSV row counts.
* Re-validates PK/FK consistency at DB level.
* Rechecks claim timelines and underwriting funnel consistency.
* Ensures no unexpected NULLs in critical ID and status fields.

This step ensures nothing was corrupted during the load process.

---

## 4.11 HealthCheck — BI View Performance Benchmark

**File:** `11_healthcheck_dbperformance.py`

Focuses on **performance and scalability** of the analytical views used by BI tools:

* Measures execution time of key views and representative analytical queries.
* Evaluates query complexity (e.g. via EXPLAIN / EXPLAIN ANALYZE).
* Flags heavy views that might require indexing or refactoring.

This ensures that Looker Studio dashboards operate with acceptable latency.

---

## 4.12 HealthCheck — Business & KPI-Level Validation

**File:** `12_healthcheck_business.py`

Final layer of quality control, oriented to **business semantics**:

* Checks that key KPIs (loss ratio, churn rate, hit ratio, STP rate, etc.) fall within plausible ranges given the configuration.
* Validates cross-domain relationships, for example:

  * Quote → Policy → Claim chains.
  * Churned customers not having active policies beyond churn date.
  * Pricing segments coherent with observed losses and exposure.
* Acts as a “sanity check” that the portfolio behavior makes sense for an insurance analyst or actuary.

Once this healthcheck passes, the dataset is considered production-ready for demo / portfolio purposes.

---

# 5. Data Model Overview

## 5.1 Dimensional & Fact Tables (BI Layer)

Typical normalized outputs include:

**Dimensions**

* `dim_regions`
* `dim_states`
* `dim_customers`

**Facts**

* `fact_policies`
* `fact_claims`
* `fact_quotes`
* `fact_uw_decisions`
* `fact_retention`
* `fact_pricing_segments`
* `fact_loss_development`

## 5.2 Conceptual ERD (Textual)

```text
dim_customers ──┐
                ├── fact_policies ─── fact_claims ─── fact_loss_development
dim_states ─────┘

fact_policies ─── fact_quotes ─── fact_uw_decisions

dim_customers ─── fact_retention
fact_policies ─── fact_pricing_segments
```

## 5.3 Grains & Constraints

* 1 row per **customer_id** in `dim_customers`.
* 1 row per **policy_id** in `fact_policies`.
* 1 row per **claim_id** in `fact_claims`.
* 1 row per **quote_id** in `fact_quotes`.
* 1 row per **(claim_id × development_month)** in `fact_loss_development`.
* 1 row per **segment_id** in `fact_pricing_segments`.

---

# 6. Running the Project

## 6.1 Requirements

* Python 3.10+ + Packages: supabase-py pandas requests 
* Supabase project (free tier is sufficient)
* Environment variables:

  * `SUPABASE_URL`
  * `SUPABASE_SERVICE_ROLE_KEY`
  * `SUPABASE_DB_URL`

## 6.2 Installation

```bash
pip install -r requirements.txt
```

## 6.3 Running Modules Manually (Typical Order)

```bash
python 01_module_A_configurator.py

python 02_module_B_generator.py
python 03_healthcheck_dataset.py

python 04_module_C_normalizer.py
python 05_healthcheck_normalizer.py

python 06_healthcheck_connection.py
python 07_module_D_schema.py
python 08_healthcheck_schema.py

python 09_module_E_loader.py
python 10_healthcheck_loader.py

python 12_healthcheck_dbperformance.py
python 13_healthcheck_business.py
```

You can wrap this into a Makefile or a single orchestrator script if desired.

---

# 7. CLI Output Gallery

Placeholders for screenshots of CLI runs (to be added as image files in `/assets/images`):

* Generator logs:
  `![Generator Logs](./assets/images/generator_logs.png)`

* Normalizer HealthCheck summary:
  `![Normalizer HealthCheck](./assets/images/healthcheck_normalizer.png)`

* Loader batch progress:
  `![Loader Batches](./assets/images/loader_batches.png)`

* Business HealthCheck KPIs:
  `![Business HealthCheck](./assets/images/healthcheck_business.png)`

---

# 8. Dashboards Gallery (Looker Studio)

Planned dashboards (URLs to be added later):

* Claims & Loss Analysis
* Pricing & Profitability
* Underwriting Funnel & STP
* Retention & Churn

Suggested image placeholders:

* `![Claims Dashboard](./assets/images/dashboard_claims.png)`
* `![Pricing Dashboard](./assets/images/dashboard_pricing.png)`
* `![Underwriting Dashboard](./assets/images/dashboard_uw.png)`
* `![Retention Dashboard](./assets/images/dashboard_retention.png)`

---

# 9. Why This Project Matters

This project demonstrates:

* A realistic **insurance analytical ecosystem** end-to-end.
* **Multiple layers of HealthChecks** resembling enterprise practices:
  structural, referential, temporal, performance, and business-level.
* A **hybrid profile**: Data Engineering + Insurance Analytics, not just toy data.
* A concrete foundation for Looker Studio and other BI tools to plug in and immediately explore KPIs.

---

# 10. How to Reproduce Locally

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Configure Supabase and environment variables.
5. Run the modules in the order described in section 6.3.
6. Connect Supabase to Looker Studio and build dashboards on top of the created views.

---

# 11. Assets & Repository Structure

Suggested structure:

```text
/assets/
    /images/
        architecture.png
        erd.png
        generator_logs.png
        healthcheck_normalizer.png
        loader_batches.png
        healthcheck_business.png
        dashboard_claims.png
        dashboard_pricing.png
        dashboard_uw.png
        dashboard_retention.png

/output/
    /raw/
    /normalized/
    /final/        # optional final exports

scripts:
    01_module_A_configurator.py
    02_module_B_generator.py
    03_healthcheck_dataset.py
    04_module_C_normalizer.py
    05_healthcheck_normalizer.py
    06_healthcheck_connection.py
    07_module_D_schema.py
    08_healthcheck_schema.py
    09_module_E_loader.py
    10_healthcheck_loader.py
    12_healthcheck_dbperformance.py
    13_healthcheck_business.py
    clean_data.py
    run_sql_erase.py
```

---

# 12. License & Disclaimers

## 12.1 License

This project is released under the **MIT License**.
You are free to use, modify, and adapt it for educational and portfolio purposes.

## 12.2 Synthetic Data Disclaimer

All data generated and used by this project is **100% synthetic**.
It does **not** correspond to any real customer, policy, claim, underwriting decision, or pricing information, and is safe to share publicly for demonstration and learning purposes.
