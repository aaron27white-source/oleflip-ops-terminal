"""health.py — liveness + proof the Phase 1 import and DB are wired up, plus
agent-system health (scheduler, provider keys, last successful run per agent)."""

from fastapi import APIRouter, Depends

from app.agents.scheduler import scheduler_status
from app.db import get_conn
from app.services.agents_service import provider_status

router = APIRouter(tags=["meta"])

# Populated once at startup by main.lifespan.
STATUS: dict = {"phase1_parts": None, "migration_version": None}


@router.get("/api/health")
def health(conn=Depends(get_conn)):
    db_ok = True
    last_success: dict = {}
    try:
        conn.execute("SELECT 1").fetchone()
        rows = conn.execute(
            "SELECT agent_id, MAX(finished_at) AS last FROM agent_runs "
            "WHERE status = 'success' GROUP BY agent_id"
        ).fetchall()
        last_success = {r["agent_id"]: r["last"] for r in rows}
    except Exception:
        db_ok = False
    return {
        "status": "ok",
        "db_ok": db_ok,
        "phase1_ok": STATUS.get("phase1_parts") is not None,
        "phase1_parts": STATUS.get("phase1_parts"),
        "migration_version": STATUS.get("migration_version"),
        "agents": {
            "scheduler": scheduler_status(),
            "providers": provider_status(),
            "last_success": last_success,
        },
    }
