-- ============================================================
-- INSURANCE ANALYTICS — BI CONTRACT V1 (FROZEN)
-- PostgreSQL / Supabase
-- ============================================================

-- Ensure the schema exists; default schema is 'public'
CREATE SCHEMA IF NOT EXISTS public;

-- Grant access to the schema for the default roles
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

-- ============================================================
-- DIMENSIONS — Core tables for dimensional modeling
-- ============================================================

-- Time dimension table (dim_time)
-- Contains temporal details for all fact records
CREATE TABLE IF NOT EXISTS public.dim_time (
    date_key     INT PRIMARY KEY,  -- Date key (YYYYMMDD) for easy reference
    full_date    DATE,             -- Full date in standard format
    year         INT,              -- Year (e.g., 2025)
    month        INT,              -- Month (1 to 12)
    month_name   TEXT,             -- Month name (e.g., January)
    quarter      INT,              -- Quarter (1 to 4)
    year_month   TEXT,             -- Concatenated year-month (e.g., "2025-01")
    day_of_week  INT,              -- Day of the week (1 to 7)
    is_weekend   BOOLEAN           -- Flag indicating if the day is a weekend
);

-- State dimension table (dim_state)
-- Contains state-related information
CREATE TABLE IF NOT EXISTS public.dim_state (
    state_code   TEXT PRIMARY KEY, -- State code (e.g., 'NY', 'CA')
    region_code  TEXT,             -- Region code (e.g., 'NE', 'MW')
    market_tier  TEXT              -- Market tier classification (e.g., 'Tier 1')
);

-- Clients dimension table (dim_clients)
-- Contains information about clients
CREATE TABLE IF NOT EXISTS public.dim_clients (
    client_id            TEXT PRIMARY KEY,        -- Unique client ID
    registration_year    INT,                      -- Year the client registered
    age                  INT,                      -- Age of the client
    gender               TEXT,                     -- Gender of the client
    customer_segment     TEXT,                     -- Customer segment (e.g., 'Individual', 'Corporate')
    state_code           TEXT REFERENCES public.dim_state(state_code), -- Foreign key to dim_state
    region_code          TEXT,                      -- Region code (linked with state)
    market_tier          TEXT,                      -- Market tier (linked with state)
    max_policies_allowed INT                        -- Maximum number of policies allowed for this client
);

-- Products dimension table (dim_products)
-- Contains information about product offerings
CREATE TABLE IF NOT EXISTS public.dim_products (
    product_key      TEXT PRIMARY KEY, -- Unique product key
    line_of_business TEXT,             -- Line of business (e.g., 'Life', 'Health', 'Auto')
    plan_name        TEXT              -- Plan name (e.g., 'Basic', 'Standard', 'Premium')
);

-- Policies dimension table (dim_policies)
-- Contains policy-level information
CREATE TABLE IF NOT EXISTS public.dim_policies (
    policy_id     TEXT PRIMARY KEY,          -- Unique policy ID
    policy_number TEXT,                      -- Policy number
    client_id     TEXT REFERENCES public.dim_clients(client_id), -- Foreign key to clients
    state_code    TEXT REFERENCES public.dim_state(state_code), -- Foreign key to state
    region_code   TEXT,                      -- Region code (linked with state)
    is_renewal    BOOLEAN                   -- Flag to indicate if the policy is a renewal
);

-- ============================================================
-- FACT TABLES — Core transactional data for BI
-- ============================================================

-- Fact table for policies (fact_policies)
CREATE TABLE IF NOT EXISTS public.fact_policies (
    policy_id           TEXT PRIMARY KEY REFERENCES public.dim_policies(policy_id), -- Foreign key to dim_policies
    product_key         TEXT REFERENCES public.dim_products(product_key),         -- Foreign key to dim_products
    state_code          TEXT REFERENCES public.dim_state(state_code),             -- Foreign key to dim_state
    region_code         TEXT,                                                    -- Region code (linked with state)
    effective_date_key  INT REFERENCES public.dim_time(date_key),                -- Foreign key to dim_time (effective date)
    expiration_date_key INT,                                                     -- Expiration date (nullable, no foreign key constraint)
    policy_year         INT,                                                     -- Policy year
    policy_month        INT,                                                     -- Policy month
    status              TEXT,                                                    -- Policy status (e.g., 'Active', 'Expired')
    risk_score          NUMERIC,                                                 -- Risk score (numerical value)
    monthly_premium     NUMERIC,                                                 -- Monthly premium amount
    annual_premium      NUMERIC                                                  -- Annual premium amount
);

-- Fact table for claims (fact_claims)
CREATE TABLE IF NOT EXISTS public.fact_claims (
    claim_id               TEXT PRIMARY KEY,                               -- Unique claim ID
    policy_id              TEXT REFERENCES public.dim_policies(policy_id), -- Foreign key to dim_policies
    product_key            TEXT REFERENCES public.dim_products(product_key), -- Foreign key to dim_products
    line_of_business       TEXT,                                            -- Line of business (e.g., 'Life')
    state_code             TEXT REFERENCES public.dim_state(state_code),  -- Foreign key to dim_state
    region_code            TEXT,                                            -- Region code
    claim_type             TEXT,                                            -- Type of claim (e.g., 'Death', 'Theft')
    claim_status           TEXT,                                            -- Claim status (e.g., 'Paid', 'Pending')
    fraud_flag             BOOLEAN,                                         -- Fraud detection flag
    incident_date_key      INT REFERENCES public.dim_time(date_key),       -- Foreign key to dim_time (incident date)
    report_date_key        INT REFERENCES public.dim_time(date_key),       -- Foreign key to dim_time (report date)
    settlement_date_key    INT,                                             -- Settlement date (nullable)
    days_to_settle         INT,                                             -- Number of days to settle the claim
    claim_amount_requested NUMERIC,                                         -- Requested claim amount
    claim_amount_approved  NUMERIC,                                         -- Approved claim amount
    claim_amount_paid      NUMERIC                                          -- Paid claim amount
);

-- Fact table for expenses (fact_expenses)
CREATE TABLE IF NOT EXISTS public.fact_expenses (
    expense_id       TEXT PRIMARY KEY, -- Unique expense ID
    expense_category TEXT,             -- Category of the expense (e.g., 'Operating')
    state_code       TEXT REFERENCES public.dim_state(state_code), -- Foreign key to dim_state
    region_code      TEXT,             -- Region code
    date_key         INT REFERENCES public.dim_time(date_key),    -- Foreign key to dim_time (month/year)
    expense_amount   NUMERIC                                                -- Amount of the expense
);

-- Fact table for taxes (fact_taxes)
CREATE TABLE IF NOT EXISTS public.fact_taxes (
    tax_id      TEXT PRIMARY KEY,                               -- Unique tax ID
    tax_type    TEXT,                                            -- Type of tax (e.g., 'State Tax')
    state_code  TEXT REFERENCES public.dim_state(state_code),    -- Foreign key to dim_state
    date_key    INT REFERENCES public.dim_time(date_key),        -- Foreign key to dim_time (tax date)
    tax_base    NUMERIC,                                         -- Tax base value
    tax_rate    NUMERIC,                                         -- Tax rate applied
    tax_amount  NUMERIC,                                          -- Total tax amount
	policy_id	TEXT
);

-- ============================================================
-- INDEXES — For faster querying and BI performance
-- ============================================================

-- Create indexes for important fact tables
CREATE INDEX IF NOT EXISTS idx_fp_eff_exp
ON public.fact_policies (effective_date_key, expiration_date_key);

CREATE INDEX IF NOT EXISTS idx_fc_incident
ON public.fact_claims (incident_date_key);

CREATE INDEX IF NOT EXISTS idx_fc_policy
ON public.fact_claims (policy_id);

-- ============================================================
-- ROW LEVEL SECURITY (RLS) — Enable RLS for secure access
-- ============================================================

-- Enable Row Level Security on all tables to enforce access policies
ALTER TABLE public.dim_time       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_state      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_clients    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_products   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_policies   ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.fact_policies  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fact_claims    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fact_expenses  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fact_taxes     ENABLE ROW LEVEL SECURITY;

-- VIEWS


-- ============================================================
-- DASHBOARD 1 — EXECUTIVE PORTFOLIO (MONTHLY SNAPSHOT)
-- ONE VIEW = ONE DASHBOARD
-- ============================================================

CREATE OR REPLACE VIEW public.vw_dash_exec_portfolio AS
SELECT
    -- Canonical date for BI tools
    TO_DATE(t.year_month || '-01', 'YYYY-MM-DD') AS month_date,

    t.year,
    t.month,
    t.year_month,

    -- Portfolio size
    COUNT(DISTINCT p.policy_id) AS active_policies,

    -- Premium exposure
    SUM(p.annual_premium)  AS total_annual_premium,
    SUM(p.monthly_premium) AS total_monthly_premium,

    -- Optional breakdown helpers
    p.state_code,
    p.region_code,
    pr.line_of_business

FROM public.fact_policies p
JOIN public.dim_time t
  ON t.date_key BETWEEN p.effective_date_key
                    AND COALESCE(p.expiration_date_key, p.effective_date_key)
LEFT JOIN public.dim_products pr
  ON pr.product_key = p.product_key

GROUP BY
    month_date,
    t.year,
    t.month,
    t.year_month,
    p.state_code,
    p.region_code,
    pr.line_of_business;


-- ============================================================
-- DASHBOARD 2 — CLAIMS & LOSS (MONTHLY PERFORMANCE)
-- ONE VIEW = ONE DASHBOARD
-- ============================================================

CREATE OR REPLACE VIEW public.vw_dash_claims_loss AS
SELECT
    -- Canonical monthly date
    TO_DATE(t.year_month || '-01', 'YYYY-MM-DD') AS month_date,

    t.year,
    t.month,
    t.year_month,

    -- Dimensions
    p.product_key,
    pr.line_of_business,
    p.state_code,
    p.region_code,

    -- Exposure
    COUNT(DISTINCT p.policy_id) AS exposed_policies,

    -- Claims volume
    COUNT(DISTINCT c.claim_id) AS claim_count,

    -- Financials
    SUM(c.claim_amount_paid) AS total_losses,
    SUM(p.annual_premium)    AS total_premium,

    -- Frequency & severity
    CASE
        WHEN COUNT(DISTINCT p.policy_id) > 0
        THEN COUNT(DISTINCT c.claim_id)::NUMERIC
             / COUNT(DISTINCT p.policy_id)
        ELSE NULL
    END AS claim_frequency,

    CASE
        WHEN COUNT(DISTINCT c.claim_id) > 0
        THEN SUM(c.claim_amount_paid)
             / COUNT(DISTINCT c.claim_id)
        ELSE NULL
    END AS claim_severity,

    -- Loss Ratio
    CASE
        WHEN SUM(p.annual_premium) > 0
        THEN SUM(c.claim_amount_paid)
             / SUM(p.annual_premium)
        ELSE NULL
    END AS loss_ratio

FROM public.fact_claims c
JOIN public.fact_policies p
  ON p.policy_id = c.policy_id
JOIN public.dim_time t
  ON t.date_key = c.incident_date_key
LEFT JOIN public.dim_products pr
  ON pr.product_key = p.product_key

GROUP BY
    month_date,
    t.year,
    t.month,
    t.year_month,
    p.product_key,
    pr.line_of_business,
    p.state_code,
    p.region_code;


-- ============================================================
-- DASHBOARD 3 — OPERATIONS DAILY MONITORING
-- ONE VIEW = ONE DASHBOARD
-- GRAIN: ONE ROW PER DAY / SEGMENT
-- ============================================================

CREATE OR REPLACE VIEW public.vw_dash_operations_daily AS
SELECT
    -- Canonical daily date
    t.full_date AS day_date,

    t.year,
    t.month,
    t.year_month,

    -- Dimensions
    p.state_code,
    p.region_code,
    pr.line_of_business,

    -- Portfolio in force (as of day)
    COUNT(DISTINCT p.policy_id) AS active_policies,

    -- Daily exposure
    SUM(p.monthly_premium) AS daily_premium_exposure,

    -- New business (policy starts)
    COUNT(DISTINCT CASE
        WHEN t.date_key = p.effective_date_key
        THEN p.policy_id
    END) AS policies_started,

    -- Policy terminations (expirations)
    COUNT(DISTINCT CASE
        WHEN t.date_key = p.expiration_date_key
        THEN p.policy_id
    END) AS policies_ended

FROM public.dim_time t
JOIN public.fact_policies p
  ON t.date_key BETWEEN p.effective_date_key
                    AND COALESCE(p.expiration_date_key, t.date_key)
LEFT JOIN public.dim_products pr
  ON pr.product_key = p.product_key

GROUP BY
    t.full_date,
    t.year,
    t.month,
    t.year_month,
    p.state_code,
    p.region_code,
    pr.line_of_business;


-- ============================================================
-- DASHBOARD 4 — RISK & UNDERWRITING (DAILY MONITORING)
-- ONE VIEW = ONE DASHBOARD
-- ============================================================

CREATE OR REPLACE VIEW public.vw_dash_risk_daily AS
SELECT
    -- Canonical daily date
    t.full_date AS day_date,

    t.year,
    t.month,
    t.year_month,

    -- Dimensions
    dp.state_code,
    dp.region_code,
    pr.line_of_business,

    -- Portfolio base
    COUNT(DISTINCT fp.policy_id) AS active_policies,

    -- Risk metrics
    AVG(fp.risk_score) AS avg_risk_score,

    COUNT(DISTINCT CASE
        WHEN fp.risk_score >= 0.8 THEN fp.policy_id
    END) AS high_risk_policies,

    -- Underwriting mix
    COUNT(DISTINCT CASE
        WHEN dp.is_renewal = false THEN fp.policy_id
    END) AS new_business_policies,

    COUNT(DISTINCT CASE
        WHEN dp.is_renewal = true THEN fp.policy_id
    END) AS renewal_policies,

    -- New business risk
    AVG(CASE
        WHEN dp.is_renewal = false THEN fp.risk_score
    END) AS avg_new_business_risk

FROM public.dim_time t
JOIN public.fact_policies fp
  ON t.date_key BETWEEN fp.effective_date_key
                    AND COALESCE(fp.expiration_date_key, t.date_key)
JOIN public.dim_policies dp
  ON dp.policy_id = fp.policy_id
LEFT JOIN public.dim_products pr
  ON pr.product_key = fp.product_key

GROUP BY
    t.full_date,
    t.year,
    t.month,
    t.year_month,
    dp.state_code,
    dp.region_code,
    pr.line_of_business;


-- GRANTS

-- Read-only access for BI users
GRANT SELECT ON
    public.dim_time,
    public.dim_state,
    public.dim_clients,
    public.dim_products,
    public.dim_policies,
    public.fact_policies,
    public.fact_claims,
    public.fact_expenses,
    public.fact_taxes
TO authenticated;

-- Full access for service role (ETL, maintenance)
GRANT SELECT, INSERT, UPDATE, DELETE ON
    public.dim_time,
    public.dim_state,
    public.dim_clients,
    public.dim_products,
    public.dim_policies,
    public.fact_policies,
    public.fact_claims,
    public.fact_expenses,
    public.fact_taxes
TO service_role;


-- BI read access (Looker / dashboards)
GRANT SELECT ON
    public.vw_dash_exec_portfolio,
    public.vw_dash_claims_loss,
    public.vw_dash_operations_daily,
    public.vw_dash_risk_daily
TO authenticated;

-- Backend & validation access
GRANT SELECT ON
    public.vw_dash_exec_portfolio,
    public.vw_dash_claims_loss,
    public.vw_dash_operations_daily,
    public.vw_dash_risk_daily
TO service_role;


-- Notify PostgREST to reload schema metadata
NOTIFY pgrst, 'reload schema';
