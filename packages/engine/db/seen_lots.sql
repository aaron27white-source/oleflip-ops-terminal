-- Dedup table for auction lots already seen by the scanner (no seed rows).
CREATE TABLE IF NOT EXISTS seen_lots (
    source     TEXT NOT NULL,
    lot_key    TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    PRIMARY KEY (source, lot_key)
);
