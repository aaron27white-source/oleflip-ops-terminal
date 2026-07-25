-- 014_bids.sql — bid tracking (optionally linked to a watched listing).

CREATE TABLE IF NOT EXISTS bids (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    watched_listing_id INTEGER REFERENCES watched_listings(id),
    item_name          TEXT NOT NULL,
    url                TEXT,
    bid_amount         REAL NOT NULL,
    max_bid            REAL,
    auction_end        TEXT,
    status             TEXT NOT NULL DEFAULT 'active',  -- active|won|lost|outbid
    result_price       REAL,
    created_at         TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_bids_status ON bids(status);
