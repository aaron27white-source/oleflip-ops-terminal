"""Tier 1 gap-fill — the E-Inventory agent persists structured suggestions for
aging stock, and the /inventory/suggestions endpoints read/act on them."""

from app.agents import runner


def fake_llm(text):
    def t(provider, model, system, messages, max_tokens):
        return {"text": text, "tokens_in": 20, "tokens_out": 10}

    return t


def test_e_inventory_writes_suggestion_for_stale_item(conn):
    conn.execute(
        "INSERT INTO inventory (title, buy_price, buy_date, status) "
        "VALUES ('Dell R730 server', 300, date('now','-70 days'), 'in_stock')"
    )
    conn.commit()
    res = runner.run_agent("e-inventory", transport=fake_llm("Mark it down."), conn=conn)
    assert res["status"] == "success"

    rows = conn.execute("SELECT * FROM inventory_suggestions").fetchall()
    assert len(rows) == 1
    assert rows[0]["days_held"] >= 60
    assert rows[0]["suggested_platform"] == "ebay"  # 'server' → ebay heuristic
    assert rows[0]["applied"] == 0


def test_no_suggestion_for_fresh_item(conn):
    conn.execute(
        "INSERT INTO inventory (title, buy_price, buy_date, status) "
        "VALUES ('fresh find', 50, date('now','-5 days'), 'in_stock')"
    )
    conn.commit()
    runner.run_agent("e-inventory", transport=fake_llm("ok"), conn=conn)
    assert conn.execute("SELECT COUNT(*) FROM inventory_suggestions").fetchone()[0] == 0


def test_suggestions_rewritten_idempotently(conn):
    conn.execute(
        "INSERT INTO inventory (title, buy_price, buy_date, status) "
        "VALUES ('old lot', 100, date('now','-90 days'), 'listed')"
    )
    conn.commit()
    runner.run_agent("e-inventory", transport=fake_llm("a"), conn=conn)
    runner.run_agent("e-inventory", transport=fake_llm("b"), conn=conn)
    # second run clears the un-applied set and rewrites — no duplicate.
    assert conn.execute("SELECT COUNT(*) FROM inventory_suggestions").fetchone()[0] == 1


def test_suggestions_endpoint_lists_and_applies(client, conn):
    conn.execute(
        "INSERT INTO inventory (id, title, buy_price, buy_date, status) "
        "VALUES (777, 'old server', 200, date('now','-90 days'), 'in_stock')"
    )
    conn.execute(
        "INSERT INTO inventory_suggestions (inventory_id, suggested_platform, reasoning, days_held) "
        "VALUES (777, 'ebay', 'held 90d', 90)"
    )
    conn.commit()

    body = client.get("/api/inventory/suggestions").json()
    assert body["total"] == 1
    sug = body["items"][0]
    assert sug["title"] == "old server"

    assert client.patch(f"/api/inventory/suggestions/{sug['id']}").status_code == 200
    assert client.get("/api/inventory/suggestions").json()["total"] == 0
