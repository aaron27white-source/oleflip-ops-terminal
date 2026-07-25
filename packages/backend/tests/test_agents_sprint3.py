"""Sprint 3 — strategic agents (Research Bot, Auditor) + prompt-activation gate."""

import json

from app.agents import runner
from app.agents.util import week_start


def fake_llm(text):
    def t(provider, model, system, messages, max_tokens):
        return {"text": text, "tokens_in": 30, "tokens_out": 15}
    return t


# ── Research Bot -> intel_board ──────────────────────────────────────────────
def test_research_bot_writes_intel(conn):
    intel = json.dumps([
        {"category": "price_drop", "subject": "DDR4 16GB", "signal": "down 15% this week",
         "action": "e-pricer: refresh DDR4", "confidence": "high"},
        {"category": "new_gen", "subject": "OptiPlex 7090", "signal": "last-gen 7080 dropping",
         "action": "e-scanner: hunt 7080", "confidence": "med"},
    ])
    res = runner.run_agent("research-bot", transport=fake_llm(intel), conn=conn)
    assert res["status"] == "success"
    rows = conn.execute("SELECT * FROM intel_board WHERE week_start = ?", (week_start(),)).fetchall()
    assert len(rows) == 2
    assert {r["category"] for r in rows} == {"price_drop", "new_gen"}


def test_research_bot_idempotent_within_week(conn):
    intel = json.dumps([{"category": "business", "subject": "s", "signal": "x"}])
    runner.run_agent("research-bot", transport=fake_llm(intel), conn=conn)
    runner.run_agent("research-bot", transport=fake_llm(intel), conn=conn)
    n = conn.execute("SELECT COUNT(*) FROM intel_board WHERE week_start = ? AND consumed = 0",
                     (week_start(),)).fetchone()[0]
    assert n == 1  # unconsumed signals replaced, not duplicated


# ── Auditor -> agent_scores + proposed (inactive) prompt ─────────────────────
def test_auditor_scores_and_proposes(conn):
    audit = json.dumps([
        {"agent_id": "e-scanner", "score": 8, "trend": "up", "notes": "good coverage",
         "proposed_prompt": "You are E-Scanner. " + ("Be sharper about bulk lots. " * 4)},
        {"agent_id": "auditor", "score": 10, "trend": "flat", "notes": "self — must be ignored"},
    ])
    res = runner.run_agent("auditor", transport=fake_llm(audit), conn=conn)
    assert res["status"] == "success"

    score = conn.execute("SELECT score, trend FROM agent_scores WHERE agent_id = 'e-scanner' "
                         "AND week_start = ?", (week_start(),)).fetchone()
    assert score["score"] == 8 and score["trend"] == "up"
    # auditor must not score itself
    assert conn.execute("SELECT COUNT(*) FROM agent_scores WHERE agent_id = 'auditor'"
                        ).fetchone()[0] == 0
    # a proposed prompt was inserted inactive
    prop = conn.execute("SELECT active, created_by FROM agent_prompts WHERE agent_id = 'e-scanner' "
                        "AND created_by = 'auditor'").fetchone()
    assert prop["active"] == 0


def test_auditor_score_upserts_same_week(conn):
    a1 = json.dumps([{"agent_id": "e-pricer", "score": 5, "trend": "flat", "notes": "n"}])
    a2 = json.dumps([{"agent_id": "e-pricer", "score": 7, "trend": "up", "notes": "better"}])
    runner.run_agent("auditor", transport=fake_llm(a1), conn=conn)
    runner.run_agent("auditor", transport=fake_llm(a2), conn=conn)
    rows = conn.execute("SELECT score FROM agent_scores WHERE agent_id = 'e-pricer'").fetchall()
    assert len(rows) == 1 and rows[0]["score"] == 7  # upsert, latest wins


# ── prompt activation gate ───────────────────────────────────────────────────
def test_pending_and_activate_prompt(client, conn):
    audit = json.dumps([{"agent_id": "marketing", "score": 6, "trend": "flat", "notes": "n",
                         "proposed_prompt": "You are Marketing. " + ("Sharper pricing psych. " * 4)}])
    runner.run_agent("auditor", transport=fake_llm(audit), conn=conn)

    pending = client.get("/api/agents/prompts/pending").json()
    assert pending["total"] == 1
    pid = pending["items"][0]["id"]
    assert pending["items"][0]["agent_id"] == "marketing"

    assert client.post(f"/api/agents/prompts/{pid}/activate").json() == {
        "activated": pid, "agent_id": "marketing"}

    # exactly one active prompt for marketing, and it's the activated one
    active = conn.execute("SELECT id FROM agent_prompts WHERE agent_id = 'marketing' AND active = 1"
                          ).fetchall()
    assert len(active) == 1 and active[0]["id"] == pid
    assert client.get("/api/agents/prompts/pending").json()["total"] == 0


def test_activate_missing_prompt_404(client):
    assert client.post("/api/agents/prompts/99999/activate").status_code == 404


def test_intel_endpoint_returns_research_output(client, conn):
    intel = json.dumps([{"category": "price_drop", "subject": "GPU glut", "signal": "prices soft"}])
    runner.run_agent("research-bot", transport=fake_llm(intel), conn=conn)
    r = client.get("/api/intel").json()
    assert r["total"] >= 1
    assert any(i["subject"] == "GPU glut" for i in r["items"])


def test_agent_detail_and_prompts_endpoints(client):
    detail = client.get("/api/agents/e-scanner").json()
    assert detail["agent"]["id"] == "e-scanner"
    assert "recent_runs" in detail
    prompts = client.get("/api/agents/e-scanner/prompts").json()
    assert prompts["total"] >= 1  # the seeded prompt
