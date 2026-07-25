-- 010_agent_scores.sql — Auditor's weekly scorecard per agent.

CREATE TABLE IF NOT EXISTS agent_scores (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id            TEXT NOT NULL REFERENCES agents(id),
    week_start          TEXT NOT NULL,
    week_end            TEXT NOT NULL,
    score               INTEGER,               -- 1..10
    prev_score          INTEGER,
    trend               TEXT,                  -- 'up'|'down'|'flat'
    metrics_json        TEXT,                  -- runs, findings, actionable_pct, etc.
    prompt_version      TEXT,
    prev_prompt_version TEXT,
    notes               TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(agent_id, week_start)
);
