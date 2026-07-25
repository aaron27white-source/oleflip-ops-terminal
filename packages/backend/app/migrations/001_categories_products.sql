-- Phase 2 migration 001 — general resale catalog (categories + products).
-- Additive: does not touch Phase 1 tables (parts/machines/etc).

CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    icon        TEXT,
    parent_id   INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    brand           TEXT,
    model           TEXT NOT NULL,
    specs_json      TEXT,
    condition_tiers TEXT,
    est_low         REAL,
    est_high        REAL,
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(category_id, brand, model)
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
