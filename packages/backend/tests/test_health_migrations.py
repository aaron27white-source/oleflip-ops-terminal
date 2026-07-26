"""M0 + M1 — Phase 1 import wired up, all tables/views exist, migrations idempotent."""

from app.db import init_database


def test_health_reports_phase1_and_migrations(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db_ok"] is True
    assert body["phase1_ok"] is True
    assert body["phase1_parts"] == 12  # bundled reference engine seeds 12 parts
    assert body["migration_version"] == "021_itad_geo.sql"


def test_all_phase1_and_phase2_tables_exist(conn):
    names = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
        ).fetchall()
    }
    # Phase 1
    for t in ("parts", "price_history", "current_prices", "net_profit", "machines",
              "machine_parts", "part_queries", "auction_watches", "seen_lots"):
        assert t in names, f"missing Phase 1 object {t}"
    # Phase 2
    for t in ("categories", "products", "sources", "inventory", "inventory_pnl",
              "flagged_deals", "leads", "schema_migrations",
              "itad_companies", "itad_call_logs", "itad_purchases", "itad_company_summary"):
        assert t in names, f"missing Phase 2 object {t}"


def test_migrations_are_idempotent(temp_db):
    # init twice on the same file — seed counts must not double.
    init_database()
    from app.db import get_connection
    c = get_connection(temp_db)
    cats1 = c.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    srcs1 = c.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    c.close()
    init_database()
    c = get_connection(temp_db)
    cats2 = c.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    srcs2 = c.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    applied = c.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    c.close()
    assert cats1 == cats2 == 8
    assert srcs1 == srcs2 == 6  # +1: the Voice Log source (017)
    assert applied == 21  # twenty-one migration files, each recorded once


def test_seed_categories_and_sources_present(conn):
    cats = {r["name"] for r in conn.execute("SELECT name FROM categories")}
    assert {"Phones", "Flip Phones", "Monitors", "Tablets", "Laptops", "Peripherals"} <= cats
    srcs = {r["name"] for r in conn.execute("SELECT name FROM sources")}
    assert "GovDeals" in srcs and "Flea Market" in srcs
