-- 013_watched_listings.sql — post-flag watch list (distinct from pre-purchase flagged_deals).

CREATE TABLE IF NOT EXISTS watched_listings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name       TEXT NOT NULL,
    url             TEXT,
    source          TEXT,
    target_price    REAL,
    max_bid         REAL,
    last_price_seen REAL,
    status          TEXT NOT NULL DEFAULT 'active',  -- active|won|lost|expired|cancelled
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_watch_status ON watched_listings(status);
