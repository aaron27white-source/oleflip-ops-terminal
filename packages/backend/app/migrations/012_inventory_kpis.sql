-- 012_inventory_kpis.sql — Inventory Signal feedback loop for the E-Scanner mode switch.

CREATE TABLE IF NOT EXISTS inventory_kpis (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date     TEXT NOT NULL,
    inventory_value   REAL NOT NULL,
    max_desired_value REAL NOT NULL DEFAULT 2000,
    signal_pct        REAL,                -- value/max_desired*100
    mode              TEXT,                -- 'conservative'|'normal'|'aggressive'
    sell_through_rate REAL,                -- last 30d, for Auditor calibration
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(snapshot_date)
);
