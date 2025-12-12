# **Functional Specification Requirements (FSR) **

## **Insurance Data Generation & Warehouse Pipeline**

**Author:** Miguel Ladines
**Version:** v1.0

# **Table of Contents**

**1. Scope & Business Analytical Requirements**
 1.1 Purpose
 1.2 Analytical Context
 1.3 Dashboard-Driven Scope
 1.4 Out-of-Scope Items

**2. Data Model Specification (Operational + Analytical)**
 2.1 Modeling Principles
 2.2 High-Level Entity Map
 2.3 Core Operational Tables
 2.4 Analytical / Dimensional Structures
 2.5 Entity Relationships & Integrity Rules

**3. Data Dictionary (Fields, Types, Rules, Usage)**
 3.1 Attribute Conventions
 3.2 Customer Domain Fields
 3.3 Policy Domain Fields
 3.4 Claims Domain Fields
 3.5 Underwriting Domain Fields
 3.6 Pricing & Profitability Fields
 3.7 Shared Dimensions and Lookup Structures

**4. ETL/ELT Functional Requirements (Pipeline A–D)**
 4.1 Module A – Configuration Builder
 4.2 Module B – Synthetic Data Generator
  4.2.1 Customer Engine
  4.2.2 Policy Engine
  4.2.3 Claims Engine
  4.2.4 Underwriting Engine
  4.2.5 Retention Engine
  4.2.6 Pricing Engine
 4.3 Module C – Normalization & Enhancement
 4.4 Module D – Loader & BI Output Layer

**5. Transformations & Derived Metrics**
 5.1 Claims Derivations
 5.2 Retention & Churn Derivations
 5.3 Underwriting Derivations
 5.4 Pricing & Profitability Derivations
 5.5 Date, Time, and Exposure Derivations

**6. Quality Gates & HealthChecks**
 6.1 Purpose of Analytical Quality Controls
 6.2 Validation Categories
 6.3 Domain-Specific HealthChecks
 6.4 Cross-Domain Consistency Rules
 6.5 Determinism & Reproducibility Validations

**7. BI Output & Consumption Contract**
 7.1 File Formats & Storage Standards
 7.2 Dataset Naming Conventions
 7.3 Mandatory Columns by Output Table
 7.4 Grain & Partitioning Requirements
 7.5 Dashboard-Specific Data Guarantees



# **1. Scope & Business Analytical Requirements**



## **1.1 Purpose**

This Functional Specification Requirements (FSR) document defines the analytical, functional, and data-engineering requirements for a synthetic data pipeline designed **exclusively** to support **four core insurance dashboards**:

* Claims & Loss Analysis
* Retention & Churn
* Underwriting Operations
* Pricing & Profitability

Each requirement, entity, transformation, and rule exists strictly to enable accurate KPI computation, segmentation, trends, and visualization for these dashboards.
No functionality outside this analytical purpose is included.



## **1.2 Analytical Context**

The insurance industry depends on analytics to monitor risk exposure, customer behavior, loss performance, underwriting efficiency, and pricing adequacy.

This project generates a **high-fidelity synthetic dataset** that behaves like a real multi-line portfolio:

* Customers with realistic demographic, behavioral, and risk attributes
* Policies with lifecycle events, premiums, cancellations, and payments
* Claims with frequency, severity, fraud indicators, and lifecycle timestamps
* Quotes with underwriting decisions and conversion paths
* Pricing attributes such as loss development, expenses, and market comparison

The pipeline produces data ready for BI dashboards, but does not aim to replicate real insurance administration systems.



## **1.3 Dashboard-Driven Scope**

The analytical scope is **entirely defined** by the data needs of the four dashboards.
Key principles:

* **Nothing is added unless a dashboard requires it.**
* **Every metric appearing on a dashboard must be fully supported.**
* **All tables must contain only the fields necessary for KPI computation and filtering.**
* **Data model complexity is minimized but must remain analytically correct.**

Consequently:

* Claims data must support loss ratio, severity, frequency, pipeline aging, fraud signals.
* Retention data must support churn detection, cohort analysis, tenure, CLV, and campaign impact.
* Underwriting data must support quote-to-bind, processing times, STP rate, and underwriter performance.
* Pricing data must support combined ratio, loss cost trends, rate adequacy, expense ratios, ROE, and market comparison.



## **1.4 Out-of-Scope Items**

To ensure a lean analytical pipeline, the following are **explicitly excluded**:

* Real underwriting decision algorithms
* Real actuarial pricing models (GLM, credibility, stochastic reserving)
* Predictive ML models (fraud/churn scores will be synthetic)
* Operational systems such as billing, CRM, PAS, or claims administration
* Regulatory reporting structures (e.g., Solvency II QRTs)
* Multi-entity, multi-currency accounting layers

The goal is **analytical simulation**, not operational replication.



# **2. Business Analytical Requirements Overview**



## **2.1 Claims & Loss Analysis Requirements**

### **Key analytical capabilities**

* Loss Ratio (earned premium vs incurred loss)
* Claim frequency and severity metrics
* Trend analysis (12M rolling, YoY)
* Severity distributions and severity bands
* Lifecycle timing metrics (reporting delay, settlement delay)
* Open-claim pipeline visualization
* Adjuster performance slicing
* Geographic segmentation (state, city)
* Fraud Score (synthetic, rule-based)

### **Data behaviors required**

* Chronologically valid sequences (occurrence ≤ report ≤ close)
* Paid amounts linked to claims with correct dates
* Reserved amounts present even if no payments occur
* Ability to derive incurred loss (paid + reserve)
* Each claim tied to a valid active policy at its occurrence date



## **2.2 Retention & Churn Analysis Requirements**

### **Key analytical capabilities**

* Retention rate, churn rate, net customer movement
* Cohort-based retention visualization
* Customer tenure in months
* Churn flag, date, and reason
* Behavioral indicators (days since last payment)
* Churn Score (synthetic risk indicator)
* CLV estimation
* Cross-sell and multi-product analysis
* Retention campaign effectiveness metrics

### **Data behaviors required**

* Customer lifecycle must support Active → Churned transitions
* Payment timing must allow lapse/churn tendencies
* Cohort derivation via acquisition or first-policy date
* Customer-aggregated metrics (claims count, premium totals, product count)



## **2.3 Underwriting Operations Requirements**

### **Key analytical capabilities**

* Quote-to-bind ratio
* Hit ratio by channel, product, underwriter
* STP rate (auto-approval)
* Time-to-quote and time-to-bind
* Underwriting funnel (Requested → Quoted → Accepted → Bound)
* Decline reason categorization
* Risk classification distribution
* Underwriter productivity and efficiency

### **Data behaviors required**

* Timestamped quote states must follow logical order
* Bound quotes must map 1:1 with issued policies
* Underwriter attributes must be stable (level, authority)
* Risk class and risk score required for slicing



## **2.4 Pricing & Profitability Requirements**

### **Key analytical capabilities**

* Combined Ratio (Loss + Expense)
* Expense Ratio by product and time period
* Technical Margin calculations
* Pure Premium components
* Rate Adequacy Index (our premium vs technically required premium)
* ROE (Return on Equity)
* Loss cost trends via simplified development snapshots
* Market competitiveness versus competitor premiums

### **Data behaviors required**

* Earned premium must be derivable from policy exposure period
* Loss development must provide sequential development months
* Expense data must align with product and time period
* Market prices must map to same segments as internal policies
* Pricing segments must be well defined (risk class, age band, region)



# **3. Cross-Domain Analytical Requirements**



## **3.1 Shared Entities**

The following entities must remain consistent across all domains:

* Customers
* Policies
* Products / Lines of business
* Geography
* Time attributes (month, year, reporting periods)
* Risk indicators

These shared structures enable coherent slicing across dashboards.



## **3.2 Shared Metrics & Derived Attributes**

Critical derived fields reused in multiple dashboards:

* Tenure (months)
* Age band
* Risk score
* Earned premium
* Claim severity band
* Days since last payment
* Processing time (quotes)
* Churn flag
* Churn score
* Quote-to-bind indicator
* Frequency denominators (exposure)



## **3.3 Consistency & Integrity Rules**

Analytical correctness requires:

* Bound quotes must produce policies
* Policies must map to customers
* Claims must map to valid policies during active coverage
* Earned premium must not be negative
* Churned customers cannot have active policies
* Development snapshots must follow chronological progression



# **4. Analytical Assumptions & Constraints**



## **4.1 Synthetic Data Simulation Principles**

The pipeline will simulate:

* Realistic frequency and severity patterns
* Payment behaviors and churn phenomena
* Underwriting activity levels
* Market pricing differences
* Loss development over time

All values must remain statistically coherent and reproducible.



## **4.2 Determinism Requirements**

A fixed seed must produce identical:

* customer population
* policy portfolio
* claims
* quotes and underwriting outcomes
* loss development snapshots
* synthetic fraud/churn/risk scores



## **4.3 Granularity & Time Windows**

Required analytic grains:

* Daily → claims, quotes, lifecycle timestamps
* Monthly → earned premium, cohorts, payment behavior
* Annual → underwriting year, accident year



## **4.4 Data Volume Targets**

Configurable, with typical ranges:

* Customers: 5,000–100,000
* Policies: 1–3 per customer
* Claims: 5–20% claim rate depending on product
* Quotes: 3–5× policy count
* Development snapshots: 3–6 development periods
* Campaign records: a few thousand events



# **2. Data Model Specification (Operational + Analytical)**

## **2.1 Modeling Principles**

### **2.1.1 Dashboard-Driven Modeling**

The data model is built exclusively to support the analytical and KPI requirements of the four dashboards:

* Claims & Loss Analysis
* Retention & Churn
* Underwriting Operations
* Pricing & Profitability

No table, field, or relationship is included unless it directly supports one or more dashboard calculations, segmentations, or filters.

### **2.1.2 Hybrid Operational–Analytical Schema**

The model combines:

* **Operational-style synthetic source tables** (customers, policies, claims, quotes, payments…)
* **Analytical/derived structures** (summaries, development snapshots, pricing segments, exposure metrics)

This ensures both granular events and aggregated metrics are available for BI.

### **2.1.3 Referential Integrity Across All Domains**

The following constraints must always hold:

* A policy must have a valid customer.
* A claim must reference a valid policy active during the occurrence date.
* A bound quote must reference an issued policy.
* Pricing segments must map to policies and/or customers via dimension attributes.
* Development snapshots must reference valid policies and accident years.

### **2.1.4 Temporal Coherence**

All timestamps must respect insurance lifecycle chronology:

Quote → Bind → Policy Effective → Claim Occurrence → Claim Report → Claim Close → Claim Payments

### **2.1.5 Analytical Granularity**

The model supports:

* **Daily granularity** for claims and underwriting timelines
* **Monthly granularity** for earned premium, cohorts, churn, development periods
* **Annual granularity** for underwriting year and accident year



## **2.2 High-Level Entity Map**

The analytical model is composed of **12 core entities**, grouped by domain.

### **2.2.1 Customer & Retention Domain**

* customers
* customer_policies_summary
* retention_campaigns

### **2.2.2 Policy & Product Domain**

* policies
* products (embedded as attributes, not a standalone table unless needed)
* geographic attributes (embedded state/city fields)

### **2.2.3 Claims Domain**

* claims_master
* claims_payments
* adjusters

### **2.2.4 Underwriting Domain**

* quotes
* underwriters
* agents
* production_targets

### **2.2.5 Pricing & Profitability Domain**

* loss_development
* expenses
* pricing_segments
* capital_allocation
* market_data

These entities collectively support all KPIs and analytic views required for the four dashboards.



## **2.3 Core Operational Tables**

This subsection specifies the minimal operational-style tables required to feed analytical processing.



### **2.3.1 customers**

**Purpose:**
Captures demographic, geographic, and lifecycle attributes used across retention, claims segmentation, underwriting, and pricing.

**Key Fields:**

* customer_id (PK)
* customer_since (date)
* status (Active, Churned, Suspended)
* churn_date (nullable)
* churn_reason
* age, gender, occupation, marital_status
* state, city
* acquisition_channel
* referral_source
* risk_profile (synthetic low/medium/high)

**Analytical Uses:**

* Cohorts
* Churn metrics
* Demographic segmentation
* Risk grouping
* Filtering across dashboards



### **2.3.2 policies**

**Purpose:**
Central entity linking customers, underwriting outcomes, claims exposure, and pricing structures.

**Key Fields:**

* policy_id (PK)
* customer_id (FK)
* quote_id (FK, nullable)
* product_line
* coverage_amount
* deductible
* premium_written
* premium_earned (derived)
* policy_status (Active, Lapsed, Cancelled, Expired)
* effective_date
* expiration_date
* cancellation_date
* cancellation_reason
* payment_frequency
* last_payment_date
* days_since_last_payment (derived)
* risk_score (synthetic)
* underwriting_year
* accident_year
* state, city

**Analytical Uses:**

* Loss ratio components
* Retention and churn triggers
* Underwriting conversion
* Pricing adequacy and profitability
* Exposure-based metrics



### **2.3.3 claims_master**

**Purpose:**
Represents claim lifecycle and financial aspects required for severity, frequency, and incurred-loss analytics.

**Key Fields:**

* claim_id (PK)
* policy_id (FK)
* occurrence_date
* report_date
* close_date
* claim_status
* claim_type
* cause_of_loss
* reserved_amount
* paid_amount (latest known)
* total_incurred (derived = paid_amount + reserved_amount)
* fraud_score (synthetic, rule-based)
* reopened_flag
* legal_representation_flag
* state, city
* adjuster_id (FK)

**Analytical Uses:**

* Frequency, severity KPIs
* Fraud analysis
* Loss ratio inputs
* Claim lifecycle and aging
* Geographic loss distribution



### **2.3.4 claims_payments**

**Purpose:**
Captures cash movement related to claims, enabling payment trends, settlement times, and incurred vs paid reconciliations.

**Key Fields:**

* payment_id (PK)
* claim_id (FK)
* payment_date
* payment_amount
* payment_type (Indemnity, Medical, Legal, Deductible)

**Analytical Uses:**

* Settlement timeline
* Severity confirmation
* Loss development snapshots
* Monetary analysis



### **2.3.5 quotes**

**Purpose:**
Captures underwriting activity and conversion lifecycle.

**Key Fields:**

* quote_id (PK)
* quote_number
* request_date
* quote_date
* quote_expiration_date
* quote_status (Requested, Quoted, Accepted, Bound, Declined, Expired)
* decline_reason
* product_line
* coverage_amount
* quoted_premium
* risk_class
* risk_score
* stp_flag (straight-through processing)
* referral_flag
* state, city
* branch_id
* underwriter_id (FK)
* agent_id (FK)

**Analytical Uses:**

* Quote-to-bind ratio
* Hit ratio
* Time-to-quote, time-to-bind
* Underwriter performance
* Funnel analytics



### **2.3.6 underwriters**

**Purpose:**
Represents underwriting staff for performance slicing.

**Key Fields:**

* underwriter_id (PK)
* underwriter_name
* underwriter_level (Junior, Senior, Principal)
* authority_limit
* branch_id



### **2.3.7 agents**

**Purpose:**
Represents distribution channels for segmentation.

**Key Fields:**

* agent_id (PK)
* agent_name
* agent_type (Captive, Independent, Broker)
* branch_id
* state



### **2.3.8 retention_campaigns**

**Purpose:**
Captures customer-level retention interactions.

**Key Fields:**

* campaign_id (PK)
* customer_id (FK)
* campaign_type (Win-back, Renewal, Cross-sell)
* contact_date
* responded_flag
* retained_flag
* additional_premium



## **2.4 Analytical / Dimensional Structures**

These structures provide aggregated or derived metrics required for pricing, profitability, forecasting, trend analysis, and dashboard visualizations.



### **2.4.1 customer_policies_summary**

**Purpose:**
Aggregated table providing customer-level metrics for retention and risk analysis.

**Key Fields:**

* customer_id (PK)
* total_policies
* active_policies
* total_premium_annual
* tenure_months (derived)
* total_claims
* total_claims_amount
* engagement_score (synthetic)
* nps_score
* last_contact_date



### **2.4.2 loss_development**

**Purpose:**
Simplified loss development snapshots required for pricing KPIs and loss cost trends.

**Key Fields:**

* policy_id (FK)
* accident_year
* development_month (e.g., 12, 24, 36)
* incurred_losses
* paid_losses
* case_reserves
* ibnr_reserves (synthetic optional)



### **2.4.3 expenses**

**Purpose:**
Expense allocation for calculating expense ratio and combined ratio.

**Key Fields:**

* expense_id (PK)
* period (YYYY-MM)
* product_line
* expense_type (Commission, Salary, IT, Marketing, Overhead)
* expense_amount
* policy_count_for_metric



### **2.4.4 pricing_segments**

**Purpose:**
Captures segment-level attributes required to compute rate adequacy and competitive pricing analysis.

**Key Fields:**

* segment_id (PK)
* product_line
* state
* risk_class
* age_band
* technically_required_premium
* our_average_premium
* market_average_premium
* exposure_count
* loss_ratio_expected



### **2.4.5 capital_allocation**

**Purpose:**
Inputs required for ROE and technical profitability KPIs.

**Key Fields:**

* product_line (PK)
* underwriting_year (PK)
* capital_allocated
* risk_charge
* target_roe



### **2.4.6 market_data**

**Purpose:**
Simulated competitor pricing and market share data.

**Key Fields:**

* competitor_id
* product_line
* state
* coverage_type
* average_premium
* market_share
* date_snapshot



## **2.5 Entity Relationships & Integrity Rules**

**2.5.1 Customer–Policy Relationship**

* A customer may hold multiple policies.
* A policy must belong to exactly one customer.

**2.5.2 Policy–Claim Relationship**

* A policy may have zero or many claims.
* A claim must map to one active policy at the time of occurrence.

**2.5.3 Quote–Policy Relationship**

* A bound quote must produce exactly one policy.
* Unbound quotes do not generate policies.

**2.5.4 Claim–Payment Relationship**

* A claim may have zero or many payments.
* Payment dates must fall between report_date and close_date.

**2.5.5 Pricing Segment Consistency**

* Pricing segments must align with product_line, state, and risk attributes present in policies.

**2.5.6 Temporal Coherence**
All date sequences must follow:

request_date ≤ quote_date ≤ bind_date ≤ effective_date ≤ expiration_date
and
effective_date ≤ occurrence_date ≤ close_date



# **3. Data Dictionary (Fields, Types, Rules, Usage)**

This section defines the authoritative field-level specification for every table described in the Data Model.
Each attribute includes:

* **Type**: logical data type
* **Rule / Constraint**: functional requirement
* **Usage**: dashboards or KPIs dependent on the attribute

Only fields required by the four dashboards are included.



# **3.1 Attribute Conventions**

### **3.1.1 ID Fields**

All primary keys must be:

* Unique
* Non-null
* Deterministic under fixed seed generation
* Prefixed by domain where applicable (e.g., claim_id, quote_id)

### **3.1.2 Date & Timestamp Fields**

All dates must:

* Use ISO format `YYYY-MM-DD`
* Respect logical order (e.g., occurrence_date ≤ report_date)

### **3.1.3 Currency Fields**

All currency values:

* Stored as decimal(12,2)
* Must be ≥ 0
* Derived metrics must reference source currency fields without rounding errors

### **3.1.4 Categorical Fields**

Must use controlled vocabularies:

* claim_status = {Open, Closed, Denied, Pending}
* quote_status = {Requested, Quoted, Accepted, Bound, Declined, Expired}
* policy_status = {Active, Lapsed, Cancelled, Expired}
* gender = {Male, Female, Other}
* agent_type = {Captive, Independent, Broker}



# **3.2 Customer Domain Fields**



## **3.2.1 Table: customers**

| Field               | Type    | Rule / Constraint                     | Usage                          |
| - | - | - |  |
| customer_id         | string  | PK, unique                            | All dashboards                 |
| customer_since      | date    | Must be ≤ first policy effective date | Cohorts, retention             |
| status              | string  | {Active, Churned, Suspended}          | Retention, pricing segments    |
| churn_date          | date    | Null unless status=Churned            | Churn metrics                  |
| churn_reason        | string  | Controlled vocabulary                 | Churn drivers                  |
| age                 | integer | 18–90                                 | Segmentation                   |
| gender              | string  | Controlled set                        | Claims, retention segmentation |
| occupation          | string  | Optional, synthetic categories        | Pricing, segmentation          |
| marital_status      | string  | {Single, Married, Divorced, Widowed}  | Pricing segments               |
| state               | string  | Must align with geography list        | Claims heatmaps                |
| city                | string  | Must align with selected state        | Geographic dashboards          |
| acquisition_channel | string  | {Agent, Broker, Digital, Referral}    | UW, retention                  |
| referral_source     | string  | Nullable                              | Marketing analytics            |
| risk_profile        | string  | {Low, Medium, High}                   | Pricing, underwriting          |



## **3.2.2 Table: customer_policies_summary**

| Field                | Type          | Rule / Constraint           | Usage                    |
| -- | - |  |  |
| customer_id          | string        | PK, FK → customers          | Retention                |
| total_policies       | integer       | ≥ 0                         | Customer portfolio value |
| active_policies      | integer       | ≥ 0                         | Retention risk           |
| total_premium_annual | decimal(12,2) | Sum of premium_written      | CLV                      |
| tenure_months        | integer       | Derived from customer_since | Cohorts, tenure          |
| total_claims         | integer       | ≥ 0                         | Churn prediction         |
| total_claims_amount  | decimal(12,2) | Sum of incurred             | CLV, retention           |
| engagement_score     | integer       | 0–100 synthetic             | Churn risk               |
| nps_score            | integer       | 0–10 synthetic              | Risk/churn drivers       |
| last_contact_date    | date          | Optional                    | Retention analytics      |



# **3.3 Policy Domain Fields**



## **3.3.1 Table: policies**

| Field                   | Type          | Rule / Constraint                    | Usage                   |
| -- | - |  | -- |
| policy_id               | string        | PK                                   | All dashboards          |
| customer_id             | string        | FK → customers                       | All dashboards          |
| quote_id                | string        | Nullable FK                          | Underwriting conversion |
| product_line            | string        | {Auto, Life, Health, Property, etc.} | All dashboards          |
| coverage_amount         | decimal(12,2) | ≥0                                   | Pricing, underwriting   |
| deductible              | decimal(12,2) | ≥0                                   | Pricing segmentation    |
| premium_written         | decimal(12,2) | ≥0                                   | Pricing, retention      |
| premium_earned          | decimal(12,2) | Derived monthly exposure             | Loss ratio              |
| policy_status           | string        | {Active, Lapsed, Cancelled, Expired} | Retention               |
| effective_date          | date          | ≤ expiration_date                    | All dashboards          |
| expiration_date         | date          | ≥ effective_date                     | All dashboards          |
| cancellation_date       | date          | Null unless policy_status=Cancelled  | Churn                   |
| cancellation_reason     | string        | Controlled set                       | Churn drivers           |
| payment_frequency       | string        | {Monthly, Quarterly, Annual}         | Retention               |
| last_payment_date       | date          | Required for Active policies         | Lapse detection         |
| days_since_last_payment | integer       | Derived                              | Churn score             |
| risk_score              | integer       | 0–100 synthetic                      | Pricing, underwriting   |
| underwriting_year       | integer       | Extract from bind/effective          | Pricing                 |
| accident_year           | integer       | For claims alignment                 | Pricing                 |
| state                   | string        | Required                             | Geographic slicing      |
| city                    | string        | Required                             | Geographic slicing      |



# **3.4 Claims Domain Fields**



## **3.4.1 Table: claims_master**

| Field                     | Type    | Rule / Constraint                                        | Usage               |
| - | - | -- | - |
| claim_id                  | string  | PK                                                       | Claims dashboard    |
| policy_id                 | string  | FK → policies                                            | All claims KPIs     |
| occurrence_date           | date    | ≤ report_date                                            | Frequency           |
| report_date               | date    | ≤ close_date                                             | Operational metrics |
| close_date                | date    | Null if still open                                       | Settlement KPIs     |
| claim_status              | string  | {Open, Closed, Denied, Pending}                          | Pipeline            |
| claim_type                | string  | {Theft, Collision, Medical, Death, PropertyDamage, etc.} | Severity slicing    |
| cause_of_loss             | string  | Controlled vocabulary                                    | Analytics           |
| reserved_amount           | decimal | ≥0                                                       | Incurred loss       |
| paid_amount               | decimal | ≥0                                                       | Incurred loss       |
| total_incurred            | decimal | Derived = reserved + paid                                | Loss ratio          |
| fraud_score               | integer | 0–100 synthetic                                          | Fraud analytics     |
| reopened_flag             | boolean | True/False                                               | Reopen rate         |
| legal_representation_flag | boolean | True/False                                               | Claims mix          |
| state                     | string  | Must match policy state                                  | Heatmaps            |
| city                      | string  | Must match policy city                                   | Heatmaps            |
| adjuster_id               | string  | FK                                                       | Operational slicing |



## **3.4.2 Table: claims_payments**

| Field          | Type    | Rule / Constraint                       | Usage              |
| -- | - |  |  |
| payment_id     | string  | PK                                      | Payment analysis   |
| claim_id       | string  | FK → claims_master                      | Linking            |
| payment_date   | date    | Between report and close date           | Time-to-settlement |
| payment_amount | decimal | ≥0                                      | Cashflow           |
| payment_type   | string  | {Indemnity, Medical, Legal, Deductible} | Expense/injury mix |



# **3.5 Underwriting Domain Fields**



## **3.5.1 Table: quotes**

| Field                 | Type    | Rule / Constraint                            | Usage                       |
|  | - | -- |  |
| quote_id              | string  | PK                                           | UW funnel                   |
| quote_number          | string  | Unique                                       | Reference                   |
| request_date          | date    | Start of funnel                              | Time-to-quote               |
| quote_date            | date    | ≥ request_date                               | Time-to-quote               |
| quote_expiration_date | date    | ≥ quote_date                                 | Pipeline                    |
| quote_status          | string  | Lifecycle enum                               | Funnel, hit ratio           |
| decline_reason        | string  | Null unless Declined                         | Root-cause                  |
| product_line          | string  | Required                                     | Segmentation                |
| coverage_amount       | decimal | ≥0                                           | Risk profile                |
| quoted_premium        | decimal | ≥0                                           | Pricing comparison          |
| risk_class            | string  | {Preferred, Standard, Substandard, Declined} | UW slicing                  |
| risk_score            | integer | 0–100 synthetic                              | UW scoring                  |
| stp_flag              | boolean | Straight-through processing                  | Efficiency                  |
| referral_flag         | boolean | Indicates manual review                      | UW mix                      |
| state                 | string  | Required                                     | Geographic slicing          |
| city                  | string  | Required                                     | Geographic slicing          |
| branch_id             | string  | Required                                     | Production target alignment |
| underwriter_id        | string  | FK                                           | Underwriter performance     |
| agent_id              | string  | FK                                           | Channel performance         |



## **3.5.2 Table: underwriters**

| Field             | Type    | Rule / Constraint           | Usage                  |
| -- | - |  | - |
| underwriter_id    | string  | PK                          | Performance            |
| underwriter_name  | string  | Required                    | Display                |
| underwriter_level | string  | {Junior, Senior, Principal} | Segmentation           |
| authority_limit   | decimal | ≥0                          | Risk assignment        |
| branch_id         | string  | Required                    | Geographical alignment |



## **3.5.3 Table: agents**

| Field      | Type   | Rule / Constraint              | Usage                   |
| - |  |  | -- |
| agent_id   | string | PK                             | Channel analysis        |
| agent_name | string | Required                       | Display                 |
| agent_type | string | {Captive, Independent, Broker} | Channel mix             |
| branch_id  | string | Required                       | Production targets      |
| state      | string | Required                       | Geographic segmentation |



# **3.6 Pricing & Profitability Fields**



## **3.6.1 Table: loss_development**

| Field             | Type    | Rule / Constraint | Usage               |
| -- | - | -- | - |
| policy_id         | string  | FK                | Loss cost trend     |
| accident_year     | integer | Required          | Trend alignment     |
| development_month | integer | {12, 24, 36…}     | Period order        |
| incurred_losses   | decimal | ≥0                | Loss cost           |
| paid_losses       | decimal | ≥0                | Paid trend          |
| case_reserves     | decimal | ≥0                | Development         |
| ibnr_reserves     | decimal | ≥0 synthetic      | Development context |



## **3.6.2 Table: expenses**

| Field                   | Type             | Rule / Constraint                           | Usage         |
| -- | - | - | - |
| expense_id              | string           | PK                                          | Tracking      |
| period                  | string (YYYY-MM) | Required                                    | Expense ratio |
| product_line            | string           | Required                                    | Allocation    |
| expense_type            | string           | Commission, Salary, IT, Marketing, Overhead | Breakdown     |
| expense_amount          | decimal          | ≥0                                          | Expense ratio |
| policy_count_for_metric | integer          | ≥0                                          | Unit cost     |



## **3.6.3 Table: pricing_segments**

| Field                        | Type    | Rule / Constraint | Usage               |
| - | - | -- | - |
| segment_id                   | string  | PK                | Segment tracking    |
| product_line                 | string  | Required          | Alignment           |
| state                        | string  | Required          | Geo segmentation    |
| risk_class                   | string  | Required          | Pricing alignment   |
| age_band                     | string  | {18–25, 26–35…}   | Market segmentation |
| technically_required_premium | decimal | ≥0                | Rate adequacy       |
| our_average_premium          | decimal | ≥0                | Adequacy            |
| market_average_premium       | decimal | ≥0                | Competitiveness     |
| exposure_count               | integer | ≥0                | Credibility         |
| loss_ratio_expected          | decimal | 0–100             | Pricing indicator   |



## **3.6.4 Table: capital_allocation**

| Field             | Type    | Rule / Constraint | Usage           |
| -- | - | -- |  |
| product_line      | string  | Part of PK        | ROE             |
| underwriting_year | integer | Part of PK        | ROE             |
| capital_allocated | decimal | ≥0                | ROE calculation |
| risk_charge       | decimal | ≥0                | Profitability   |
| target_roe        | decimal | ≥0                | Benchmark       |



## **3.6.5 Table: market_data**

| Field           | Type    | Rule / Constraint | Usage               |
|  | - | -- | - |
| competitor_id   | string  | PK component      | Comparison          |
| product_line    | string  | Required          | Alignment           |
| state           | string  | Required          | Geo match           |
| coverage_type   | string  | Required          | Comparison slice    |
| average_premium | decimal | ≥0                | Competitive pricing |
| market_share    | decimal | 0–100             | Benchmark           |
| date_snapshot   | date    | Required          | Time slicing        |



# **4. ETL/ELT Functional Requirements (Pipeline A–D)**

This section defines the full functional behavior of the synthetic data pipeline.
The pipeline consists of four modules:

* **Module A – Configuration Builder**
* **Module B – Synthetic Data Generator**
* **Module C – Normalization & Enhancement**
* **Module D – Loader & BI Output Layer**

All modules must operate deterministically when provided with a fixed random seed.



# **4.1 Module A – Configuration Builder**

Module A gathers the parameters that determine the **size**, **distribution**, and **behavior** of the synthetic portfolio.



## **4.1.1 Functional Purpose**

The configuration builder:

* Accepts user input for portfolio size and simulation complexity
* Generates a structured configuration object (`config.json`)
* Ensures constraints between parameters (e.g., claims volume proportional to product mix)
* Provides defaults when inputs are omitted
* Produces deterministic seeds for the generator



## **4.1.2 Required Input Parameters**

| Parameter                 | Description                                | Constraints        |
| - |  |  |
| num_customers             | Number of customers to generate            | ≥ 1000 recommended |
| avg_policies_per_customer | Coverage density                           | 1–3 typical        |
| claim_rate                | Probability a policy has ≥1 claim per year | 5–20%              |
| quote_multiplier          | Quotes generated per expected policy       | 3–5                |
| years_of_history          | Simulation window                          | 1–5 years          |
| region_distribution       | Mapping of customers by region             | Must sum to 100%   |
| product_mix               | Share by product line                      | Must sum to 100%   |
| random_seed               | Optional deterministic seed                | Integer            |



## **4.1.3 Functional Rules**

1. If `random_seed` is provided, it must be propagated to all modules.
2. Product mix must control both policy and quote generation.
3. Claim rate must determine expected number of claims per policy-year.
4. Historical years must constrain possible occurrence, report, and payment dates.
5. Region distribution must drive customers, policies, quotes, and claims geography.



## **4.1.4 Output**

Module A produces:

* `config.json` containing all validated inputs
* Derived parameters such as:

  * expected_policies = num_customers × avg_policies_per_customer
  * expected_quotes = expected_policies × quote_multiplier
  * expected_claims = expected_policies × claim_rate



# **4.2 Module B – Synthetic Data Generator**

Module B synthesizes raw operational data across all insurance domains.
It contains **six independent generation engines** that run in sequence but remain logically modular.



## **4.2.1 Customer Engine**

### Functional Purpose

Generates customer records with demographic, geographic, and lifecycle attributes matching the required distributions.

### Functional Rules

1. Age distribution must follow configurable demographic curves.
2. Geography must follow the region distribution provided in the configuration.
3. Risk profile must be correlated with age, geography, and product tendencies.
4. Customer_since must fall within the simulation window.
5. Churned customers must receive churn_date and churn_reason.



## **4.2.2 Policy Engine**

### Functional Purpose

Creates policies linked to customers with appropriate coverage, dates, premiums, and status.

### Functional Rules

1. Effective and expiration dates must fall within allowed simulation years.
2. Cancellation must occur only after effective_date.
3. Premium_written must be consistent with product_line risk.
4. Risk_score must be correlated with premium and product-line risk profile.
5. Payment frequency must follow synthetic distributions (e.g., 60% monthly, 30% annual).
6. Earned premium is not generated here; will be derived in Module C.



## **4.2.3 Claims Engine**

### Functional Purpose

Simulates claims with realistic severity, frequency, and lifecycle processes.

### Functional Rules

1. Occurrence_date must fall between policy effective and expiration.
2. Report_date must be ≥ occurrence_date and subject to random reporting delays.
3. Close_date must be ≥ report_date, unless claim remains open.
4. Claim_type and cause_of_loss must follow product-specific distributions.
5. Reserved_amount and paid_amount must follow synthetic severity curves.
6. Fraud_score must be rule-based and deterministic under seed.
7. Payment events must be generated probabilistically (0–n payments per claim).



## **4.2.4 Underwriting Engine**

### Functional Purpose

Simulates the quote lifecycle and conversion to policies.

### Functional Rules

1. request_date must fall within simulation timeline.
2. quote_date must be ≥ request_date.
3. quote_status must follow funnel probabilities: Requested → Quoted → (Accepted/Declined/Expired) → Bound.
4. Bound quotes must link to actual policies generated earlier.
5. quoted_premium must be consistent with product risk.
6. risk_class and risk_score must align with underwriting decision logic.
7. STP decisions must be applied based on risk thresholds.



## **4.2.5 Retention Engine**

### Functional Purpose

Generates customer-level behavioral indicators and retention campaign interactions.

### Functional Rules

1. days_since_last_payment must align with payment_frequency.
2. churn_score must correlate with behavioral risk factors (engagement, payment history, claims).
3. retention_campaigns must be generated for at-risk customers.
4. campaign outcomes (responded_flag, retained_flag) must follow plausible success rates.



## **4.2.6 Pricing Engine**

### Functional Purpose

Simulates pricing segment attributes, loss development snapshots, expense structures, and competitor pricing.

### Functional Rules

1. Development periods must increment sequentially (e.g., 12 → 24 → 36 months).
2. incurred_losses and paid_losses must increase monotonically with development period.
3. technically_required_premium must reflect risk_class and segment attributes.
4. market_average_premium must differ across competitors by ±10–25%.
5. expenses must follow product-line proportions.
6. capital_allocation must align with product risk and underwriting_year.



# **4.3 Module C – Normalization & Enhancement**

Module C transforms raw generated data into **BI-ready analytical tables**, enforces referential integrity, and derives required metrics.



## **4.3.1 Standardization Rules**

1. All date fields must be converted to ISO format.
2. All numeric fields must be cast into correct decimal/integer types.
3. Controlled vocabularies must be validated (status fields, categories).
4. Duplicate and inconsistent records must be removed or corrected.



## **4.3.2 Referential Integrity Enforcement**

1. Verify all policies reference valid customers.
2. Verify all claims reference valid policies with correct temporal alignment.
3. Verify all bound quotes reference exactly one policy.
4. Verify all underwriting and pricing attributes reference valid segments.

Invalid records must be filtered out with deterministic rules.



## **4.3.3 Derived Metrics Computation**

Module C must compute all KPI-critical fields:

### Claims

* total_incurred = paid_amount + reserved_amount
* days_to_settlement = close_date − report_date
* severity_band based on paid_amount quantiles

### Retention

* tenure_months = months between customer_since and churn_date or current date
* churn_flag = 1 if status=Churned
* payment behavior attributes

### Underwriting

* time_to_quote
* time_to_bind
* quote_to_bind_flag

### Pricing

* earned_premium via pro-rata exposure
* loss development completeness checks
* rate_adequacy_index components



# **4.4 Module D – Loader & BI Output Layer**

Module D writes final datasets to the analytical output layer and prepares files for BI consumption.



## **4.4.1 Output Data Requirements**

The module must generate:

* Structured output files (CSV/Parquet)
* Supabase table loads (if configured)
* Clean dictionary metadata for BI teams



## **4.4.2 Naming & Storage Rules**

1. Each table must be exported using lowercase snake_case names.
2. Partitioning must be applied by year or month for large tables.
3. Loader must maintain versioned folders (e.g., `v1`, `v1_run_001`).



## **4.4.3 BI Consumption Guarantees**

To ensure the dashboards function:

1. All required columns must be present with expected data types.
2. No nulls in critical fields (IDs, statuses, dates).
3. All foreign keys must resolve valid references.
4. All derived fields must be precomputed—BI must not compute logic beyond simple aggregations.



# **5. Transformations & Derived Metrics**

This section defines all computed fields required for KPI calculation, segmentation, filtering, and visualizations across the four dashboards.
Each transformation must be implemented deterministically and consistently across the pipeline.

Transformations fall into four analytical domains:

* Claims
* Retention & Churn
* Underwriting
* Pricing & Profitability

A fifth category defines date- and exposure-based derivations used across multiple domains.

Only transformations explicitly required by dashboard logic are included.



# **5.1 Claims Derivations**

Claims transformations support loss analysis, severity and frequency metrics, fraud signals, lifecycle timing, and incurred loss calculations.



## **5.1.1 total_incurred**

**Definition:**

```
total_incurred = paid_amount + reserved_amount
```

**Rules:**

* Must be recalculated if either source field changes.
* Must never be negative.

**Usage:**
Loss Ratio, severity metrics, incurred trends.



## **5.1.2 days_to_settlement**

**Definition:**

```
days_to_settlement = close_date - report_date
```

**Rules:**

* Null if claim_status != "Closed".
* Must be ≥ 0 for valid records.

**Usage:**
Settlement efficiency KPIs, claim pipeline analytics.



## **5.1.3 reporting_delay**

**Definition:**

```
reporting_delay = report_date - occurrence_date
```

**Rules:**

* Must be ≥ 0.

**Usage:**
Fraud scoring input, operational SLAs, claims behavior analysis.



## **5.1.4 severity_band**

**Definition:**
Categorizes claims based on paid_amount distribution:

* Micro: < $1,000
* Small: $1,000–$10,000
* Medium: $10,000–$50,000
* Large: > $50,000

**Rules:**

* Thresholds configurable per product line.
* Must be based on paid_amount or total_incurred (configurable).

**Usage:**
Severity dashboards, segmentation, frequency vs severity scatterplots.



## **5.1.5 claim_age_bucket**

**Definition:**
Buckets for open claims based on time since report_date:

* 0–15 days
* 16–30 days
* 31–60 days
* 61+ days

**Rules:**

* Only applies to open claims.

**Usage:**
Aging funnel visualization, operational performance.



## **5.1.6 fraud_score**

**Definition:**
Synthetic rule-based scoring (0–100).

**Inputs:**

* reporting_delay
* severity deviation flags
* legal_representation_flag
* claim history frequency

**Rules:**

* Must be deterministic under fixed seed.
* Score must follow right-skewed distribution.

**Usage:**
Fraud detection section of the Claims dashboard.



# **5.2 Retention & Churn Derivations**

Transformations that explain customer lifecycle, risk of churn, and engagement behaviors.



## **5.2.1 tenure_months**

**Definition:**

```
tenure_months = floor( months_between( customer_since, reference_date ) )
```

**Rules:**

* reference_date = churn_date if status = "Churned"
* reference_date = simulation_end_date otherwise

**Usage:**
Cohort analysis, churn segmentation, CLV modeling.



## **5.2.2 churn_flag**

**Definition:**

```
churn_flag = 1 if status = "Churned", else 0
```

**Usage:**
Churn KPIs, segmentation, funnel-like retention analytics.



## **5.2.3 days_since_last_payment**

**Definition:**

```
days_since_last_payment = reference_date - last_payment_date
```

**Rules:**

* Must be ≥ 0 for Active policies.
* May be null for Cancelled/Expired if no payment history.

**Usage:**
Churn driver analysis, lapse detection models.



## **5.2.4 churn_score**

**Definition:**
Synthetic churn propensity score (0–1).

**Inputs:**

* tenure_months
* total_claims
* days_since_last_payment
* engagement_score
* nps_score
* active_policies

**Rules:**

* Weighted linear or logistic-like synthetic function.
* Must be deterministic.
* Must produce a U-shaped or monotonic increasing risk shape depending on tenure.

**Usage:**
Churn risk segmentation, At-Risk customer lists.



## **5.2.5 cross_sell_ratio**

**Definition:**

```
cross_sell_ratio = active_policies / total_policies
```

**Rules:**

* Must handle division by zero.

**Usage:**
Customer value modeling, retention cohort analysis.



## **5.2.6 clv_estimated**

**Definition:**
Simplified customer lifetime value:

```
clv_estimated = avg_annual_premium × (expected_lifetime_years) × gross_margin_factor
```

**Rules:**

* expected_lifetime_years derived from inverse churn score or cohort behavior
* gross_margin_factor ≈ 0.60–0.80 (configurable)

**Usage:**
Customer valuation, strategic segments.



# **5.3 Underwriting Derivations**

These metrics support conversion funnels, efficiency KPIs, underwriter performance, and quote dynamics.



## **5.3.1 time_to_quote**

**Definition:**

```
time_to_quote = quote_date - request_date
```

**Rules:**

* Must be ≥ 0.

**Usage:**
Operational SLAs, UW efficiency.



## **5.3.2 time_to_bind**

**Definition:**

```
time_to_bind = bind_date - quote_date
```

**Rules:**

* bind_date exists only if quote_status="Bound".
* Must be ≥ 0.

**Usage:**
Binding funnel KPIs, process performance.



## **5.3.3 quote_to_bind_flag**

**Definition:**
Binary flag:

```
1 if quote_status = "Bound"
0 otherwise
```

**Usage:**
Hit ratio, conversion metrics, underwriter performance.



## **5.3.4 stp_indicator**

**Definition:**

```
stp_indicator = 1 if stp_flag = True  
                 and risk_score ≤ stp_threshold  
                 else 0
```

**Rules:**

* stp_threshold configurable (e.g., 30).

**Usage:**
Straight-Through Processing rate, efficiency tracking.



## **5.3.5 decline_reason_group**

**Definition:**
Maps granular decline_reason to standardized categories:

* Price-related
* Risk-related
* Documentation
* Customer decision
* Other

**Usage:**
Root-cause dashboards and funnel drop-off analysis.



## **5.3.6 underwriter_efficiency_score**

**Definition:**
Synthetic metric combining:

* quote volume
* hit ratio
* time_to_quote
* risk mix
* stp_indicator

**Rules:**

* Must be normalized 0–1.
* Deterministic and reinferable.

**Usage:**
Ranking underwriters, performance dashboards.



# **5.4 Pricing & Profitability Derivations**

Transformations enabling profitability KPIs, technical pricing metrics, and market comparisons.



## **5.4.1 earned_premium**

**Definition:**
Pro-rata allocation:

```
earned_premium = premium_written × (days_in_period / policy_term_days)
```

**Rules:**

* Must be computed monthly for accurate Loss Ratio.
* Must align with effective_date and expiration_date.



## **5.4.2 pure_premium**

**Definition:**

```
pure_premium = total_incurred / exposure_units
```

**Rules:**

* exposure_units based on policy duration and risk segmentation.

**Usage:**
Pricing adequacy and profitability.



## **5.4.3 rate_adequacy_index**

**Definition:**

```
rate_adequacy_index = our_average_premium / technically_required_premium
```

**Usage:**
Pricing Adequacy visualizations.



## **5.4.4 expense_ratio**

**Definition:**

```
expense_ratio = total_expenses / premium_written
```

**Usage:**
Combined Ratio calculations.



## **5.4.5 combined_ratio**

**Definition:**

```
combined_ratio = loss_ratio + expense_ratio
```

**Usage:**
Profitability dashboard core metric.



## **5.4.6 roe (return_on_equity)**

**Definition:**

```
roe = underwriting_profit / capital_allocated
```

where:

```
underwriting_profit = earned_premium - incurred_losses - expenses
```

**Usage:**
Product-level profitability evaluation.



## **5.4.7 loss_cost_trend**

**Definition:**
Percentage change between sequential development periods:

```
loss_cost_trend = (loss_cost_current / loss_cost_prior) - 1
```

**Usage:**
Loss cost trend graphs in Pricing dashboard.



# **5.5 Date, Time, and Exposure Derivations**

Cross-domain fields derived consistently for KPIs:



## **5.5.1 month_id**

**Definition:**

```
month_id = YYYYMM
```

**Usage:**
Cohorts, earned premium, loss development.



## **5.5.2 year_id**

Used for underwriting year (UWY) and accident year (AY).



## **5.5.3 exposure_units**

Simplified:

```
exposure_units = days_covered / 365
```

**Usage:**
Frequency, loss cost, pricing metrics.



## **5.5.4 policy_term_days**

```
policy_term_days = expiration_date - effective_date
```



## **5.5.5 age_band**

Standardized bands such as:

* 18–25
* 26–35
* 36–45
* 46–60
* 61+

Used in pricing and segmentation.



# **6. Quality Gates & HealthChecks**

This section defines all validation requirements the pipeline must satisfy before analytical outputs are released.
These controls ensure correctness, determinism, completeness, and semantic coherence across all domains: Claims, Retention, Underwriting, and Pricing.

HealthChecks are grouped into:

* Structural validations
* Referential integrity validations
* Temporal coherence validations
* Domain-specific analytical checks
* Cross-domain consistency rules
* Determinism checks

Each HealthCheck must run in Module C (Normalization & Enhancement) or Module D (Loader), as appropriate.



# **6.1 Purpose of Analytical Quality Controls**

The dashboards rely on derived KPIs that are sensitive to:

* Missing or corrupt policy–claim links
* Invalid date sequences
* Negative or inconsistent financial amounts
* Incorrect quote lifecycles
* Broken pricing segment relationships
* Incorrect loss development ordering
* Misaligned churn events

Quality Gates ensure:

* KPI accuracy (especially Loss Ratio, ROE, Rate Adequacy, Churn Rate)
* BI tool stability
* Full reproducibility of outputs

Passing all HealthChecks is mandatory before delivering the BI-ready datasets.



# **6.2 Validation Categories**



## **6.2.1 Structural Validations**

These validations confirm that tables, schemas, and field-level structures meet minimum expectations.

### Required Controls

* Tables exist with expected names.
* All mandatory columns exist in each table.
* Data types match the dictionary requirements (dates, decimals, integers).
* No critical field contains null values (e.g., IDs, dates, statuses).
* Numeric fields must not contain negative values unless explicitly allowed.
* Controlled vocabularies (status fields, reasons) must match allowed values.

### Failure Impact

Structural validation failures prevent the dataset from loading into BI tools.



## **6.2.2 Referential Integrity Validations**

Guarantees that relationships between tables remain unbroken.

### Required Controls

1. **Customer–Policy Integrity**

   * Every policy.customer_id must exist in customers.customer_id.

2. **Policy–Claim Integrity**

   * Every claim.policy_id must exist in policies.policy_id.

3. **Quote–Policy Integrity**

   * All bound quotes must link to one and only one policy.

4. **Underwriter & Agent Links**

   * underwriter_id and agent_id in quotes must match valid entries.

5. **Loss Development Links**

   * Every loss_development.policy_id must reference a valid policy.

6. **Pricing Segment Alignment**

   * pricing_segments attributes (state, product_line, risk_class) must be present in policies.

### Failure Impact

Breaks dashboard joins and invalidates KPIs such as frequency, hit ratio, or rating adequacy.



## **6.2.3 Temporal Coherence Validations**

Validates chronological correctness across the synthetic insurance lifecycle.

### Required Controls

1. **Policy Lifecycle**

   * effective_date ≤ expiration_date
   * cancellation_date ≥ effective_date when present

2. **Claims Lifecycle**

   * occurrence_date must be within policy effective period
   * occurrence_date ≤ report_date ≤ close_date (if closed)
   * payment_date must be ≥ report_date and ≤ close_date

3. **Underwriting Lifecycle**

   * request_date ≤ quote_date
   * quote_date ≤ bind_date (for bound quotes)
   * bind_date ≤ effective_date

4. **Churn Lifecycle**

   * churn_date must be ≥ customer_since
   * churn_date must be ≥ last_payment_date

5. **Pricing & Loss Development**

   * development_months must progress monotonically per policy
   * loss development values must not decrease across periods (paid and incurred must be non-decreasing)

### Failure Impact

Temporal violations produce impossible KPIs and misaligned time-series charts.



## **6.2.4 Domain-Specific Analytical Checks**

Each dashboard requires its own high-integrity quality checks.



### **Claims-Specific Checks**

1. total_incurred must equal paid_amount + reserved_amount.
2. paid_amount may not exceed total_incurred by more than a tolerance threshold.
3. No open claim may have a close_date.
4. No closed claim may have open status.
5. Fraud score must be between 0–100.
6. severity_band must be assigned for all claims with payments.



### **Retention-Specific Checks**

1. churn_flag must match status ("Churned").
2. tenure_months must be ≥ 0.
3. days_since_last_payment must be ≥ 0 for Active customers.
4. cross_sell_ratio must be within 0–1.
5. churn_score must be within 0–1.



### **Underwriting-Specific Checks**

1. A bound quote must always map to a policy.
2. time_to_quote and time_to_bind must be ≥ 0.
3. Funnel states must follow order (no regressions).
4. Declined quotes must have a decline_reason.
5. STP rules must be applied consistently.



### **Pricing-Specific Checks**

1. earned_premium must be between 0 and premium_written.
2. exposure_units must be > 0 for all active periods.
3. combined_ratio components must be non-negative.
4. Rate Adequacy Index must be > 0.
5. Development values must not decrease across months for the same policy.
6. market_average_premium must be > 0.



## **6.2.5 Cross-Domain Consistency Rules**

These checks ensure coherence across major business processes.

### Required Controls

1. **Quotes → Policies → Claims Chain**

   * If a policy originated from a quote, product_line and coverage must match.
   * Claims must map to policies whose product_line matches pricing segments.

2. **Customer → Policy → Claims Chain**

   * Customers marked as Churned must not have Active policies.
   * Policies of churned customers may not have claims after churn_date.

3. **Geographic Consistency**

   * Claim state and city must match policy geography.
   * Pricing segments must match policy geography.

4. **Risk Profile & Score Alignment**

   * Risk scores must be within expected bounds for each product_line.
   * Underwriting risk_class must align with risk_score thresholds.

### Failure Impact

Cross-domain inconsistencies corrupt KPIs and distort dashboard visualizations.



## **6.2.6 Determinism & Reproducibility Validations**

Ensures that outputs can be regenerated perfectly when using the same seed.

### Required Controls

1. If random_seed is provided, all stochastic processes must use it.
2. Any run with the same configuration must produce identical:

   * customers
   * policies
   * claims
   * quotes
   * loss development snapshots
   * synthetic scores (fraud, churn, risk)
3. Hash-of-output-tables must match between runs.

### Failure Impact

Non-deterministic datasets invalidate testing and version control.



# **7. BI Output & Consumption Contract**

This section defines the standards, formats, naming conventions, structural guarantees, and stability requirements for all analytical datasets produced by the pipeline and consumed by BI dashboards.
These rules ensure that dashboard implementations remain stable, predictable, and insulated from internal pipeline changes.



# **7.1 File Formats & Storage Standards**



## **7.1.1 Accepted Output Formats**

The pipeline must generate BI-ready datasets in:

* **CSV** (UTF-8, comma-separated, quoted strings)
* **Parquet** (preferred for analytical engines)
* **Supabase tables** (if configured)

Both CSV and Parquet outputs must contain identical schemas and field values.



## **7.1.2 Dataset Export Requirements**

1. Final datasets must be exported to a structured folder hierarchy such as:

```
/output/
   /policies/
   /claims/
   /claims_payments/
   /customers/
   /quotes/
   /pricing/
   /underwriting/
   /retention/
   /loss_development/
   /expenses/
   /market/
   /retention_campaigns/
   version_metadata.json
```

2. Each subfolder may contain **partitioned files** based on logical criteria (typically year or month).

3. All exports must include a metadata file describing:

* Row count
* Column list and data types
* Schema version
* Generation timestamp
* Random seed (if applicable)



## **7.1.3 Partitioning Rules**

To support time-based filtering:

* **claims**, **policies**, **quotes**, **loss_development**, and **expenses** must be partitioned by **year**.
* Optionally, large tables may be partitioned by **month** when row count exceeds 1 million.

Partitioning keys must be formatted:

```
year=YYYY/
year=YYYY/month=MM/
```



# **7.2 Dataset Naming Conventions**



## **7.2.1 File Names**

All exported dataset names must follow **lowercase snake_case**, e.g.:

* `customers.csv` / `customers.parquet`
* `policies_2023.parquet`
* `claims_2022_2023.parquet`
* `pricing_segments.csv`

Versioned outputs may append:

```
_v1
_v2
_run001
```

Example:

```
claims_master_v1_run003.parquet
```



## **7.2.2 Table Names in Supabase**

Tables must use consistent lowercase snake_case names:

* `customers`
* `policies`
* `claims_master`
* `claims_payments`
* `quotes`
* `underwriters`
* `agents`
* `pricing_segments`
* `loss_development`

No prefixes or suffixes (e.g., “tbl_”) are permitted.



# **7.3 Mandatory Columns by Output Table**

Every dataset must include the full set of fields defined in the **Data Dictionary (Section 3)**.

### Required Guarantees:

1. **No column may be omitted**, even if certain rows contain null values for optional fields.
2. **Column order must remain stable across versions** (alphabetical ordering is preferred).
3. **Data types must match dictionary definitions** exactly.

This ensures dashboards can ingest data without needing schema detection logic.



# **7.4 Grain & Partitioning Requirements**



## **7.4.1 Grain Requirements per Table**

Each table must preserve the following analytical grain:

| Table              | Required Grain                                   |
|  |  |
| customers          | One row per customer_id                          |
| policies           | One row per policy_id                            |
| claims_master      | One row per claim_id                             |
| claims_payments    | One row per payment_id                           |
| quotes             | One row per quote_id                             |
| underwriters       | One row per underwriter_id                       |
| agents             | One row per agent_id                             |
| loss_development   | One row per policy_id × development_month        |
| expenses           | One row per expense_id                           |
| pricing_segments   | One row per unique segment_id                    |
| capital_allocation | One row per product_line × underwriting_year     |
| market_data        | One row per competitor_id × product_line × state |

Violations of grain (duplication, merging) are not permitted.



## **7.4.2 BI Aggregation Safety**

Datasets must be structured so that BI tools (Power BI, Looker) can:

* Aggregate metrics without introducing duplicates
* Perform row-level filtering without collapsing grain
* Join tables along foreign keys unambiguously

Therefore:

* No multi-grain tables are allowed
* No nested arrays, JSON-encoded fields, or non-tabular structures
* All fact tables must reference dimensional attributes via FK fields



## **7.4.3 Logical Partitioning for BI Performance**

Large datasets (e.g., claims, quotes) must be partitioned by:

* **year of occurrence** (claims_master)
* **year of quote_date** (quotes)
* **underwriting_year** (policies)
* **accident_year** (loss_development)
* **period** (expenses, YYYY-MM)

Partitioning ensures faster refresh cycles and lower memory overhead in BI tools.



# **7.5 Dashboard-Specific Data Guarantees**

The pipeline must ensure that each dashboard receives complete, consistent, and KPI-ready datasets.



## **7.5.1 Claims & Loss Analysis Guarantees**

1. **total_incurred**, **fraud_score**, **severity_band**, and **days_to_settlement** must be precomputed.
2. All claims must contain policy-level attributes required for segmentation (product_line, state, risk_score).
3. Claims with missing lifecycle dates must be filtered or corrected.
4. Claims must map to valid policies active at the occurrence_date.
5. All derived financial metrics must match definitions exactly.



## **7.5.2 Retention & Churn Guarantees**

1. **tenure_months**, **churn_flag**, **churn_score**, and **days_since_last_payment** must be fully populated.
2. No Active customer may contain churn_date.
3. Cohort month must be included as an attribute or derivable from customer_since.
4. customer_policies_summary must be computed and exported.



## **7.5.3 Underwriting Operations Guarantees**

1. **time_to_quote**, **time_to_bind**, and conversion indicators must be precomputed.
2. Bound quotes must link directly to policies.
3. Decline reasons must follow standardized categories.
4. STP logic must be reflected in stp_flag and stp_indicator.



## **7.5.4 Pricing & Profitability Guarantees**

1. **earned_premium**, exposure units, and policy terms must be precomputed.
2. Development snapshots must follow increasing development_month ordering.
3. Rate Adequacy Index fields must be complete for all pricing segments.
4. Expense and capital allocation tables must align with product lines found in policies.
5. No missing or zero market_average_premium values unless explicitly configured.

