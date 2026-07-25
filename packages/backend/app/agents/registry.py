"""registry.py — maps agent id -> Agent class, and builds an instance from the
agents table row. Sprint 1: everything uses BaseAgent's generic behavior; later
sprints register specific impls in AGENT_CLASSES (id -> subclass)."""

from app.agents.base import BaseAgent
from app.agents.impl.auditor import AuditorAgent
from app.agents.impl.e_customer import ECustomerAgent
from app.agents.impl.e_inventory import EInventoryAgent
from app.agents.impl.e_listings import EListingsAgent
from app.agents.impl.e_pricer import EPricerAgent
from app.agents.impl.e_scanner import EScannerAgent
from app.agents.impl.marketing import MarketingAgent
from app.agents.impl.research_bot import ResearchBotAgent
from app.errors import ApiError

# All 8 agents now have concrete impls.
AGENT_CLASSES: dict[str, type[BaseAgent]] = {
    "e-scanner": EScannerAgent,
    "e-pricer": EPricerAgent,
    "e-listings": EListingsAgent,
    "e-inventory": EInventoryAgent,
    "e-customer": ECustomerAgent,
    "research-bot": ResearchBotAgent,
    "marketing": MarketingAgent,
    "auditor": AuditorAgent,
}


def get_agent_class(agent_id: str) -> type[BaseAgent]:
    return AGENT_CLASSES.get(agent_id, BaseAgent)


def load_agent(conn, agent_id: str) -> BaseAgent:
    row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if not row:
        raise ApiError(404, "agent_not_found", f"No agent {agent_id!r}.")
    return get_agent_class(agent_id)(dict(row))
