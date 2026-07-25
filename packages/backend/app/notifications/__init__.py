"""Tier 3 — notification pipeline.

Event constants + the shared engine. Agents/services call the helpers in
`events.py`; the engine routes to enabled channels (Discord, Web Push) with
per-preference throttling and dedup. Every channel is inert until its creds are
present, so this is safe to ship before anything is configured.
"""


class Event:
    DEAL_FOUND = "deal_found"
    DEAL_ESCALATED = "deal_escalated"
    INVENTORY_STALE = "inventory_stale"
    DAILY_BRIEF = "daily_brief"
    AGENT_FAILURE = "agent_failure"
    SYSTEM = "system"


ALL_EVENTS = (
    Event.DEAL_FOUND,
    Event.DEAL_ESCALATED,
    Event.INVENTORY_STALE,
    Event.DAILY_BRIEF,
    Event.AGENT_FAILURE,
    Event.SYSTEM,
)
