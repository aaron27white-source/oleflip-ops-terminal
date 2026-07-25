"""Sprint 2 — operational agents. No live network: LLM transport is injected and
E-Scanner's deterministic scan step is monkeypatched to a no-op."""

import json

import pytest

from app.agents import runner


def fake_llm(text):
    def t(provider, model, system, messages, max_tokens):
        return {"text": text, "tokens_in": 20, "tokens_out": 10}
    return t


@pytest.fixture(autouse=True)
def _no_live_scan(monkeypatch):
    # E-Scanner runs a real GovDeals scan in prod; stub it out in tests.
    monkeypatch.setattr("app.services.scanner_service.run_scan",
                        lambda *a, **k: {"lots": [], "scanned": 0})


# ── E-Inventory: deterministic mode + kpi snapshot ───────────────────────────
def test_e_inventory_conservative_when_full(conn):
    conn.execute("INSERT INTO inventory (title, buy_price, buy_date, status) "
                 "VALUES ('big lot', 1700, date('now','-70 days'), 'listed')")
    conn.commit()
    res = runner.run_agent("e-inventory", transport=fake_llm("Mark down big lot."), conn=conn)
    assert res["status"] == "success"
    kpi = conn.execute("SELECT * FROM inventory_kpis ORDER BY id DESC LIMIT 1").fetchone()
    assert kpi["mode"] == "conservative"
    assert kpi["signal_pct"] == 85.0
    assert kpi["inventory_value"] == 1700
    assert "conservative" in res["summary"]


def test_e_inventory_aggressive_when_low(conn):
    conn.execute("INSERT INTO inventory (title, buy_price, buy_date, status) "
                 "VALUES ('small', 100, date('now','-5 days'), 'listed')")
    conn.commit()
    runner.run_agent("e-inventory", transport=fake_llm("ok"), conn=conn)
    assert conn.execute("SELECT mode FROM inventory_kpis ORDER BY id DESC LIMIT 1"
                        ).fetchone()[0] == "aggressive"


def test_e_inventory_kpi_upserts_same_day(conn):
    runner.run_agent("e-inventory", transport=fake_llm("a"), conn=conn)
    runner.run_agent("e-inventory", transport=fake_llm("b"), conn=conn)
    assert conn.execute("SELECT COUNT(*) FROM inventory_kpis WHERE snapshot_date = date('now')"
                        ).fetchone()[0] == 1


# ── E-Scanner: verdicts onto flagged_deals + intel consumed ──────────────────
def test_e_scanner_writes_verdicts_and_consumes_intel(conn):
    conn.execute("INSERT INTO inventory_kpis (snapshot_date, inventory_value, max_desired_value, "
                 "signal_pct, mode) VALUES (date('now'), 50, 2000, 2.5, 'aggressive')")
    conn.execute("INSERT INTO flagged_deals (source, lot_key, title, matched_model, margin_good, "
                 "dismissed, quantity) VALUES ('govdeals','LOT1','Dell lot','OptiPlex 7080',1,0,5)")
    conn.execute("INSERT INTO intel_board (category, subject, signal, week_start, consumed) "
                 "VALUES ('price_drop','DDR4','falling',date('now'),0)")
    conn.commit()

    verdicts = json.dumps([{"lot_key": "LOT1", "verdict": "BUY", "note": "strong margin"}])
    res = runner.run_agent("e-scanner", transport=fake_llm(verdicts), conn=conn)
    assert res["status"] == "success"

    d = conn.execute("SELECT agent_verdict, agent_note FROM flagged_deals WHERE lot_key='LOT1'"
                     ).fetchone()
    assert d["agent_verdict"] == "BUY" and "margin" in d["agent_note"]
    assert conn.execute("SELECT consumed FROM intel_board WHERE subject='DDR4'").fetchone()[0] == 1
    assert "aggressive" in res["summary"]


def test_e_scanner_survives_bad_json(conn):
    conn.execute("INSERT INTO flagged_deals (source, lot_key, title, dismissed) "
                 "VALUES ('govdeals','LOT2','x',0)")
    conn.commit()
    res = runner.run_agent("e-scanner", transport=fake_llm("not json at all"), conn=conn)
    assert res["status"] == "success"  # graceful — no verdict written, no crash
    assert conn.execute("SELECT agent_verdict FROM flagged_deals WHERE lot_key='LOT2'"
                        ).fetchone()[0] is None


# ── E-Pricer: 30d vs 90d divergence from price_history ───────────────────────
def test_e_pricer_flags_movers(conn):
    part = conn.execute("SELECT id FROM parts LIMIT 1").fetchone()[0]
    conn.execute("DELETE FROM price_history WHERE part_id = ?", (part,))  # isolate from seeded prices
    for d, price in [(-70, 100), (-65, 100), (-60, 100), (-5, 130), (-3, 130), (-1, 130)]:
        conn.execute("INSERT INTO price_history (part_id, price, source, date) "
                     "VALUES (?, ?, 'test', date('now', ?))", (part, price, f"{d} days"))
    conn.commit()
    res = runner.run_agent("e-pricer", transport=fake_llm("Buy — trending up."), conn=conn)
    assert res["status"] == "success"
    assert res["summary"].startswith("1 mover")


# ── chain: E-Inventory sets the mode E-Scanner then reads ────────────────────
def test_inventory_to_scanner_mode_chain(conn):
    conn.execute("INSERT INTO inventory (title, buy_price, buy_date, status) "
                 "VALUES ('full', 1900, date('now'), 'listed')")
    conn.execute("INSERT INTO flagged_deals (source, lot_key, title, dismissed) "
                 "VALUES ('govdeals','LOT3','y',0)")
    conn.commit()
    runner.run_agent("e-inventory", transport=fake_llm("full"), conn=conn)  # -> conservative
    res = runner.run_agent("e-scanner",
                           transport=fake_llm('[{"lot_key":"LOT3","verdict":"PASS","note":"tight"}]'),
                           conn=conn)
    assert "conservative" in res["summary"]
    assert conn.execute("SELECT agent_verdict FROM flagged_deals WHERE lot_key='LOT3'"
                        ).fetchone()[0] == "PASS"
