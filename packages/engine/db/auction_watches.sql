-- Saved auction searches for the GovDeals-style scanner. Self-creating table.
CREATE TABLE IF NOT EXISTS auction_watches (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    search_text    TEXT NOT NULL UNIQUE,
    category_ids   TEXT,   -- optional actor category filter, NULL = unfiltered
    location_state TEXT    -- optional US-state filter, NULL = nationwide
);

INSERT OR IGNORE INTO auction_watches (search_text) VALUES
('Dell OptiPlex'),
('HP EliteDesk'),
('Lenovo ThinkCentre'),
('computer lot'),
('server lot'),
('PowerEdge'),
('ProLiant'),
('scrap computers');
