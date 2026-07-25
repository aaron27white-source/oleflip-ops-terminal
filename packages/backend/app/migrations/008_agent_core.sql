-- 008_agent_core.sql — Agent registry (seeded) + per-run telemetry + budgets.

CREATE TABLE IF NOT EXISTS agents (
    id               TEXT PRIMARY KEY,        -- 'e-scanner', 'auditor', ...
    display_name     TEXT NOT NULL,
    layer            TEXT NOT NULL,           -- 'operational' | 'strategic'
    provider         TEXT NOT NULL,           -- 'anthropic' | 'deepseek' | 'openai' | 'grok'
    model            TEXT NOT NULL,           -- resolved at seed time from env, updatable
    schedule_cron    TEXT,                    -- NULL = on-demand only
    daily_budget_usd REAL NOT NULL DEFAULT 0.50,
    enabled          INTEGER NOT NULL DEFAULT 1,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id       TEXT NOT NULL REFERENCES agents(id),
    started_at     TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at    TEXT,
    trigger        TEXT NOT NULL DEFAULT 'schedule',   -- 'schedule' | 'manual' | 'chain'
    provider       TEXT,
    model          TEXT,
    tokens_in      INTEGER DEFAULT 0,
    tokens_out     INTEGER DEFAULT 0,
    cost_usd       REAL DEFAULT 0,
    status         TEXT NOT NULL DEFAULT 'running',     -- running|success|error|partial|skipped_budget
    output_summary TEXT,
    error          TEXT,
    prompt_version TEXT                                 -- hash of prompt used
);
CREATE INDEX IF NOT EXISTS idx_runs_agent_time ON agent_runs(agent_id, started_at);
