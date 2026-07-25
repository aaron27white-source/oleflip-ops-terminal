-- 017_voice.sql — Tier 2 voice logging.
-- Audit trail for every transcript parsed into inventory + a dedicated source.
-- NOTE: sources.type is CHECK-constrained (govdeals/fb/itad/flea/university/other),
-- so the Voice Log source uses type 'other', not 'voice'.

INSERT OR IGNORE INTO sources (name, type, reliability_score, notes)
VALUES ('Voice Log', 'other', 3, 'Items logged hands-free via voice / flea-market mode');

CREATE TABLE IF NOT EXISTS voice_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_transcript TEXT NOT NULL,
    parsed_json    TEXT,                         -- JSON the LLM returned
    items_created  INTEGER NOT NULL DEFAULT 0,
    provider       TEXT,
    model          TEXT,
    tokens_in      INTEGER DEFAULT 0,
    tokens_out     INTEGER DEFAULT 0,
    cost_usd       REAL DEFAULT 0,
    error          TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_voice_logs_time ON voice_logs(created_at);
