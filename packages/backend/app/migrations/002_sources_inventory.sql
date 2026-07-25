-- Phase 2 migration 002 — sources + inventory + derived-P&L view.

CREATE TABLE IF NOT EXISTS sources (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL UNIQUE,
    type              TEXT NOT NULL
                      CHECK (type IN ('govdeals','fb','itad','flea','university','other')),
    reliability_score INTEGER DEFAULT 3
                      CHECK (reliability_score BETWEEN 1 AND 5),
    notes             TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS inventory (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    INTEGER REFERENCES products(id) ON DELETE SET NULL,
    machine_model TEXT REFERENCES machines(model) ON DELETE SET NULL,
    title         TEXT NOT NULL,
    condition     TEXT,
    buy_price     REAL NOT NULL,
    buy_shipping  REAL NOT NULL DEFAULT 0,
    buy_date      TEXT NOT NULL DEFAULT (date('now')),
    source_id     INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    status        TEXT NOT NULL DEFAULT 'in_stock'
                  CHECK (status IN ('in_stock','listed','sold','scrapped')),
    sell_price    REAL,
    sell_fees     REAL DEFAULT 0,
    sell_shipping REAL DEFAULT 0,
    sell_date     TEXT,
    sold_on       TEXT,
    notes         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status);
CREATE INDEX IF NOT EXISTS idx_inventory_source ON inventory(source_id);

-- Net P&L is derived, never stored stale.
CREATE VIEW IF NOT EXISTS inventory_pnl AS
SELECT
    i.*,
    ROUND(COALESCE(i.sell_price,0) - COALESCE(i.sell_fees,0) - COALESCE(i.sell_shipping,0)
          - i.buy_price - i.buy_shipping, 2)                        AS net_profit,
    CASE WHEN i.buy_price + i.buy_shipping > 0
         THEN ROUND(100.0 * (COALESCE(i.sell_price,0) - COALESCE(i.sell_fees,0)
              - COALESCE(i.sell_shipping,0) - i.buy_price - i.buy_shipping)
              / (i.buy_price + i.buy_shipping), 0)
         ELSE NULL END                                              AS roi_pct
FROM inventory i;
