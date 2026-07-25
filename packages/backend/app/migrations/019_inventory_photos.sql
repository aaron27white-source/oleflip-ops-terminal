-- 019_inventory_photos.sql — Tier 4 photo capture.
-- One row per stored image; files live under UPLOAD_DIR/{inventory_id}/.

CREATE TABLE IF NOT EXISTS inventory_photos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id  INTEGER NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,             -- stored name, unique within the item folder
    original_name TEXT,
    file_size     INTEGER,                   -- bytes (after resize)
    width         INTEGER,
    height        INTEGER,
    sort_order    INTEGER NOT NULL DEFAULT 0,
    is_primary    INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_photos_inventory ON inventory_photos(inventory_id, sort_order);
