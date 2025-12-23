---

# Insurance Analytics Data Model

**DB-First Design Documentation (BI Contract v1)**

> **Source of truth:** `schema.sql`
> **Database:** PostgreSQL (Supabase)
> **Audience:** Data Engineers / DBAs
> **Modeling style:** Star schema (Dimensional Modeling)
> **Purpose:** Analytical warehouse for insurance KPIs and dashboards

---

## Table of Contents (T0C – Level 1)

1. [Modeling Scope & Principles](#modeling-scope--principles)
2. [Logical Data Model Overview](#logical-data-model-overview)
3. [Physical Data Model](#physical-data-model)

   * [Dimensions](#dimensions)

     * [dim_time](#dim_time)
     * [dim_state](#dim_state)
     * [dim_clients](#dim_clients)
     * [dim_products](#dim_products)
     * [dim_policies](#dim_policies)
   * [Fact Tables](#fact-tables)

     * [fact_policies](#fact_policies)
     * [fact_claims](#fact_claims)
     * [fact_expenses](#fact_expenses)
     * [fact_taxes](#fact_taxes)
4. [Entity Relationships & Cardinality](#entity-relationships--cardinality)
5. [Design Decisions & Constraints](#design-decisions--constraints)

---

## Modeling Scope & Principles

### Scope

This data model supports **analytical workloads only**.
It is **not** an OLTP or policy administration system.

Primary use cases:

* Portfolio size & premium exposure
* Claims frequency, severity, and loss ratio
* Risk distribution and underwriting monitoring
* Expense and tax impact analysis

### Core Principles

| Principle              | Explanation                                       |
| ---------------------- | ------------------------------------------------- |
| **Star schema**        | Optimized for BI tools and aggregation            |
| **Immutable facts**    | Facts are append-only; no updates expected        |
| **Surrogate-free IDs** | Business keys used directly (policy_id, claim_id) |
| **Explicit grain**     | Every fact table has a clearly defined grain      |
| **Time as dimension**  | All temporal analysis uses `dim_time`             |

---

## Logical Data Model Overview

### High-Level Entities

Plain English translation included.

```
TIME
 └── Used to analyze events by day, month, year

STATE
 └── Geographic classification (state, region, market tier)

CLIENT
 └── A customer who owns one or more insurance policies

PRODUCT
 └── An insurance offering (line of business + plan)

POLICY
 └── A contract between client and insurer

CLAIM
 └── A request for compensation under a policy

EXPENSE
 └── Operating costs of the insurance company

TAX
 └── Government taxes applied to premiums
```

---

## Physical Data Model

---

## Dimensions

---

### `dim_time`

**Purpose (plain English):**
Central calendar table used to analyze all facts by date.

**Grain:**
➡️ **One row per calendar day**

**Primary Key:**

* `date_key` (YYYYMMDD integer)

#### Columns

| Column      | Type    | Meaning                       |
| ----------- | ------- | ----------------------------- |
| date_key    | INT     | Surrogate date key (20250131) |
| full_date   | DATE    | Actual calendar date          |
| year        | INT     | Calendar year                 |
| month       | INT     | Calendar month (1–12)         |
| month_name  | TEXT    | Month name                    |
| quarter     | INT     | Quarter (1–4)                 |
| year_month  | TEXT    | YYYY-MM                       |
| day_of_week | INT     | 1 (Mon) – 7 (Sun)             |
| is_weekend  | BOOLEAN | Weekend flag                  |

**Why this exists:**
Avoids date functions in BI tools and standardizes time logic.

---

### `dim_state`

**Purpose:**
Geographic lookup and market segmentation.

**Grain:**
➡️ **One row per state**

**Primary Key:**

* `state_code`

#### Columns

| Column      | Meaning                         |
| ----------- | ------------------------------- |
| state_code  | State abbreviation (e.g. NY)    |
| region_code | Region grouping (NE, SE, MW, W) |
| market_tier | Market size / importance tier   |

---

### `dim_clients`

**Purpose:**
Customer master data.

**Grain:**
➡️ **One row per client**

**Primary Key:**

* `client_id`

**Foreign Keys:**

* `state_code → dim_state`

#### Columns

| Column               | Meaning                    |
| -------------------- | -------------------------- |
| client_id            | Unique customer identifier |
| registration_year    | Year client joined         |
| age                  | Age at registration        |
| gender               | Client gender              |
| customer_segment     | Individual / Corporate     |
| state_code           | Client’s state             |
| region_code          | Derived region             |
| market_tier          | Derived market tier        |
| max_policies_allowed | Underwriting limit         |

---

### `dim_products`

**Purpose:**
Insurance product catalog.

**Grain:**
➡️ **One row per product plan**

**Primary Key:**

* `product_key`

#### Columns

| Column           | Meaning                       |
| ---------------- | ----------------------------- |
| product_key      | LOB + Plan (e.g. HEALTH_GOLD) |
| line_of_business | Life / Health / Auto          |
| plan_name        | Plan tier name                |

---

### `dim_policies`

**Purpose:**
Policy header information.

**Grain:**
➡️ **One row per policy**

**Primary Key:**

* `policy_id`

**Foreign Keys:**

* `client_id → dim_clients`
* `state_code → dim_state`

#### Columns

| Column        | Meaning                  |
| ------------- | ------------------------ |
| policy_id     | Unique policy identifier |
| policy_number | Business policy number   |
| client_id     | Policy owner             |
| state_code    | Issuing state            |
| region_code   | Geographic region        |
| is_renewal    | New business vs renewal  |

---

## Fact Tables

---

### `fact_policies`

**Purpose:**
Policy lifecycle, premium, and risk metrics.

**Grain:**
➡️ **One row per policy**

**Primary Key:**

* `policy_id`

**Foreign Keys:**

* `policy_id → dim_policies`
* `product_key → dim_products`
* `state_code → dim_state`
* `effective_date_key → dim_time`

#### Columns

| Column              | Meaning               |
| ------------------- | --------------------- |
| effective_date_key  | Policy start date     |
| expiration_date_key | Policy end date       |
| policy_year         | Start year            |
| policy_month        | Start month           |
| status              | Active / Expired      |
| risk_score          | Risk assessment score |
| monthly_premium     | Monthly price         |
| annual_premium      | Annualized price      |

---

### `fact_claims`

**Purpose:**
Claims activity and loss amounts.

**Grain:**
➡️ **One row per claim**

**Primary Key:**

* `claim_id`

**Foreign Keys:**

* `policy_id → dim_policies`
* `product_key → dim_products`
* `incident_date_key → dim_time`
* `report_date_key → dim_time`

#### Columns

| Column                 | Meaning                 |
| ---------------------- | ----------------------- |
| claim_type             | Type of incident        |
| claim_status           | Paid / Pending / Denied |
| fraud_flag             | Fraud indicator         |
| days_to_settle         | Claim resolution time   |
| claim_amount_requested | Initial claim           |
| claim_amount_approved  | Approved amount         |
| claim_amount_paid      | Paid amount             |

---

### `fact_expenses`

**Purpose:**
Operational expenses of insurer.

**Grain:**
➡️ **One row per state per month per expense category**

**Primary Key:**

* `expense_id`

**Foreign Keys:**

* `state_code → dim_state`
* `date_key → dim_time`

---

### `fact_taxes`

**Purpose:**
Premium tax tracking.

**Grain:**
➡️ **One row per policy**

**Primary Key:**

* `tax_id`

**Foreign Keys:**

* `state_code → dim_state`
* *(date_key nullable by design)*

#### Columns

| Column     | Meaning              |
| ---------- | -------------------- |
| tax_type   | PREMIUM_TAX          |
| tax_base   | Premium amount taxed |
| tax_rate   | Applied tax rate     |
| tax_amount | Tax paid             |

---

## Entity Relationships & Cardinality

```
dim_clients 1 ────< dim_policies 1 ────1 fact_policies
                          |
                          └───< fact_claims
```

* One client → many policies
* One policy → many claims
* One state → many clients, policies, claims, expenses
* One time row → many facts

---

## Design Decisions & Constraints

* **No soft deletes**: historical accuracy preserved
* **Nullable settlement dates**: future claim lifecycle support
* **No FK on expiration_date_key**: policies may expire outside time range
* **Indexes only on facts**: dimensions assumed small
* **RLS enabled everywhere**: Supabase security-first design

---

# Semantic Layer (BI Views)

**Insurance Analytics – Dashboard Contract v1**

> **Source of truth:** `full_schema.txt`
> **Layer type:** Semantic / Analytical Views
> **Rule:** **1 View = 1 Dashboard**
> **Audience:** Data Engineers, DBAs, BI Engineers

---

## Table of Contents (Semantic Layer)

1. [Semantic Layer Principles](#semantic-layer-principles)
2. [vw_dash_exec_portfolio](#vw_dash_exec_portfolio)
3. [vw_dash_claims_loss](#vw_dash_claims_loss)
4. [vw_dash_operations_daily](#vw_dash_operations_daily)
5. [vw_dash_risk_daily](#vw_dash_risk_daily)
6. [Cross-View Consistency Rules](#cross-view-consistency-rules)
7. [Performance & DBA Notes](#performance--dba-notes)

---

## Semantic Layer Principles

### Why Views Exist

These views:

* Abstract **complex joins** away from BI tools
* Enforce **single source of KPI truth**
* Guarantee **stable grain per dashboard**
* Prevent ad-hoc metric redefinition

### Contract Rules

| Rule                 | Meaning                        |
| -------------------- | ------------------------------ |
| 1 view = 1 dashboard | No mixed dashboard logic       |
| Fixed grain          | BI tools must not re-aggregate |
| Read-only            | No transformations in BI       |
| Time-aware           | All metrics are time-sliced    |

---

## `vw_dash_exec_portfolio`

### Business Purpose (Plain English)

**Executive snapshot of portfolio size and premium exposure by month.**

Used by leadership to answer:

* How big is the portfolio?
* How much premium is exposed?
* How is it distributed by geography and product?

---

### Grain

➡️ **One row per month × state × region × line_of_business**

This is a **monthly snapshot**, not transactional data.

---

### Source Tables

| Table         | Role              |
| ------------- | ----------------- |
| fact_policies | Portfolio base    |
| dim_time      | Monthly expansion |
| dim_products  | Product grouping  |

---

### Time Logic (Critical)

```sql
t.date_key BETWEEN p.effective_date_key
               AND COALESCE(p.expiration_date_key, p.effective_date_key)
```

**Meaning in plain English:**
A policy contributes to *every month it is active*, not only its start month.

---

### Metrics

| Metric                | Definition                 |
| --------------------- | -------------------------- |
| active_policies       | Count of in-force policies |
| total_annual_premium  | Annualized exposure        |
| total_monthly_premium | Monthly exposure           |

---

### Design Notes

* Uses **annual premium** for exposure, not revenue
* Expansion across months is intentional
* Safe for cumulative charts

---

## `vw_dash_claims_loss`

### Business Purpose

**Claims performance and loss ratio monitoring.**

Answers:

* How many claims occurred?
* How severe are claims?
* Are losses aligned with premium?

---

### Grain

➡️ **One row per month × product × state × region**

Claims are grouped by **incident date month**.

---

### Source Tables

| Table         | Role               |
| ------------- | ------------------ |
| fact_claims   | Claims data        |
| fact_policies | Exposure base      |
| dim_time      | Monthly alignment  |
| dim_products  | LOB classification |

---

### KPIs Explained (Plain English)

| KPI             | Meaning                  |
| --------------- | ------------------------ |
| claim_frequency | Claims per active policy |
| claim_severity  | Average paid loss        |
| loss_ratio      | Losses ÷ premium         |

Loss Ratio interpretation:

* `< 1.0` → profitable
* `> 1.0` → losing money

---

### Critical DBA Note

Claims are joined to **policy exposure**, not independent counts.
This avoids inflated frequency.

---

## `vw_dash_operations_daily`

### Business Purpose

**Daily operational monitoring of policy flow.**

Answers:

* How many policies are active today?
* How many started or ended today?

---

### Grain

➡️ **One row per day × state × region × line_of_business**

---

### Metrics

| Metric                 | Meaning                       |
| ---------------------- | ----------------------------- |
| active_policies        | Policies in force on that day |
| daily_premium_exposure | Daily premium equivalent      |
| policies_started       | New policies                  |
| policies_ended         | Expired policies              |

---

### Time Expansion Logic

Uses **daily expansion** between effective and expiration date.

This view is **computationally heavier** by design.

---

## `vw_dash_risk_daily`

### Business Purpose

**Risk and underwriting quality monitoring.**

Answers:

* How risky is the portfolio today?
* Is new business riskier than renewals?

---

### Grain

➡️ **One row per day × state × region × line_of_business**

---

### Risk KPIs

| Metric                | Meaning                 |
| --------------------- | ----------------------- |
| avg_risk_score        | Average portfolio risk  |
| high_risk_policies    | Count of risky policies |
| new_business_policies | First-time policies     |
| renewal_policies      | Renewals                |
| avg_new_business_risk | Risk of new business    |

---

### Risk Threshold Note

```sql
WHEN fp.risk_score >= 0.8
```

This is a **synthetic threshold** for demo purposes, not actuarial.

---

## Cross-View Consistency Rules

| Rule                   | Reason                  |
| ---------------------- | ----------------------- |
| Same time logic        | Prevent metric drift    |
| Same policy base       | Portfolio alignment     |
| No derived joins in BI | Prevent inconsistencies |
| No KPI recalculation   | Contract enforcement    |

---

## Performance & DBA Notes

### Index Usage

| Index           | Used By                 |
| --------------- | ----------------------- |
| idx_fp_eff_exp  | All time-expanded views |
| idx_fc_incident | Claims dashboard        |
| idx_fc_policy   | Claims joins            |

---

### Expected Load Profile

| View                     | Cost   |
| ------------------------ | ------ |
| vw_dash_exec_portfolio   | Low    |
| vw_dash_claims_loss      | Medium |
| vw_dash_operations_daily | High   |
| vw_dash_risk_daily       | High   |

---

### Scaling Recommendations

* Partition `fact_policies` by year if >10M rows
* Pre-aggregate monthly snapshots if latency >3s
* Avoid BI filters on `date_key BETWEEN`

---

## Final Notes

This semantic layer:

* Enforces **analytical correctness**
* Prevents **dashboard KPI drift**
* Is **intentionally conservative** in design
* Mirrors enterprise insurance BI patterns

---
