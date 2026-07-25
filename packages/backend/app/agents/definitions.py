"""definitions.py — the 8 agents' static config, seeded into the `agents` table.

Provider/model resolve from settings at seed time (env-configurable, never
hardcoded in agent code). schedule_cron is standard 5-field cron; None = the
agent only runs on demand. See Agent-System-Build-Spec.md §2 / §5.
"""

# Each: id, display_name, layer, default_provider, provider_attr (settings),
# model_attr (settings), schedule_cron, daily_budget_usd.
AGENT_DEFS: list[dict] = [
    {"id": "e-scanner", "display_name": "E-Scanner 🔍", "layer": "operational",
     "default_provider": "anthropic", "provider_attr": "provider_escanner",
     "model_attr": "model_escanner", "schedule_cron": "0 9 * * *", "daily_budget_usd": 0.50},
    {"id": "e-pricer", "display_name": "E-Pricer 💰", "layer": "operational",
     "default_provider": "deepseek", "provider_attr": "provider_epricer",
     "model_attr": "model_epricer", "schedule_cron": "0 8 * * 1", "daily_budget_usd": 0.10},
    {"id": "e-listings", "display_name": "E-Listings 📦", "layer": "operational",
     "default_provider": "deepseek", "provider_attr": "provider_elistings",
     "model_attr": "model_elistings", "schedule_cron": None, "daily_budget_usd": 0.10},
    {"id": "e-inventory", "display_name": "E-Inventory 📋", "layer": "operational",
     "default_provider": "deepseek", "provider_attr": "provider_einventory",
     "model_attr": "model_einventory", "schedule_cron": "0 8 * * *", "daily_budget_usd": 0.10},
    {"id": "e-customer", "display_name": "E-Customer 🤝", "layer": "operational",
     "default_provider": "anthropic", "provider_attr": "provider_ecustomer",
     "model_attr": "model_ecustomer", "schedule_cron": None, "daily_budget_usd": 0.10},
    {"id": "research-bot", "display_name": "Research Bot 🔬", "layer": "strategic",
     "default_provider": "anthropic", "provider_attr": "provider_research",
     "model_attr": "model_research", "schedule_cron": "0 7 * * 1", "daily_budget_usd": 0.50},
    {"id": "marketing", "display_name": "Marketing 📣", "layer": "strategic",
     "default_provider": "anthropic", "provider_attr": "provider_marketing",
     "model_attr": "model_marketing", "schedule_cron": "0 9 * * 3", "daily_budget_usd": 0.20},
    {"id": "auditor", "display_name": "Auditor 🎯", "layer": "strategic",
     "default_provider": "anthropic", "provider_attr": "provider_auditor",
     "model_attr": "model_auditor", "schedule_cron": "0 18 * * 0", "daily_budget_usd": 2.00},
]

AGENT_IDS = [d["id"] for d in AGENT_DEFS]


def resolve_provider(defn: dict, settings) -> str:
    """Env override (provider_*) if set, else the agent's default provider."""
    return getattr(settings, defn["provider_attr"], "") or defn["default_provider"]


def resolve_model(defn: dict, settings) -> str:
    return getattr(settings, defn["model_attr"])
