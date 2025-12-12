# **DATA ARCHITECTURE DOCUMENT (DAD)**

**Insurance Analytics Warehouse – Supabase / PostgreSQL**

**Author:** Miguel Ladines
**Version:** 2.0
**Status:** Aligned with production schema

---

## **1. Executive Summary**

This document defines the **end-to-end data architecture** of the *Insurance Analytics Warehouse*, implemented on **Supabase (PostgreSQL)** and populated through a **deterministic synthetic data pipeline**.

The architecture is designed **exclusively for analytics**, supporting dashboards for:

* Claims & Loss Analysis
* Underwriting Funnel & STP
* Retention & Churn
* Pricing & Portfolio Performance

The warehouse follows a **hybrid dimensional (star-like) model**, enforces **Row-Level Security (RLS)** on all tables, and exposes **analytical views as the BI consumption contract**.

---

## **2. Architecture Principles**

1. **Dashboard-Driven Design**
   No table or column exists without a clear analytical or KPI purpose.

2. **Strict Layer Separation**
   RAW → Normalized → Warehouse → BI Views.

3. **Single Source of Truth (SSOT)**
   Supabase `dim_*` and `fact_*` tables are the authoritative analytical source.

4. **Security by Default**
   RLS enabled on all tables, with write access restricted to `service_role`.

5. **BI-Optimized Consumption**
   BI tools (Looker Studio) query **views only**, never base tables.

6. **Deterministic & Reproducible**
   The same `config.json` always produces identical warehouse outputs.

---

## **3. High-Level Architecture**

```
Module A: Configuration
        ↓
Module B: RAW Generator
        ↓
HealthCheck: RAW Quality
        ↓
Module C: Normalizer
        ↓
HealthCheck: Normalized Quality
        ↓
Module D: Schema & Security
        ↓
Module E: Loader
        ↓
HealthChecks: Loader / Performance / Business
        ↓
Looker Studio Dashboards
```

---

## **4. Logical Data Architecture**

### **4.1 Dimension Tables**

| Table           | Purpose                                   |
| --------------- | ----------------------------------------- |
| `dim_regions`   | Macro geographic segmentation             |
| `dim_states`    | States linked to regions                  |
| `dim_customers` | Customer demographics, buckets, geography |

---

### **4.2 Fact Tables**

| Table                   | Grain                          |
| ----------------------- | ------------------------------ |
| `fact_policies`         | 1 row per `policy_id`          |
| `fact_claims`           | 1 row per `claim_id`           |
| `fact_quotes`           | 1 row per `quote_id`           |
| `fact_uw_decisions`     | 1 row per `quote_id`           |
| `fact_retention`        | 1 row per customer event       |
| `fact_pricing_segments` | 1 row per `segment_id`         |
| `fact_loss_development` | `claim_id × development_month` |

---

### **4.3 Core Relationships**

```
dim_regions ──┐
              ├─ dim_states ──┐
                              ├─ dim_customers ──┐
                                                  ├─ fact_policies ── fact_claims ── fact_loss_development
                                                  ├─ fact_quotes ── fact_uw_decisions
                                                  ├─ fact_retention
                                                  └─ fact_pricing_segments
```

---

## **5. Physical Architecture (PostgreSQL)**

### **5.1 Database Engine**

* PostgreSQL 15 (Supabase-managed)
* Identity columns for event-style facts
* Explicit PK/FK constraints to enforce referential integrity

---

### **5.2 Indexing Strategy**

Indexes exist **only where required for BI and healthchecks**:

* `dim_customers(region, state)`
* `fact_policies(customer_id)`
* `fact_claims(policy_id, customer_id)`
* `fact_quotes(customer_id)`
* `fact_uw_decisions(quote_id)`
* `fact_pricing_segments(state)`
* `fact_loss_development(claim_id)`

Objective: **sub-500 ms execution for BI views**.

---

## **6. Security & Access Architecture**

### **6.1 Role Model**

| Role            | Access                                     |
| --------------- | ------------------------------------------ |
| `anon`          | SELECT on `dim_regions`, `dim_states`      |
| `authenticated` | SELECT on all dimensions, facts, and views |
| `service_role`  | Full CRUD (ETL and maintenance)            |

---

### **6.2 Row-Level Security (RLS)**

* RLS enabled on **all tables**
* `anon` and `authenticated` roles are **read-only**
* Write access explicitly denied via policies
* `service_role` granted controlled full access

---

## **7. BI Consumption Layer (Views)**

Views are the **stable analytical contract** for Looker Studio.

### **7.1 Analytical Views**

| View                     | Grain           | Dashboard     |
| ------------------------ | --------------- | ------------- |
| `vw_loss_ratio`          | policy × claim  | Claims & Loss |
| `vw_underwriting_funnel` | quote           | Underwriting  |
| `vw_churn`               | customer        | Retention     |
| `vw_pricing_adequacy`    | segment         | Pricing       |
| `vw_policy_frequency`    | policy          | Claims        |
| `vw_executive_portfolio` | product × state | Executive     |

---

### **7.2 View Design Rules**

* Minimal logic in BI tools
* Precomputed flags (`quoted_flag`, `bound_flag`)
* Ratios calculated in SQL
* Controlled LEFT JOINs to preserve exposure

---

## **8. Performance Architecture**

### **8.1 Performance Targets**

| Metric                 | Target   |
| ---------------------- | -------- |
| BI view execution time | < 500 ms |
| EXPLAIN plan cost      | < 50,000 |
| Looker Studio latency  | < 1 s    |

Validated using `healthcheck_dbperformance.py`.

---

## **9. Data Lifecycle Management**

* **Reset:** `clean_data.py` (TRUNCATE + RESTART IDENTITY)
* **Rebuild:** `run_sql_erase.py` + schema recreation
* **Reload:** `09_module_E_loader.py`
* **Validation:** HealthChecks 10–12

The lifecycle follows a **truncate-and-reload analytical model**.

---

## **10. Explicit Out of Scope**

The following are intentionally excluded:

* Slowly Changing Dimensions (SCD Type 2)
* Billing or payment systems
* Real actuarial reserving
* Production ML scoring
* Streaming / CDC ingestion

This warehouse is **analytical, not operational**.

---
