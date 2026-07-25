"""Sprint 4 — Marketing / E-Customer / E-Listings, on-demand params, cost projection."""

from app.agents import runner
from app.agents.definitions import AGENT_IDS
from app.agents.registry import AGENT_CLASSES


def fake_llm(text="ok."):
    def t(provider, model, system, messages, max_tokens):
        return {"text": text, "tokens_in": 10, "tokens_out": 5}
    return t


def test_all_eight_agents_have_impls():
    assert set(AGENT_IDS) == set(AGENT_CLASSES)
    assert len(AGENT_CLASSES) == 8


def test_marketing_runs(conn):
    part = conn.execute("SELECT id FROM parts LIMIT 1").fetchone()[0]
    conn.execute("INSERT INTO price_history (part_id, price, source, date) "
                 "VALUES (?, 50, 'test', date('now','-2 days'))", (part,))
    conn.commit()
    res = runner.run_agent("marketing", transport=fake_llm("Use .99 endings."), conn=conn)
    assert res["status"] == "success" and "Pricing tactics" in res["summary"]


def test_e_customer_with_message(conn):
    res = runner.run_agent("e-customer", transport=fake_llm("Sorry — full refund coming."),
                           conn=conn, params={"message": "item arrived broken"})
    assert res["status"] == "success" and res["summary"].startswith("Draft reply:")


def test_e_customer_without_message_is_graceful(conn):
    res = runner.run_agent("e-customer", transport=fake_llm("need the message"), conn=conn)
    assert res["status"] == "success" and "no message provided" in res["summary"]


def test_e_listings_from_specs(conn):
    res = runner.run_agent("e-listings", transport=fake_llm("Title: Dell 16GB DDR4..."),
                           conn=conn, params={"specs": "16GB DDR4 pull, tested"})
    assert res["status"] == "success" and res["summary"].startswith("Listing draft:")


def test_e_listings_from_inventory_item(conn):
    conn.execute("INSERT INTO inventory (title, buy_price, buy_date, status, condition) "
                 "VALUES ('HP 800 G4', 100, date('now'), 'listed', 'used pull')")
    inv_id = conn.execute("SELECT id FROM inventory ORDER BY id DESC LIMIT 1").fetchone()[0]
    conn.commit()
    res = runner.run_agent("e-listings", transport=fake_llm("Title: HP 800 G4 SFF..."),
                           conn=conn, params={"inventory_id": inv_id})
    assert res["status"] == "success" and res["summary"].startswith("Listing draft:")


def test_run_endpoint_passes_params(client, monkeypatch):
    monkeypatch.setattr("app.agents.llm._dispatch",
                        lambda *a: {"text": "Refund issued, apologies.", "tokens_in": 8, "tokens_out": 4})
    r = client.post("/api/agents/e-customer/run", json={"params": {"message": "where is my item"}})
    assert r.status_code == 200 and r.json()["status"] == "success"
    assert "Draft reply" in r.json()["summary"]


def test_costs_include_projection(client):
    assert "projected_month" in client.get("/api/agents/costs").json()
