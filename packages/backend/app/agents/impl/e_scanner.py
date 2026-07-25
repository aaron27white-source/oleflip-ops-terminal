"""E-Scanner 🔍 — reads the current buying mode + unconsumed research intel, runs a
fresh deterministic GovDeals scan (best-effort; tolerates a missing Apify token),
then asks the LLM for a per-lot BUY/PASS/WATCH verdict on the open flagged deals.
Writes the verdict/note back onto flagged_deals; marks the consumed intel."""

from app.agents.base import BaseAgent
from app.agents.util import extract_json
from app.notifications import events as notify

_MODE_RULE = {
    "conservative": "CONSERVATIVE — only flag exceptional 60%+ margin lots",
    "normal": "NORMAL — flag 40%+ margin lots",
    "aggressive": "AGGRESSIVE — flag any 25%+ margin lot",
}


class EScannerAgent(BaseAgent):
    def build_context(self, conn) -> str:
        kpi = conn.execute(
            "SELECT mode FROM inventory_kpis ORDER BY snapshot_date DESC LIMIT 1"
        ).fetchone()
        self._mode = (kpi["mode"] if kpi else "normal") or "normal"

        intel = conn.execute(
            "SELECT id, category, subject, signal, action FROM intel_board "
            "WHERE consumed = 0 ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
        self._intel_ids = [r["id"] for r in intel]

        scan_note = ""
        try:
            from app.services import scanner_service
            scanner_service.run_scan(conn, watch=None, dry_run=False)
        except Exception as e:  # Apify down / no token — reason over existing lots, don't fabricate
            scan_note = f" (live scan unavailable: {getattr(e, 'message', str(e))})"

        deals = conn.execute(
            "SELECT lot_key, title, matched_model, quantity, per_unit_cost, "
            "max_bid_per_unit, headroom, margin_good FROM flagged_deals "
            "WHERE dismissed = 0 ORDER BY margin_good DESC, headroom DESC LIMIT 40"
        ).fetchall()
        deal_lines = [
            f"- lot_key={d['lot_key']} | {d['matched_model'] or '?'} x{d['quantity'] or 1} | "
            f"per-unit ${(d['per_unit_cost'] or 0):.2f} vs max ${(d['max_bid_per_unit'] or 0):.2f} | "
            f"headroom ${(d['headroom'] or 0):.2f}"
            for d in deals
        ]
        intel_lines = [f"- [{r['category']}] {r['subject']}: {r['signal']}" for r in intel]

        return (
            f"Buying mode: {_MODE_RULE.get(self._mode, self._mode)}.{scan_note}\n"
            + ("Research intel:\n" + "\n".join(intel_lines) + "\n" if intel_lines else "")
            + ("Open flagged lots:\n" + "\n".join(deal_lines)
               if deal_lines else "No open flagged lots.")
            + "\n\nFor EACH lot, decide given the mode and intel. Return ONLY a JSON array of "
              '{"lot_key": <key>, "verdict": "BUY"|"PASS"|"WATCH", "note": "<=12 words"}.'
        )

    def apply(self, conn, result, context) -> str:
        verdicts = extract_json(result.text)
        judged = 0
        buy_keys: list[str] = []
        if isinstance(verdicts, list):
            for v in verdicts:
                if not isinstance(v, dict):
                    continue
                lot_key = v.get("lot_key")
                verdict = str(v.get("verdict") or "").upper()[:8]
                note = str(v.get("note") or "")[:200]
                if lot_key and verdict:
                    cur = conn.execute(
                        "UPDATE flagged_deals SET agent_verdict = ?, agent_note = ? WHERE lot_key = ?",
                        (verdict, note, lot_key),
                    )
                    if cur.rowcount:
                        judged += 1
                        if verdict == "BUY":
                            buy_keys.append(lot_key)
        # Fire deal alerts for freshly-BUID lots (engine dedups on lot_key).
        for lk in buy_keys:
            row = conn.execute(
                "SELECT id, lot_key, matched_model, title, current_bid, headroom, agent_verdict "
                "FROM flagged_deals WHERE lot_key = ?", (lk,),
            ).fetchone()
            if row:
                notify.deal_found(conn, dict(row))
        if self._intel_ids:
            placeholders = ",".join("?" * len(self._intel_ids))
            conn.execute(
                f"UPDATE intel_board SET consumed = 1 WHERE id IN ({placeholders})",  # nosec B608 — placeholders is only ?*n; ids bound as params
                self._intel_ids,
            )
        return f"Judged {judged} lot(s) in {self._mode} mode."
