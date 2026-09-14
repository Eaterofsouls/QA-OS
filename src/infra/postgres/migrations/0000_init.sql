-- 0000_init.sql
-- ============================================================
-- Initialize migration tracking table.
-- This is the first migration and is always run.
-- All subsequent migrations are recorded in _migrations.
-- ============================================================

CREATE TABLE IF NOT EXISTS _migrations (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- Record this migration itself (idempotent via ON CONFLICT DO NOTHING)
INSERT INTO _migrations (name) VALUES ('0000_init') ON CONFLICT DO NOTHING;
