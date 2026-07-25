"""base.py — BaseAgent lifecycle. Every run goes through run() so no agent can
skip budget-checking, run-logging, or error capture (build spec §4.2).

Sprint 1: BaseAgent is also the default behavior for agents without a specific
impl yet — build_context asks the model for a short status, apply stores it.
Later sprints subclass BaseAgent and override build_context / apply to read and
write the agent's real target tables (registry maps id -> class).
"""

from app.agents import llm
from app.errors import ApiError


class BaseAgent:
    def __init__(self, row: dict):
        self.id = row["id"]
        self.display_name = row["display_name"]
        self.provider = row["provider"]
        self.model = row["model"]
        self.daily_budget_usd = row["daily_budget_usd"]
        self.params: dict = {}  # optional on-demand input (e.g. a customer message)

    # ── overridable seams ────────────────────────────────────────────────────
    def build_context(self, conn) -> str:
        """Deterministic Python: pull the data the agent reasons over, return the
        user-message content. Default: a trivial online check (Sprint 1)."""
        return (
            f"Health check for {self.display_name}. In one sentence, confirm you are "
            "online and state your role. Do not do any other work."
        )

    def apply(self, conn, result: llm.LLMResult, context: str) -> str:
        """Parse the model output and persist to the agent's target tables.
        Default: no side effects; the model text becomes the run summary."""
        return result.text.strip()[:500]

    # ── the one lifecycle everything uses ────────────────────────────────────
    def run(self, conn, trigger: str = "manual", transport=None, params: dict | None = None) -> dict:
        self.params = params or {}
        prompt = conn.execute(
            "SELECT version, body FROM agent_prompts WHERE agent_id = ? AND active = 1 "
            "ORDER BY id DESC LIMIT 1",
            (self.id,),
        ).fetchone()
        prompt_version = prompt["version"] if prompt else None
        prompt_body = prompt["body"] if prompt else ""

        # Budget gate — skip (visibly) if today's spend already hit the cap.
        spent = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM agent_runs "
            "WHERE agent_id = ? AND date(started_at) = date('now') AND status != 'skipped_budget'",
            (self.id,),
        ).fetchone()[0]
        if self.daily_budget_usd and spent >= self.daily_budget_usd:
            cur = conn.execute(
                "INSERT INTO agent_runs (agent_id, finished_at, trigger, provider, model, "
                "status, output_summary, prompt_version) VALUES "
                "(?, datetime('now'), ?, ?, ?, 'skipped_budget', ?, ?)",
                (self.id, trigger, self.provider, self.model,
                 f"Skipped — daily budget ${self.daily_budget_usd:.2f} reached.", prompt_version),
            )
            conn.commit()
            return {"run_id": cur.lastrowid, "status": "skipped_budget",
                    "agent_id": self.id, "cost_usd": 0}

        cur = conn.execute(
            "INSERT INTO agent_runs (agent_id, trigger, provider, model, status, prompt_version) "
            "VALUES (?, ?, ?, ?, 'running', ?)",
            (self.id, trigger, self.provider, self.model, prompt_version),
        )
        run_id = cur.lastrowid
        conn.commit()

        try:
            context = self.build_context(conn)
            result = llm.complete(
                self.provider, self.model, prompt_body,
                [{"role": "user", "content": context}], transport=transport,
            )
            summary = self.apply(conn, result, context)
            conn.execute(
                "UPDATE agent_runs SET finished_at = datetime('now'), tokens_in = ?, "
                "tokens_out = ?, cost_usd = ?, status = 'success', output_summary = ? "
                "WHERE id = ?",
                (result.tokens_in, result.tokens_out, result.cost_usd, summary, run_id),
            )
            conn.commit()
            return {"run_id": run_id, "status": "success", "agent_id": self.id,
                    "cost_usd": result.cost_usd, "tokens_in": result.tokens_in,
                    "tokens_out": result.tokens_out, "summary": summary}
        except Exception as e:  # never let one agent crash the scheduler/request
            detail = e.message if isinstance(e, ApiError) else str(e)
            conn.execute(
                "UPDATE agent_runs SET finished_at = datetime('now'), status = 'error', "
                "error = ? WHERE id = ?",
                (detail[:500], run_id),
            )
            conn.commit()
            return {"run_id": run_id, "status": "error", "agent_id": self.id, "error": detail}
