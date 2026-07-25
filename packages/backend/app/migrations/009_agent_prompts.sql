-- 009_agent_prompts.sql — Versioned prompts so the Auditor can diff + roll forward.

CREATE TABLE IF NOT EXISTS agent_prompts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id   TEXT NOT NULL REFERENCES agents(id),
    version    TEXT NOT NULL,              -- content hash
    body       TEXT NOT NULL,
    created_by TEXT NOT NULL DEFAULT 'seed',   -- 'seed' | 'auditor' | 'human'
    active     INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(agent_id, version)
);
CREATE INDEX IF NOT EXISTS idx_prompts_active ON agent_prompts(agent_id, active);
