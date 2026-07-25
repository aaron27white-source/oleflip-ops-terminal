-- Phase 2.5 migration 007 — ITAD CRM: supplier database, call logs, purchases,
-- and a derived per-company summary view. Additive; the only touch to an
-- existing table is a one-time copy of kind='itad' leads into itad_companies.

CREATE TABLE IF NOT EXISTS itad_companies (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL UNIQUE,
    phone          TEXT,
    address        TEXT,
    city           TEXT NOT NULL DEFAULT 'Houston',
    state          TEXT NOT NULL DEFAULT 'TX',
    website        TEXT,
    contact_person TEXT,
    status         TEXT NOT NULL DEFAULT 'not-contacted'
                   CHECK (status IN ('not-contacted','contacted','active','dead')),
    reliability    INTEGER DEFAULT 3 CHECK (reliability BETWEEN 1 AND 5),
    sells_singles  INTEGER NOT NULL DEFAULT 0,
    typical_bare_price   REAL,
    typical_loaded_price REAL,
    notes          TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_itad_status ON itad_companies(status);
CREATE INDEX IF NOT EXISTS idx_itad_city ON itad_companies(city);

CREATE TABLE IF NOT EXISTS itad_call_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id    INTEGER NOT NULL REFERENCES itad_companies(id) ON DELETE CASCADE,
    call_date     TEXT NOT NULL DEFAULT (date('now')),
    spoke_with    TEXT,
    notes         TEXT NOT NULL,
    has_inventory INTEGER NOT NULL DEFAULT 0,
    pricing_text  TEXT,
    follow_up     TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_calls_company ON itad_call_logs(company_id);

CREATE TABLE IF NOT EXISTS itad_purchases (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id    INTEGER NOT NULL REFERENCES itad_companies(id) ON DELETE CASCADE,
    purchase_date TEXT NOT NULL DEFAULT (date('now')),
    model         TEXT,
    quantity      INTEGER NOT NULL,
    unit_price    REAL NOT NULL,
    total_cost    REAL NOT NULL,
    had_ram       INTEGER NOT NULL DEFAULT 0,
    had_storage   INTEGER NOT NULL DEFAULT 0,
    working_count INTEGER,
    notes         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_purch_company ON itad_purchases(company_id);

-- Per-company rollup — derived, never stored stale (same approach as inventory_pnl).
CREATE VIEW IF NOT EXISTS itad_company_summary AS
SELECT
    c.*,
    (SELECT COUNT(*)        FROM itad_call_logs l WHERE l.company_id = c.id) AS call_count,
    (SELECT MAX(l.call_date) FROM itad_call_logs l WHERE l.company_id = c.id) AS last_call_date,
    (SELECT COUNT(*)        FROM itad_purchases p WHERE p.company_id = c.id) AS purchase_count,
    COALESCE((SELECT SUM(p.total_cost) FROM itad_purchases p WHERE p.company_id = c.id), 0) AS total_spent,
    COALESCE((SELECT SUM(p.quantity)   FROM itad_purchases p WHERE p.company_id = c.id), 0) AS total_units,
    (SELECT ROUND(AVG(p.unit_price), 2) FROM itad_purchases p WHERE p.company_id = c.id) AS avg_unit_price,
    (SELECT CASE WHEN SUM(CASE WHEN p.working_count IS NOT NULL THEN p.quantity END) > 0
             THEN ROUND(100.0 * SUM(p.working_count) /
                  SUM(CASE WHEN p.working_count IS NOT NULL THEN p.quantity END), 0) END
     FROM itad_purchases p WHERE p.company_id = c.id) AS win_rate_pct
FROM itad_companies c;

-- One-time: graduate existing kind='itad' leads into the CRM (leads left intact).
INSERT OR IGNORE INTO itad_companies (name, phone, city, notes, status)
SELECT name, contact, COALESCE(location, 'Houston'), notes, 'not-contacted'
FROM leads WHERE kind = 'itad';
