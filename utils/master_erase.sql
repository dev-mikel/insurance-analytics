-- ============================================================
-- MASTER ERASE — FULL RESET (SAFE FOR PYTHON EXECUTION)
-- Supabase / PostgreSQL
-- ============================================================

BEGIN;

-- Drop everything in public schema
DROP SCHEMA IF EXISTS public CASCADE;

-- Recreate clean public schema
CREATE SCHEMA public;

-- Restore default privileges (Supabase-friendly)
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

COMMIT;

-- ============================================================
-- END — DATABASE RESET COMPLETE
-- ============================================================
