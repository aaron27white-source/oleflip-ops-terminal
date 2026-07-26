-- 021_itad_geo.sql — geographic search for ITAD suppliers.
-- Adds latitude/longitude to itad_companies (nullable — populated by geocoding
-- the address/city/state, or set manually), plus an index for bounding-box
-- (map viewport) queries. The itad_company_summary view is recreated so its
-- `c.*` re-expands to include the new columns (SQLite freezes * at view
-- creation, so a plain ALTER wouldn't surface them through the view).

ALTER TABLE itad_companies ADD COLUMN latitude  REAL;
ALTER TABLE itad_companies ADD COLUMN longitude REAL;

CREATE INDEX IF NOT EXISTS idx_itad_geo ON itad_companies(latitude, longitude);

DROP VIEW IF EXISTS itad_company_summary;
CREATE VIEW itad_company_summary AS
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
