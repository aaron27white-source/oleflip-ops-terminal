"""Auditor 🎯 — weekly evaluator of the other seven agents. Reads each agent's
past-week runs + prior scores, scores them 1-10 with a trend, and may propose an
improved system-prompt. Proposed prompts are inserted INACTIVE (active=0) — a
human activates them via the prompt-activation endpoint (build spec §5, §10.6)."""

import hashlib
import json

from app.agents.base import BaseAgent
from app.agents.util import extract_json, week_start


class AuditorAgent(BaseAgent):
    def build_context(self, conn) -> str:
        self._week = week_start()
        rows = conn.execute(
            "SELECT id, display_name FROM agents WHERE id != 'auditor' ORDER BY id"
        ).fetchall()
        self._targets = {r["id"] for r in rows}
        blocks = []
        for r in rows:
            st = conn.execute(
                "SELECT COUNT(*) AS runs, "
                "SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) AS ok, "
                "SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) AS err, "
                "COALESCE(SUM(cost_usd),0) AS cost FROM agent_runs "
                "WHERE agent_id = ? AND started_at >= date('now','-7 days')", (r["id"],)
            ).fetchone()
            recent = conn.execute(
                "SELECT output_summary FROM agent_runs WHERE agent_id = ? AND status='success' "
                "ORDER BY id DESC LIMIT 2", (r["id"],)
            ).fetchall()
            summ = " | ".join(s["output_summary"][:120] for s in recent if s["output_summary"])
            blocks.append(
                f"{r['id']} ({r['display_name']}): {st['runs']} runs, {st['ok'] or 0} ok, "
                f"{st['err'] or 0} err, ${st['cost']:.4f}. Recent: {summ or 'no successful runs'}"
            )
        return (
            "Audit these agents for the past week. For EACH agent id, score 1-10, give a trend "
            "(up/down/flat), 1-2 sentence notes on coverage gaps, and optionally a full improved "
            "system-prompt if you can meaningfully raise its quality.\n"
            + "\n".join(blocks)
            + '\n\nReturn ONLY a JSON array of {"agent_id":..., "score":<1-10>, '
              '"trend":"up|down|flat", "notes":"...", "proposed_prompt":"<full prompt or empty>"}.'
        )

    def apply(self, conn, result, context) -> str:
        items = extract_json(result.text)
        if not isinstance(items, list):
            return "No parseable audit produced this run."
        scored = proposed = 0
        for it in items:
            if not isinstance(it, dict) or it.get("agent_id") not in self._targets:
                continue
            aid = it["agent_id"]
            try:
                score = max(1, min(10, int(it.get("score"))))
            except (TypeError, ValueError):
                score = None
            prev = conn.execute(
                "SELECT score FROM agent_scores WHERE agent_id = ? ORDER BY week_start DESC LIMIT 1",
                (aid,),
            ).fetchone()
            conn.execute(
                "INSERT INTO agent_scores (agent_id, week_start, week_end, score, prev_score, "
                "trend, metrics_json, notes) VALUES (?, ?, date(?, '+6 days'), ?, ?, ?, ?, ?) "
                "ON CONFLICT(agent_id, week_start) DO UPDATE SET score=excluded.score, "
                "prev_score=excluded.prev_score, trend=excluded.trend, notes=excluded.notes",
                (aid, self._week, self._week, score, prev["score"] if prev else None,
                 str(it.get("trend") or "")[:10], json.dumps({"by": "auditor"}),
                 str(it.get("notes") or "")[:500]),
            )
            scored += 1
            body = str(it.get("proposed_prompt") or "").strip()
            if len(body) > 40:
                version = hashlib.sha256(body.encode()).hexdigest()[:12]
                if not conn.execute("SELECT 1 FROM agent_prompts WHERE agent_id = ? AND version = ?",
                                    (aid, version)).fetchone():
                    conn.execute(
                        "INSERT INTO agent_prompts (agent_id, version, body, created_by, active) "
                        "VALUES (?, ?, ?, 'auditor', 0)", (aid, version, body))
                    proposed += 1
        return (f"Scored {scored} agent(s); proposed {proposed} prompt change(s) "
                "(inactive, pending approval).")
