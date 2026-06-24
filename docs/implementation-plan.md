# Implementation Plan — Insurance Analytics Pipeline

End-to-end guide to run the platform locally: generate synthetic data, validate it, deploy the schema to Supabase (PostgreSQL), load it, and connect Looker Studio.

Every command below is verifiable in the repository. Placeholders marked `{{TODO}}` are values only you can supply (credentials, your tested versions).

---

## 1. What it is

A modular pipeline of ordered Python scripts. Scripts numbered `01`–`10` run in sequence; the even "module" scripts do the work, and the health-check scripts validate each boundary:

| Step | Script | Role |
| ---- | ------ | ---- |
| 01 | `scripts/01_module_A_dataset_setup.py` | **Module A** — write `output/config.json` |
| 02 | `scripts/02_module_b_dataset_generator.py` | **Module B** — generate `output/raw/*.csv` |
| 03 | `scripts/03_healthcheck_dataset.py` | Validate raw datasets |
| 04 | `scripts/04_module_C_normalizer.py` | **Module C** — build star schema `output/normalized/*.csv` |
| 05 | `scripts/05_healthcheck_normalizer.py` | Validate normalized star schema + referential integrity |
| 06 | `scripts/06_healthcheck_connection.py` | Check env vars + PostgreSQL connection |
| 07 | `scripts/07_module_D_schema.py` | **Module D** — deploy `schema.sql` to Supabase |
| 08 | `scripts/08_healthcheck_schema.py` | Verify tables, views, RLS / REST access |
| 09 | `scripts/09_module_E_loader.py` | **Module E** — `COPY` normalized CSVs into PostgreSQL |
| 10 | `scripts/10_healthcheck_loader.py` | Post-load row counts, FK integrity, BI views |

Steps **01–05** run entirely locally (no database). Steps **06–10** require a Supabase/PostgreSQL connection.

---

## 2. Prerequisites

- **Python 3** — the repo does not pin a version. {{TODO: confirm the exact Python version you tested with}}
- **pip** (and ideally a virtual environment).
- **A Supabase project** (or any PostgreSQL database reachable via a connection string) — required for steps 06–10 only.
- **Google Looker Studio** account — to connect the BI views (optional, for the dashboard layer).

Python libraries used (detected from imports — no `requirements.txt` is present in the repo):

- `pandas`
- `numpy`
- `psycopg2` (install `psycopg2-binary` for a build-free install)
- `requests`

---

## 3. Installation

```bash
git clone <this-repo-url>
cd insurance-analytics

python3 -m venv .venv
source .venv/bin/activate

pip install pandas numpy psycopg2-binary requests
```

> `.venv/` and `output/` are already in `.gitignore`. {{TODO: optionally pin the four libraries above into a `requirements.txt`}}

---

## 4. Configuration

The database scripts (06–10) read credentials from environment variables. A template is provided at [`docs/env_example.txt`](./env_example.txt).

| Variable | Description |
| -------- | ----------- |
| `SUPABASE_URL` | Base URL of your Supabase project (e.g. `https://<project-id>.supabase.co`) |
| `SUPABASE_SERVICE_ROLE_KEY` | Service-role key — full access; used by ETL/validation. Keep secret. |
| `SUPABASE_ANON_KEY` | Anonymous public key — used to confirm RLS blocks anonymous access. |
| `SUPABASE_DB_URL` | PostgreSQL connection string (`postgres://postgres:<password>@db.<project-id>.supabase.co:5432/postgres`) |

Create a local `.env` from the template, fill in real values, then export them into your shell:

```bash
cp docs/env_example.txt .env
# edit .env and replace the placeholder values

set -a && source .env && set +a   # exports the variables into the current shell
```

> Never commit `.env` (it is git-ignored). Never paste real secret values into documentation.

---

## 5. Generate and validate data (local, no database)

Run from the **repository root** — these scripts read and write under `output/`.

```bash
python scripts/01_module_A_dataset_setup.py        # prompts for total clients (default 3000)
python scripts/02_module_b_dataset_generator.py    # writes output/raw/*.csv
python scripts/03_healthcheck_dataset.py           # validates raw CSVs

python scripts/04_module_C_normalizer.py           # writes output/normalized/*.csv (star schema)
python scripts/05_healthcheck_normalizer.py        # validates the normalized star schema
```

After step 05 you have a validated star schema on disk: `dim_time`, `dim_state`, `dim_clients`, `dim_products`, `dim_policies`, `fact_policies`, `fact_claims`, `fact_expenses`, `fact_taxes`.

---

## 6. Deploy schema and load into Supabase

Make sure your environment variables are exported (see [§4](#4-configuration)).

```bash
# 1) Verify connectivity and required env vars
python scripts/06_healthcheck_connection.py
```

```bash
# 2) Deploy the schema (tables, indexes, RLS, views, grants)
#    NOTE: 07 reads "schema.sql" from the current directory, so run it
#    from the schema/ folder where that file lives.
cd schema
python ../scripts/07_module_D_schema.py
cd ..
```

```bash
# 3) Verify the schema, views and RLS/REST access
python scripts/08_healthcheck_schema.py
```

```bash
# 4) Load the normalized CSVs into PostgreSQL (run from repo root)
python scripts/09_module_E_loader.py

# 5) Post-load validation: row counts, FK integrity, BI views execute
python scripts/10_healthcheck_loader.py
```

The loader truncates the fact and dimension tables inside a single transaction before `COPY`, so it is safe to re-run.

---

## 7. Validation / health checks

There is no unit-test suite; correctness is enforced by the numbered health-check scripts, which exit non-zero on failure:

- **03** — raw data: file presence, row counts, value ranges, basic referential integrity.
- **05** — normalized data: star-schema column contracts, duplicate keys, dimension/fact referential integrity.
- **06** — environment + PostgreSQL connectivity.
- **08** — expected tables and the four BI views exist; `service_role` can read the views and `anon` is blocked (RLS).
- **10** — tables are non-empty, foreign keys resolve, and all BI views execute.

Run any of them standalone, e.g.:

```bash
python scripts/05_healthcheck_normalizer.py
```

---

## 8. BI layer (Looker Studio)

The schema creates four analytical views, one per dashboard:

- `vw_dash_exec_portfolio` — executive portfolio (monthly snapshot)
- `vw_dash_claims_loss` — claims & loss performance
- `vw_dash_operations_daily` — daily operations monitoring
- `vw_dash_risk_daily` — risk & underwriting

Connect Looker Studio to your PostgreSQL/Supabase instance and build one report per view. A live example is linked from the [README](../README.md). {{TODO: document the exact Looker Studio connector settings you used}}

---

## 9. Resetting the database

`utils/erase.py` runs `master_erase.sql`, which **drops and recreates the entire `public` schema** — destructive. Like script 07, it reads the `.sql` file from the current directory, so run it from `utils/`:

```bash
cd utils
python erase.py
cd ..
```

---

## 10. Troubleshooting

- **`SQL file not found: schema.sql` / `master_erase.sql`** — scripts 07 and `utils/erase.py` resolve the `.sql` file relative to the current working directory. Run them from the folder that contains the file (`schema/` and `utils/` respectively), as shown above.
- **`Missing environment variables` from 06/08/10** — the variables were not exported into the current shell. Re-run `set -a && source .env && set +a`.
- **`psycopg2` install fails** — install `psycopg2-binary` instead of `psycopg2` (no local build tools required).
- **06 reports the database is empty even after loading** — its emptiness check looks for a legacy set of table names that differ from `schema.sql`. It is an advisory pre-flight check and does not block the pipeline.
- **`anon SHOULD NOT access ...` in 08** — Row-Level Security intentionally blocks the anonymous key; this check passes when `anon` is denied and `service_role` is allowed.
