"""agents.py — agent monitoring + control. Mirrors scanner.py: thin router,
logic in agents_service. Mutations are guarded; reads are open. Static subpaths
(/agents/runs, /agents/costs, /agents/scores) are declared before /agents/{id}
so they don't get captured by the path param."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import get_conn
from app.security import require_api_key
from app.services import agents_service as svc

router = APIRouter(prefix="/api", tags=["agents"])
guard = [Depends(require_api_key)]


class AgentPatch(BaseModel):
    enabled: bool | None = None
    daily_budget_usd: float | None = None
    schedule_cron: str | None = None
    model: str | None = None
    provider: str | None = None


class RunRequest(BaseModel):
    # Optional on-demand input, e.g. {"message": "..."} for E-Customer or
    # {"inventory_id": 5} / {"specs": "..."} for E-Listings.
    params: dict[str, Any] | None = None


@router.get("/agents")
def list_agents(conn=Depends(get_conn)):
    return svc.list_agents(conn)


@router.get("/agents/runs")
def runs(agent_id: str | None = None, status: str | None = None,
         limit: int = 50, offset: int = 0, conn=Depends(get_conn)):
    return svc.list_runs(conn, agent_id, status, limit, offset)


@router.get("/agents/costs")
def costs(conn=Depends(get_conn)):
    return svc.costs(conn)


@router.get("/agents/scores")
def scores(conn=Depends(get_conn)):
    return svc.scores(conn)


@router.get("/intel")
def intel(limit: int = 50, conn=Depends(get_conn)):
    return svc.list_intel(conn, limit)


@router.get("/agents/prompts/pending")
def pending_prompts(conn=Depends(get_conn)):
    return svc.pending_prompts(conn)


@router.post("/agents/prompts/{prompt_id}/activate", dependencies=guard)
def activate_prompt(prompt_id: int, conn=Depends(get_conn)):
    return svc.activate_prompt(conn, prompt_id)


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str, conn=Depends(get_conn)):
    return svc.get_agent(conn, agent_id)


@router.get("/agents/{agent_id}/prompts")
def agent_prompts(agent_id: str, conn=Depends(get_conn)):
    return svc.list_prompts(conn, agent_id)


@router.post("/agents/{agent_id}/run", dependencies=guard)
def run_agent(agent_id: str, body: RunRequest | None = None, conn=Depends(get_conn)):
    return svc.run_now(conn, agent_id, body.params if body else None)


@router.patch("/agents/{agent_id}", dependencies=guard)
def update_agent(agent_id: str, body: AgentPatch, conn=Depends(get_conn)):
    return svc.update_agent(conn, agent_id, body.model_dump(exclude_unset=True))
