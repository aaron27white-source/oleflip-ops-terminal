"""scheduler.py — APScheduler background loop. Registers one cron job per
enabled agent that has a schedule, each calling runner.run_agent(id, 'schedule').

The agents table is the source of truth: on (re)start jobs are re-registered from
it, so a process restart re-establishes the schedule (build spec §4.3). A missed
run is logged, not backfilled. One agent's failure never crashes the loop — the
error is captured in agent_runs by BaseAgent.run().
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.agents.runner import run_agent
from app.config import settings
from app.db import get_connection

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def send_daily_brief() -> None:
    """Tier 3 — 8AM summary to the notification channels."""
    from app.notifications import events as notify
    from app.services import dashboard_service

    conn = get_connection()
    try:
        notify.daily_brief(conn, dashboard_service.dashboard(conn, "month"))
    except Exception:  # noqa: BLE001 — a bad brief must not crash the scheduler
        logger.exception("Daily brief failed")
    finally:
        conn.close()


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    if not settings.agents_scheduler_enabled:
        return None
    if _scheduler and _scheduler.running:
        return _scheduler

    sched = BackgroundScheduler(daemon=True)
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, schedule_cron FROM agents "
            "WHERE enabled = 1 AND schedule_cron IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()

    for r in rows:
        try:
            trigger = CronTrigger.from_crontab(r["schedule_cron"])
        except (ValueError, TypeError):
            logger.warning("Bad cron %r for agent %s — job not scheduled.",
                           r["schedule_cron"], r["id"])
            continue
        sched.add_job(run_agent, trigger, args=[r["id"], "schedule"],
                      id=f"agent:{r['id']}", replace_existing=True, misfire_grace_time=3600)

    # Tier 3 — daily brief at 08:00 local.
    sched.add_job(send_daily_brief, CronTrigger(hour=8, minute=0),
                  id="daily_brief", replace_existing=True, misfire_grace_time=3600)

    sched.start()
    _scheduler = sched
    logger.info("Agent scheduler started with %d job(s).", len(sched.get_jobs()))
    return sched


def scheduler_status() -> dict:
    running = bool(_scheduler and _scheduler.running)
    return {"running": running, "jobs": len(_scheduler.get_jobs()) if running else 0}


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
