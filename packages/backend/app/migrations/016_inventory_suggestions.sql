-- 016_inventory_suggestions.sql — Tier 1 gap-fill.
-- Structured, actionable suggestions the Inventory Agent (e-inventory) writes for
-- aging stock, surfaced on the /inventory screen. suggested_price is nullable on
-- purpose: the agent only fills it when it has a real basis, never a fabricated one.

CREATE TABLE IF NOT EXISTS inventory_suggestions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id       INTEGER NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    suggested_price    REAL,                       -- nullable: only set when grounded
    suggested_platform TEXT,                        -- 'ebay' | 'facebook' | 'offerup' | ...
    reasoning          TEXT NOT NULL DEFAULT '',
    days_held          INTEGER,
    applied            INTEGER NOT NULL DEFAULT 0,  -- has the owner acted on / dismissed it?
    agent_run_id       INTEGER REFERENCES agent_runs(id),
    created_at         TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_inv_suggestions_open
    ON inventory_suggestions(applied, created_at);
