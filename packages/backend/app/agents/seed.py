"""seed.py — insert the 8 agent rows + their active default prompt.

Called from db.init_database() after migrations (like the Phase-1 seed). Provider
and model resolve from env at seed time. Idempotent and non-destructive: existing
agent rows are left untouched (so budgets/models edited via the API survive a
restart), and a default prompt is only seeded when the agent has none yet (so the
Auditor's proposed prompts are never clobbered).
"""

import hashlib

from app.agents.definitions import AGENT_DEFS, resolve_model, resolve_provider
from app.agents.prompts import DEFAULT_PROMPTS
from app.config import settings


def _version(body: str) -> str:
    return hashlib.sha256(body.encode()).hexdigest()[:12]


def seed_agents(conn) -> None:
    for d in AGENT_DEFS:
        conn.execute(
            "INSERT INTO agents (id, display_name, layer, provider, model, schedule_cron, "
            "daily_budget_usd) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
            (d["id"], d["display_name"], d["layer"], resolve_provider(d, settings),
             resolve_model(d, settings), d["schedule_cron"], d["daily_budget_usd"]),
        )
        has_prompt = conn.execute(
            "SELECT 1 FROM agent_prompts WHERE agent_id = ? LIMIT 1", (d["id"],)
        ).fetchone()
        if not has_prompt:
            body = DEFAULT_PROMPTS[d["id"]]
            conn.execute(
                "INSERT INTO agent_prompts (agent_id, version, body, created_by, active) "
                "VALUES (?, ?, ?, 'seed', 1)",
                (d["id"], _version(body), body),
            )
    conn.commit()
