-- 018_notifications.sql — Tier 3 auto-notify pipeline.
-- Preferences (per event_type × channel), a delivery log (also used for
-- throttling/dedup), and Web Push subscriptions.

CREATE TABLE IF NOT EXISTS notification_preferences (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type     TEXT NOT NULL,          -- deal_found | deal_escalated | inventory_stale | daily_brief | agent_failure | system
    channel        TEXT NOT NULL,          -- discord | push
    enabled        INTEGER NOT NULL DEFAULT 1,
    min_headroom   REAL,                    -- deal events: min $ headroom to notify
    throttle_hours INTEGER NOT NULL DEFAULT 0,  -- suppress same event_type on same channel within N hours
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(event_type, channel)
);

CREATE TABLE IF NOT EXISTS notification_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type  TEXT NOT NULL,
    channel     TEXT NOT NULL,
    title       TEXT,
    body        TEXT,
    dedup_key   TEXT,                       -- e.g. deal lot_key, so we notify once
    success     INTEGER NOT NULL DEFAULT 1,
    error       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notif_log_type_time ON notification_log(event_type, channel, created_at);
CREATE INDEX IF NOT EXISTS idx_notif_log_dedup ON notification_log(dedup_key);

CREATE TABLE IF NOT EXISTS push_subscriptions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint    TEXT NOT NULL UNIQUE,
    p256dh_key  TEXT NOT NULL,
    auth_key    TEXT NOT NULL,
    user_agent  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Default rules (owner can change via the API / settings page).
INSERT OR IGNORE INTO notification_preferences (event_type, channel, enabled, min_headroom, throttle_hours) VALUES
    ('deal_found',      'discord', 1, 40, 0),
    ('deal_escalated',  'discord', 1, 150, 0),
    ('deal_escalated',  'push',    1, 150, 0),
    ('inventory_stale', 'discord', 1, NULL, 24),
    ('daily_brief',     'discord', 1, NULL, 24),
    ('agent_failure',   'discord', 1, NULL, 0),
    ('system',          'discord', 1, NULL, 0);
