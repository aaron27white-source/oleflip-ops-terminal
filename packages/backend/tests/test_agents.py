"""Sprint 1 — agent foundation. No test hits a live network: the LLM transport is
injected (runner-level) or _dispatch is monkeypatched (API-level)."""

from app.agents import runner
from app.agents.pricing import cost_for


def _fake_transport(text="online.", tin=10, tout=5):
    def t(provider, model, system, messages, max_tokens):
        return {"text": text, "tokens_in": tin, "tokens_out": tout}
    return t


# ── seed + schema ────────────────────────────────────────────────────────────
def test_seed_creates_8_agents_each_with_active_prompt(conn):
    ids = [r["id"] for r in conn.execute("SELECT id FROM agents ORDER BY id")]
    assert len(ids) == 8
    assert {"e-scanner", "e-pricer", "auditor"} <= set(ids)
    for aid in ids:
        n = conn.execute(
            "SELECT COUNT(*) FROM agent_prompts WHERE agent_id = ? AND active = 1", (aid,)
        ).fetchone()[0]
        assert n == 1, f"{aid} should have exactly one active prompt"


def test_agent_tables_exist(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ("agents", "agent_runs", "agent_prompts", "agent_scores",
              "intel_board", "inventory_kpis"):
        assert t in names, f"missing {t}"


def test_seed_is_idempotent(conn):
    from app.agents.seed import seed_agents
    seed_agents(conn)
    seed_agents(conn)
    assert conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0] == 8
    assert conn.execute("SELECT COUNT(*) FROM agent_prompts").fetchone()[0] == 8


# ── run pipeline (fake transport) ────────────────────────────────────────────
def test_run_agent_end_to_end(conn):
    res = runner.run_agent("e-scanner", trigger="manual",
                           transport=_fake_transport("I am online", 100, 20), conn=conn)
    assert res["status"] == "success"
    row = conn.execute("SELECT * FROM agent_runs WHERE id = ?", (res["run_id"],)).fetchone()
    assert row["status"] == "success"
    assert row["tokens_in"] == 100 and row["tokens_out"] == 20
    assert row["cost_usd"] == cost_for(row["model"], 100, 20) > 0
    assert row["output_summary"] and row["prompt_version"]
    assert row["finished_at"] is not None


def test_run_records_error_on_transport_failure(conn):
    def boom(*a):
        raise RuntimeError("kaboom")
    res = runner.run_agent("e-pricer", transport=boom, conn=conn)
    assert res["status"] == "error"
    row = conn.execute("SELECT status, error FROM agent_runs WHERE id = ?",
                       (res["run_id"],)).fetchone()
    assert row["status"] == "error" and "kaboom" in row["error"]


def test_budget_skip(conn):
    conn.execute("UPDATE agents SET daily_budget_usd = 0.01 WHERE id = 'auditor'")
    conn.execute("INSERT INTO agent_runs (agent_id, status, cost_usd) "
                 "VALUES ('auditor', 'success', 0.02)")
    conn.commit()
    res = runner.run_agent("auditor", transport=_fake_transport(), conn=conn)
    assert res["status"] == "skipped_budget"
    assert conn.execute("SELECT status FROM agent_runs WHERE id = ?",
                        (res["run_id"],)).fetchone()[0] == "skipped_budget"


def test_cost_for_math():
    assert cost_for("claude-opus-4-8", 1_000_000, 0) == 5.00
    assert cost_for("claude-opus-4-8", 0, 1_000_000) == 25.00
    assert cost_for("unknown-model", 1000, 1000) == 0.0


# ── API surface ──────────────────────────────────────────────────────────────
def test_list_agents_endpoint(client):
    body = client.get("/api/agents").json()
    assert body["total"] == 8
    a = next(x for x in body["items"] if x["id"] == "e-scanner")
    assert "cost_today" in a and "runs_today" in a and "last_status" in a


def test_run_endpoint_logs_a_real_run(client, monkeypatch):
    monkeypatch.setattr("app.agents.llm._dispatch",
                        lambda *a: {"text": "ok", "tokens_in": 12, "tokens_out": 3})
    r = client.post("/api/agents/e-scanner/run")
    assert r.status_code == 200 and r.json()["status"] == "success"
    assert r.json()["tokens_in"] == 12
    runs = client.get("/api/agents/runs?agent_id=e-scanner").json()
    assert runs["total"] >= 1


def test_run_unknown_agent_404(client):
    assert client.post("/api/agents/nope/run").status_code == 404


def test_detail_costs_scores_health(client, monkeypatch):
    monkeypatch.setattr("app.agents.llm._dispatch",
                        lambda *a: {"text": "ok", "tokens_in": 100, "tokens_out": 50})
    client.post("/api/agents/e-pricer/run")

    detail = client.get("/api/agents/e-pricer").json()
    assert detail["agent"]["id"] == "e-pricer"
    assert detail["active_prompt"]["version"]

    costs = client.get("/api/agents/costs").json()
    assert "by_agent" in costs and "by_day" in costs and "month_total" in costs

    assert client.get("/api/agents/scores").json()["items"] == []

    agents = client.get("/api/health").json()["agents"]
    assert set(agents["providers"]) == {"anthropic", "deepseek", "openai", "grok"}
    assert "scheduler" in agents


def test_patch_agent(client):
    r = client.patch("/api/agents/marketing", json={"enabled": False, "daily_budget_usd": 0.99})
    assert r.status_code == 200
    a = r.json()["agent"]
    assert a["enabled"] == 0 and a["daily_budget_usd"] == 0.99
