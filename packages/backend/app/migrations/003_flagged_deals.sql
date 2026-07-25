-- Phase 2 migration 003 — pre-purchase opportunities flagged by the scanner.
-- NOT tied to inventory (you haven't bought these yet) — this is the fix for
-- the source brief's impossible deals(inventory_id) foreign key.

CREATE TABLE IF NOT EXISTS flagged_deals (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    source         TEXT NOT NULL DEFAULT 'govdeals',
    lot_key        TEXT,
    title          TEXT NOT NULL,
    matched_model  TEXT,
    current_bid    REAL,
    max_bid        REAL,
    headroom       REAL,
    margin_good    INTEGER NOT NULL DEFAULT 0,
    url            TEXT,
    flagged_at     TEXT NOT NULL DEFAULT (datetime('now')),
    dismissed      INTEGER NOT NULL DEFAULT 0,
    UNIQUE(source, lot_key)
);
CREATE INDEX IF NOT EXISTS idx_flagged_open ON flagged_deals(dismissed, margin_good);
