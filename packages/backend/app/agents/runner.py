"""runner.py — the single public entry point for running an agent. Used by the
scheduler, the manual "Trigger Now" endpoint, and (later) agent chaining.

Manages its own connection when one isn't supplied (the scheduler runs outside
any request), so a run is always self-contained."""

from app.agents.registry import load_agent
from app.db import get_connection


def run_agent(agent_id: str, trigger: str = "manual", transport=None, conn=None,
              params: dict | None = None) -> dict:
    own = conn is None
    conn = conn or get_connection()
    try:
        return load_agent(conn, agent_id).run(conn, trigger=trigger, transport=transport,
                                              params=params)
    finally:
        if own:
            conn.close()
