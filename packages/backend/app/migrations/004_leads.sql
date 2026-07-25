-- Phase 2 migration 004 — Source Finder leads (ITAD companies, university
-- surplus schedules, saved FB/GovDeals searches).

CREATE TABLE IF NOT EXISTS leads (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    kind           TEXT NOT NULL
                   CHECK (kind IN ('itad','university','fb_search','govdeals_search','other')),
    name           TEXT NOT NULL,
    contact        TEXT,
    location       TEXT,
    schedule_note  TEXT,
    last_contacted TEXT,
    url            TEXT,
    notes          TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
