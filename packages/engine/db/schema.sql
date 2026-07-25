-- it-parts reference engine — schema
-- Open, generic reference implementation of the pricing engine the backend
-- expects (parts catalog, sold-price history, machine profiles). Swap the whole
-- packages/engine/ out via PHASE1_PATH to plug in your own engine.

-- Core parts catalog — every distinct item that can be resold.
CREATE TABLE IF NOT EXISTS parts (
    id           TEXT PRIMARY KEY,   -- e.g. 'RAM-D4-16GB-DT'
    name         TEXT NOT NULL,      -- '16GB DDR4 Desktop RAM'
    category     TEXT NOT NULL,      -- 'RAM','SSD','CPU','GPU','WIFI','NIC','PSU'
    subcategory  TEXT,               -- 'DDR4','NVMe','SATA', etc.
    form_factor  TEXT,               -- 'DIMM','SODIMM','M.2','2.5"', etc.
    source_models TEXT,              -- which machines they typically come from
    notes        TEXT
);

-- Sold-price history — one row per observed sale; current price is derived.
CREATE TABLE IF NOT EXISTS price_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id     TEXT NOT NULL REFERENCES parts(id),
    price       REAL NOT NULL,
    source      TEXT NOT NULL,               -- 'eBay_sold','manual', etc.
    date        TEXT NOT NULL,               -- ISO date of the sale
    condition   TEXT DEFAULT 'used',
    url         TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Current market snapshot, auto-derived from the last 30 days of history.
CREATE VIEW IF NOT EXISTS current_prices AS
SELECT
    part_id,
    ROUND(AVG(price), 2) AS avg_price_30d,
    ROUND(AVG(price) FILTER (WHERE date >= date('now', '-90 days')), 2) AS avg_price_90d,
    MIN(price) AS lowest_price,
    MAX(price) AS highest_price,
    COUNT(*) AS sample_count
FROM price_history
WHERE date >= date('now', '-30 days')
GROUP BY part_id;

-- Net-profit view: sell price minus a flat marketplace fee and per-category shipping.
CREATE VIEW IF NOT EXISTS net_profit AS
SELECT
    p.part_id,
    p.avg_price_30d AS sell_price,
    ROUND(p.avg_price_30d * 0.1325, 2) AS ebay_fee,
    CASE pt.category
        WHEN 'RAM' THEN 5.00 WHEN 'SSD' THEN 5.50 WHEN 'CPU' THEN 4.50
        WHEN 'WIFI' THEN 4.25 WHEN 'NIC' THEN 7.00 WHEN 'GPU' THEN 9.00
        WHEN 'PSU' THEN 12.00 ELSE 6.00
    END AS shipping_cost,
    ROUND(
        p.avg_price_30d - (p.avg_price_30d * 0.1325) -
        CASE pt.category
            WHEN 'RAM' THEN 5.00 WHEN 'SSD' THEN 5.50 WHEN 'CPU' THEN 4.50
            WHEN 'WIFI' THEN 4.25 WHEN 'NIC' THEN 7.00 WHEN 'GPU' THEN 9.00
            WHEN 'PSU' THEN 12.00 ELSE 6.00
        END, 2) AS net_profit
FROM current_prices p
JOIN parts pt ON p.part_id = pt.id;

-- Machine profiles + their part bill-of-materials.
CREATE TABLE IF NOT EXISTS machines (
    model                 TEXT PRIMARY KEY,   -- e.g. 'OptiPlex 7080'
    brand                 TEXT NOT NULL,
    generation            TEXT,
    standard_ram          TEXT,
    standard_ssd          TEXT,
    standard_cpu          TEXT,
    standard_wifi         TEXT,
    standard_psu          TEXT,
    has_cooler            INTEGER DEFAULT 1,
    estimated_total_value REAL,               -- NULL = profile with no pricing yet
    safe_max_bid          REAL,
    notes                 TEXT
);

CREATE TABLE IF NOT EXISTS machine_parts (
    model    TEXT NOT NULL REFERENCES machines(model),
    part_id  TEXT NOT NULL REFERENCES parts(id),
    qty      INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (model, part_id)
);
