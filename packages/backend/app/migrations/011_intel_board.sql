-- 011_intel_board.sql — Research Bot findings; read by E-Scanner (pre-scan) + Auditor (pre-eval).

CREATE TABLE IF NOT EXISTS intel_board (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL,             -- 'price_drop'|'new_gen'|'new_product'|'business'
    subject     TEXT NOT NULL,
    signal      TEXT NOT NULL,
    action      TEXT,                      -- routed hint, e.g. 'e-pricer: refresh DDR4'
    confidence  TEXT,                      -- 'high'|'med'|'low'
    source_urls TEXT,
    week_start  TEXT NOT NULL,
    consumed    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_intel_week ON intel_board(week_start, consumed);
