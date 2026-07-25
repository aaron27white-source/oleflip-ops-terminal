"""agents_service.py — reads/writes for the agent monitoring surface. Routers stay
thin and call these; the run pipeline itself lives in app/agents/."""

import calendar
from datetime import date

from app.agents import runner
from app.config import settings
from app.errors import ApiError

_EDITABLE = {"enabled", "daily_budget_usd", "schedule_cron", "model", "provider"}


def list_agents(conn) -> dict:
    rows = conn.execute(
        """
        SELECT a.*,
          (SELECT status     FROM agent_runs r WHERE r.agent_id = a.id
             ORDER BY r.started_at DESC, r.id DESC LIMIT 1) AS last_status,
          (SELECT started_at FROM agent_runs r WHERE r.agent_id = a.id
             ORDER BY r.started_at DESC, r.id DESC LIMIT 1) AS last_run_at,
          (SELECT COUNT(*) FROM agent_runs r WHERE r.agent_id = a.id
             AND date(r.started_at) = date('now')) AS runs_today,
          (SELECT COALESCE(SUM(cost_usd), 0) FROM agent_runs r WHERE r.agent_id = a.id
             AND date(r.started_at) = date('now')) AS cost_today,
          (SELECT COUNT(*) FROM agent_runs r WHERE r.agent_id = a.id AND r.status = 'error'
             AND date(r.started_at) = date('now')) AS errors_today
        FROM agents a
        ORDER BY a.layer DESC, a.id
        """
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def get_agent(conn, agent_id: str) -> dict:
    row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if not row:
        raise ApiError(404, "agent_not_found", f"No agent {agent_id!r}.")
    prompt = conn.execute(
        "SELECT version, body, created_by, created_at FROM agent_prompts "
        "WHERE agent_id = ? AND active = 1 ORDER BY id DESC LIMIT 1",
        (agent_id,),
    ).fetchone()
    runs = conn.execute(
        "SELECT * FROM agent_runs WHERE agent_id = ? ORDER BY started_at DESC, id DESC LIMIT 20",
        (agent_id,),
    ).fetchall()
    return {
        "agent": dict(row),
        "active_prompt": dict(prompt) if prompt else None,
        "recent_runs": [dict(r) for r in runs],
    }


def run_now(conn, agent_id: str, params: dict | None = None) -> dict:
    # Validate existence for a clean 404 before the pipeline runs.
    if not conn.execute("SELECT 1 FROM agents WHERE id = ?", (agent_id,)).fetchone():
        raise ApiError(404, "agent_not_found", f"No agent {agent_id!r}.")
    return runner.run_agent(agent_id, trigger="manual", conn=conn, params=params)


def list_runs(conn, agent_id: str | None = None, status: str | None = None,
              limit: int = 50, offset: int = 0) -> dict:
    where, params = [], []
    if agent_id:
        where.append("agent_id = ?")
        params.append(agent_id)
    if status:
        where.append("status = ?")
        params.append(status)
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    total = conn.execute(f"SELECT COUNT(*) FROM agent_runs {clause}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM agent_runs {clause} ORDER BY started_at DESC, id DESC LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": total}


def costs(conn) -> dict:
    by_agent = conn.execute(
        "SELECT agent_id, COALESCE(SUM(cost_usd), 0) AS total, COUNT(*) AS runs "
        "FROM agent_runs GROUP BY agent_id ORDER BY total DESC"
    ).fetchall()
    by_day = conn.execute(
        "SELECT date(started_at) AS day, COALESCE(SUM(cost_usd), 0) AS cost "
        "FROM agent_runs WHERE started_at >= date('now', '-30 days') "
        "GROUP BY day ORDER BY day"
    ).fetchall()
    month_total = conn.execute(
        "SELECT COALESCE(SUM(cost_usd), 0) FROM agent_runs "
        "WHERE started_at >= date('now', 'start of month')"
    ).fetchone()[0]
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    projected = round(month_total / today.day * days_in_month, 4) if today.day else month_total
    return {"by_agent": [dict(r) for r in by_agent],
            "by_day": [dict(r) for r in by_day],
            "month_total": month_total,
            "projected_month": projected}


def scores(conn) -> dict:
    rows = conn.execute(
        "SELECT * FROM agent_scores ORDER BY week_start DESC, agent_id"
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def list_intel(conn, limit: int = 50) -> dict:
    """Research Bot's market-intel feed (intel_board), newest first."""
    rows = conn.execute(
        "SELECT id, category, subject, signal, action, confidence, week_start, consumed, "
        "created_at FROM intel_board ORDER BY created_at DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def update_agent(conn, agent_id: str, data: dict) -> dict:
    fields = {k: v for k, v in data.items() if k in _EDITABLE and v is not None}
    if not conn.execute("SELECT 1 FROM agents WHERE id = ?", (agent_id,)).fetchone():
        raise ApiError(404, "agent_not_found", f"No agent {agent_id!r}.")
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(f"UPDATE agents SET {sets} WHERE id = ?",  # nosec B608 — keys are the _EDITABLE whitelist; values bound as params
                     [*fields.values(), agent_id])
        conn.commit()
    return get_agent(conn, agent_id)


def provider_status() -> dict:
    """Which provider keys are present (booleans only — never the values)."""
    return {p: bool(settings.provider_key(p))
            for p in ("anthropic", "deepseek", "openai", "grok")}


# ── prompt versions + activation (Auditor's proposals gate) ──────────────────
def list_prompts(conn, agent_id: str) -> dict:
    if not conn.execute("SELECT 1 FROM agents WHERE id = ?", (agent_id,)).fetchone():
        raise ApiError(404, "agent_not_found", f"No agent {agent_id!r}.")
    rows = conn.execute(
        "SELECT id, version, body, created_by, active, created_at FROM agent_prompts "
        "WHERE agent_id = ? ORDER BY id DESC", (agent_id,)
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def pending_prompts(conn) -> dict:
    """Auditor-proposed prompts awaiting human activation (the review queue)."""
    rows = conn.execute(
        "SELECT p.id, p.agent_id, a.display_name, p.version, p.body, p.created_at "
        "FROM agent_prompts p JOIN agents a ON a.id = p.agent_id "
        "WHERE p.active = 0 AND p.created_by = 'auditor' ORDER BY p.id DESC"
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def activate_prompt(conn, prompt_id: int) -> dict:
    row = conn.execute("SELECT agent_id FROM agent_prompts WHERE id = ?", (prompt_id,)).fetchone()
    if not row:
        raise ApiError(404, "prompt_not_found", f"No prompt version {prompt_id}.")
    agent_id = row["agent_id"]
    conn.execute("UPDATE agent_prompts SET active = 0 WHERE agent_id = ?", (agent_id,))
    conn.execute("UPDATE agent_prompts SET active = 1 WHERE id = ?", (prompt_id,))
    conn.commit()
    return {"activated": prompt_id, "agent_id": agent_id}
