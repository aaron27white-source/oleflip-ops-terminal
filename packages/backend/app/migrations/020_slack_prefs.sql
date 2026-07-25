-- 020_slack_prefs.sql — seed Slack notification rules (mirrors the Discord defaults).
-- Slack, like Discord, stays inert until SLACK_WEBHOOK_URL is set in .env — this
-- just makes the channel show up (toggleable) on the settings page.

INSERT OR IGNORE INTO notification_preferences (event_type, channel, enabled, min_headroom, throttle_hours) VALUES
    ('deal_found',      'slack', 1, 40, 0),
    ('deal_escalated',  'slack', 1, 150, 0),
    ('inventory_stale', 'slack', 1, NULL, 24),
    ('daily_brief',     'slack', 1, NULL, 24),
    ('agent_failure',   'slack', 1, NULL, 0),
    ('system',          'slack', 1, NULL, 0);
