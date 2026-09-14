-- 0001_cost_ledger.sql
-- ============================================================
-- Create the cost_ledger table for per-call LLM cost tracking.
--
-- Each row records a single LLM invocation: tenant, module,
-- model, token counts, and the computed USD cost.
--
-- alert_owner defaults to the platform team; per-module owners
-- can override this column when inserting rows.
-- ============================================================

CREATE TABLE IF NOT EXISTS cost_ledger (
    id                 BIGSERIAL PRIMARY KEY,
    tenant_id          UUID         NOT NULL,
    module_name        VARCHAR(100) NOT NULL,
    model_name         VARCHAR(200) NOT NULL,
    prompt_tokens      INTEGER      NOT NULL DEFAULT 0,
    completion_tokens  INTEGER      NOT NULL DEFAULT 0,
    total_cost_usd     NUMERIC(10, 6) NOT NULL DEFAULT 0,
    alert_owner        VARCHAR(255) NOT NULL DEFAULT 'platform-team@qa-os.internal',
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Indexes for the most common query patterns
CREATE INDEX IF NOT EXISTS idx_cost_ledger_tenant_id
    ON cost_ledger(tenant_id);

CREATE INDEX IF NOT EXISTS idx_cost_ledger_created_at
    ON cost_ledger(created_at);

-- Composite index for per-tenant time-series queries
CREATE INDEX IF NOT EXISTS idx_cost_ledger_tenant_created
    ON cost_ledger(tenant_id, created_at DESC);

-- Record this migration
INSERT INTO _migrations (name) VALUES ('0001_cost_ledger') ON CONFLICT DO NOTHING;
