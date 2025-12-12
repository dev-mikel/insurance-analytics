-- ============================================================
-- SCHEMA: CREATE TABLES
-- ============================================================

create table if not exists public.dim_regions (
    region text primary key,
    num_states int
);

create table if not exists public.dim_states (
    state text primary key,
    region text references public.dim_regions(region)
);

create table if not exists public.dim_customers (
    customer_id text primary key,
    age int,
    income numeric,
    bmi numeric,
    age_group text,
    income_bucket text,
    bmi_bucket text,
    region text references public.dim_regions(region),
    state text references public.dim_states(state)
);

create table if not exists public.fact_policies (
    policy_id text primary key,
    customer_id text references public.dim_customers(customer_id),
    product_line text,
    coverage_amount numeric,
    deductible numeric,
    premium_annual numeric,
    payment_frequency text,
    start_date date,
    end_date date,
    region text,
    state text,
    tenure_years integer
);

create table if not exists public.fact_claims (
    claim_id text primary key,
    policy_id text references public.fact_policies(policy_id),
    customer_id text references public.dim_customers(customer_id),
    product_line text,
    coverage_amount numeric,
    claim_amount numeric,
    deductible numeric,
    net_paid numeric,
    occurrence_date date,
    report_date date,
    settlement_date date,
    region text,
    state text,
    fraud_score numeric,
    legal_rep_flag boolean
);

create table if not exists public.fact_quotes (
    quote_id text primary key,
    customer_id text references public.dim_customers(customer_id),
    product_line text,
    policy_id_target text references public.fact_policies(policy_id),
    request_date date,
    quote_date date,
    quote_status text,
    region text,
    state text
);

create table if not exists public.fact_uw_decisions (
    quote_id text primary key references public.fact_quotes(quote_id),
    stp_flag boolean,
    accepted_flag boolean,
    bound_flag boolean,
    expired_flag boolean,
    decline_reason text
);

create table if not exists public.fact_retention (
    id bigint generated always as identity primary key,
    customer_id text references public.dim_customers(customer_id),
    status text,
    churn_flag boolean,
    churn_reason text,
    churn_date date,
    campaign_executed boolean,
    campaign_type text,
    responded_flag boolean,
    retained_after_campaign boolean,
    engagement_score numeric,
    nps_score numeric
);

create table if not exists public.fact_pricing_segments (
    segment_id text primary key,
    product_line text,
    state text,
    technically_required_premium numeric,
    our_average_premium numeric,
    market_average_premium numeric,
    exposure_count numeric
);

create table if not exists public.fact_loss_development (
    id bigint generated always as identity primary key,
    claim_id text references public.fact_claims(claim_id),
    product_line text,
    state text,
    development_month int,
    incurred_losses numeric,
    paid_losses numeric
);

-- ============================================================
-- GRANTS FOR TABLES (anon, authenticated)
-- ============================================================

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

GRANT SELECT ON public.dim_regions TO anon, authenticated;
GRANT SELECT ON public.dim_states TO anon, authenticated;
GRANT SELECT ON public.dim_customers TO authenticated;

GRANT SELECT ON public.fact_policies TO authenticated;
GRANT SELECT ON public.fact_claims TO authenticated;
GRANT SELECT ON public.fact_quotes TO authenticated;
GRANT SELECT ON public.fact_uw_decisions TO authenticated;
GRANT SELECT ON public.fact_retention TO authenticated;
GRANT SELECT ON public.fact_pricing_segments TO authenticated;
GRANT SELECT ON public.fact_loss_development TO authenticated;

-- ============================================================
-- GRANTS FOR service_role (FULL ETL RIGHTS)
-- ============================================================

-- CRUD
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO service_role;

-- READ ACCESS (critical for REST)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO service_role;

-- SEQUENCES (needed for identity columns)
GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA public TO service_role;


-- ============================================================
-- RLS ENABLE
-- ============================================================

alter table public.dim_regions enable row level security;
alter table public.dim_states enable row level security;
alter table public.dim_customers enable row level security;
alter table public.fact_policies enable row level security;
alter table public.fact_claims enable row level security;
alter table public.fact_quotes enable row level security;
alter table public.fact_uw_decisions enable row level security;
alter table public.fact_retention enable row level security;
alter table public.fact_pricing_segments enable row level security;
alter table public.fact_loss_development enable row level security;

-- ============================================================
-- POLICIES
-- ============================================================

create policy "anon_select_dim_regions" on public.dim_regions for select to anon using (true);
create policy "anon_select_dim_states" on public.dim_states for select to anon using (true);

create policy "auth_select_dim_regions" on public.dim_regions for select to authenticated using (true);
create policy "auth_select_dim_states" on public.dim_states for select to authenticated using (true);
create policy "auth_select_dim_customers" on public.dim_customers for select to authenticated using (true);

create policy "auth_select_fact_policies" on public.fact_policies for select to authenticated using (true);
create policy "auth_select_fact_claims" on public.fact_claims for select to authenticated using (true);
create policy "auth_select_fact_quotes" on public.fact_quotes for select to authenticated using (true);
create policy "auth_select_fact_uw" on public.fact_uw_decisions for select to authenticated using (true);
create policy "auth_select_fact_retention" on public.fact_retention for select to authenticated using (true);
create policy "auth_select_fact_pricing" on public.fact_pricing_segments for select to authenticated using (true);
create policy "auth_select_fact_lossdev" on public.fact_loss_development for select to authenticated using (true);

-- deny writes for anon + authenticated
create policy "deny_write_dim_customers"  on public.dim_customers for all to anon, authenticated using (false);
create policy "deny_write_fact_policies"  on public.fact_policies for all to anon, authenticated using (false);
create policy "deny_write_fact_claims"    on public.fact_claims for all to anon, authenticated using (false);
create policy "deny_write_fact_quotes"    on public.fact_quotes for all to anon, authenticated using (false);
create policy "deny_write_fact_uw"        on public.fact_uw_decisions for all to anon, authenticated using (false);
create policy "deny_write_fact_retention" on public.fact_retention for all to anon, authenticated using (false);
create policy "deny_write_fact_pricing"   on public.fact_pricing_segments for all to anon, authenticated using (false);
create policy "deny_write_fact_lossdev"   on public.fact_loss_development for all to anon, authenticated using (false);

-- ============================================================
-- INDEXES
-- ============================================================

create index if not exists idx_dim_customers_region on public.dim_customers(region);
create index if not exists idx_dim_customers_state on public.dim_customers(state);
create index if not exists idx_fact_policies_customer on public.fact_policies(customer_id);
create index if not exists idx_fact_claims_policy on public.fact_claims(policy_id);
create index if not exists idx_fact_claims_customer on public.fact_claims(customer_id);
create index if not exists idx_fact_quotes_customer on public.fact_quotes(customer_id);
create index if not exists idx_fact_uw_quote on public.fact_uw_decisions(quote_id);
create index if not exists idx_fact_pricing_state on public.fact_pricing_segments(state);
create index if not exists idx_fact_lossdev_claim on public.fact_loss_development(claim_id);


-- ============================================================
-- REFRESH REST CACHE
-- ============================================================

NOTIFY pgrst, 'reload schema';

-- ============================================================
-- VIEWS 
-- ============================================================

-- ------------------------------------------------------------
-- LOSS & CLAIMS ANALYSIS
-- Grain: policy_id × claim_id
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_loss_ratio AS
SELECT
    p.policy_id,
    p.customer_id,
    p.product_line,
    p.region,
    p.state,
    p.start_date,
    p.end_date,

    c.claim_id,
    c.occurrence_date,
    c.report_date,
    c.settlement_date,

    p.premium_annual                AS premium_earned,
    c.claim_amount                  AS incurred_loss,
    c.net_paid,

    CASE
        WHEN p.premium_annual > 0
        THEN c.claim_amount / p.premium_annual
        ELSE NULL
    END                             AS loss_ratio

FROM public.fact_policies p
LEFT JOIN public.fact_claims c
       ON c.policy_id = p.policy_id;


-- ------------------------------------------------------------
-- UNDERWRITING FUNNEL & STP
-- Grain: quote_id
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_underwriting_funnel AS
SELECT
    q.quote_id,
    q.customer_id,
    q.policy_id_target              AS policy_id,
    q.product_line,
    q.region,
    q.state,
    q.request_date,
    q.quote_date,
    q.quote_status,

    u.stp_flag,
    u.accepted_flag,
    u.bound_flag,
    u.expired_flag,

    CASE
        WHEN q.quote_status IN ('QUOTED','ACCEPTED','BOUND')
        THEN TRUE ELSE FALSE
    END                             AS quoted_flag

FROM public.fact_quotes q
LEFT JOIN public.fact_uw_decisions u
       ON u.quote_id = q.quote_id;

-- ------------------------------------------------------------
-- RETENTION / CHURN
-- Grain: customer_id
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_churn AS
SELECT
    customer_id,
    status,
    churn_flag,
    churn_reason,
    churn_date,

    campaign_executed,
    campaign_type,
    responded_flag,
    retained_after_campaign,

    engagement_score,
    nps_score

FROM public.fact_retention;

-- ------------------------------------------------------------
-- PRICING ADEQUACY
-- Grain: segment_id
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_pricing_adequacy AS
SELECT
    segment_id,
    product_line,
    state,
    exposure_count,

    technically_required_premium,
    our_average_premium,
    market_average_premium,

    CASE
        WHEN technically_required_premium > 0
        THEN our_average_premium / technically_required_premium
        ELSE NULL
    END                             AS pricing_adequacy_ratio

FROM public.fact_pricing_segments;

-- ------------------------------------------------------------
-- POLICY FREQUENCY
-- Grain: policy_id
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_policy_frequency AS
SELECT
    p.policy_id,
    p.product_line,
    p.region,
    p.state,

    COUNT(c.claim_id)               AS claim_count,
    CASE
        WHEN COUNT(c.claim_id) > 0
        THEN 1 ELSE 0
    END                             AS has_claim_flag

FROM public.fact_policies p
LEFT JOIN public.fact_claims c
       ON c.policy_id = p.policy_id
GROUP BY
    p.policy_id,
    p.product_line,
    p.region,
    p.state;


-- ------------------------------------------------------------
-- EXECUTIVE PORTFOLIO OVERVIEW
-- Grain: product_line × state
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_executive_portfolio AS
SELECT
    p.product_line,
    p.state,

    COUNT(DISTINCT p.policy_id)     AS policy_count,
    COUNT(DISTINCT p.customer_id)   AS customer_count,

    SUM(p.premium_annual)           AS total_premium,
    SUM(c.claim_amount)             AS total_incurred_loss,

    CASE
        WHEN SUM(p.premium_annual) > 0
        THEN SUM(c.claim_amount) / SUM(p.premium_annual)
        ELSE NULL
    END                             AS loss_ratio

FROM public.fact_policies p
LEFT JOIN public.fact_claims c
       ON c.policy_id = p.policy_id
GROUP BY
    p.product_line,
    p.state;

-- ============================================================
-- 2. VIEWS GRANTS
-- ============================================================

-- Authenticated users (BI / Looker Studio)
GRANT SELECT ON vw_loss_ratio              TO authenticated;
GRANT SELECT ON vw_underwriting_funnel     TO authenticated;
GRANT SELECT ON vw_churn                   TO authenticated;
GRANT SELECT ON vw_pricing_adequacy        TO authenticated;
GRANT SELECT ON vw_policy_frequency        TO authenticated;
GRANT SELECT ON vw_executive_portfolio     TO authenticated;

-- Service role (healthchecks, loaders, admin)
GRANT SELECT ON vw_loss_ratio              TO service_role;
GRANT SELECT ON vw_underwriting_funnel     TO service_role;
GRANT SELECT ON vw_churn                   TO service_role;
GRANT SELECT ON vw_pricing_adequacy        TO service_role;
GRANT SELECT ON vw_policy_frequency        TO service_role;
GRANT SELECT ON vw_executive_portfolio     TO service_role;

-- No GRANT to anon (implicit deny)

-- ============================================================
-- REFRESH REST CACHE
-- ============================================================

NOTIFY pgrst, 'reload schema';

