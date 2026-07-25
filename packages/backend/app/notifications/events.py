"""events.py — typed helpers agents/services call when something noteworthy
happens. Each builds the title/body and hands off to the engine. Adapted to the
real flagged_deals shape (agent_verdict + headroom; there is no numeric score)."""

from datetime import datetime

from app.notifications import Event
from app.notifications.channels import COLOR_BAD, COLOR_GOOD, COLOR_INFO, COLOR_WARN
from app.notifications.engine import engine

ESCALATE_HEADROOM = 150.0  # $ headroom that promotes a deal to "escalated"


def deal_found(conn, deal: dict) -> dict:
    hd = float(deal.get("headroom") or 0)
    model = deal.get("matched_model") or deal.get("title") or "lot"
    escalated = hd >= ESCALATE_HEADROOM
    event = Event.DEAL_ESCALATED if escalated else Event.DEAL_FOUND
    body = (
        f"{deal.get('agent_verdict') or 'BUY'} · headroom +${hd:.0f} · "
        f"bid ${float(deal.get('current_bid') or 0):.0f}\n{deal.get('title') or ''}"
    )
    return engine.dispatch(
        conn, event, f"🔥 Deal: {model}", body,
        data={"url": "/scanner", "color": COLOR_GOOD},
        dedup_key=f"deal:{deal.get('lot_key')}", headroom=hd,
    )


def inventory_stale(conn, item: dict, days: int) -> dict:
    color = COLOR_BAD if days >= 90 else COLOR_WARN
    icon = "🔴" if days >= 90 else "🟡"
    body = f"{item.get('title')} · cost ${float(item.get('buy_price') or 0):.0f} · {item.get('status')}"
    return engine.dispatch(
        conn, Event.INVENTORY_STALE, f"{icon} Sitting {days} days", body,
        data={"url": "/inventory", "color": color},
        dedup_key=f"stale:{item.get('id')}:{days // 30}",  # re-alert as it crosses 30-day bands
    )


def daily_brief(conn, stats: dict) -> dict:
    body = (
        f"**In stock:** {stats.get('items_in_stock', 0)} items\n"
        f"**Tied up:** ${float(stats.get('unrealized_cost', 0)):.0f}\n"
        f"**Profit this period:** ${float(stats.get('profit_this_period', 0)):.0f}\n"
        f"**Deals to review:** {len(stats.get('best_deals', []))}\n"
        f"**Stale-price parts:** {stats.get('staleness_warnings', 0)}"
    )
    return engine.dispatch(
        conn, Event.DAILY_BRIEF,
        f"📋 Daily Brief — {datetime.now().strftime('%b %d')}", body,
        data={"url": "/", "color": COLOR_INFO},
    )


def agent_failure(conn, agent_id: str, error: str) -> dict:
    return engine.dispatch(
        conn, Event.AGENT_FAILURE, f"🚨 Agent failed: {agent_id}", error[:500],
        data={"url": "/agents", "color": COLOR_BAD},
    )
