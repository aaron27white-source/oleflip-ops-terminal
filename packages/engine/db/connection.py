"""connection.py — SQLite bootstrap for the open reference pricing engine.

Creates the schema on first run, loads synthetic seed data idempotently, and
hands back a ready sqlite3.Connection. The backend calls bootstrap(db_path=...)
against its own persistent DB file, then layers its Phase-2 migrations on top.

Swap this whole packages/engine/ package out (via PHASE1_PATH) to plug in a real
pricing/scanner engine — the backend only depends on the public function names
in db/, models/, calculator/, scanner/.
"""

import sqlite3
from pathlib import Path

_DB_DIR = Path(__file__).resolve().parent
_SCHEMA = _DB_DIR / "schema.sql"
_SEED_DATA = _DB_DIR / "seed_data.sql"
_SEED_PRICES = _DB_DIR / "seed_prices.sql"
_SEED_MACHINES = _DB_DIR / "seed_machines.sql"
_PART_QUERIES = _DB_DIR / "part_queries.sql"
_AUCTION_WATCHES = _DB_DIR / "auction_watches.sql"
_SEEN_LOTS = _DB_DIR / "seen_lots.sql"


def get_connection(db_path=None):
    """Open a sqlite3 connection with row access by column name."""
    path = db_path or (_DB_DIR.parent / "data" / "parts.db")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _script(conn, path):
    if path.exists():
        conn.executescript(path.read_text())
        conn.commit()


def load_seed_prices(conn):
    """Seed price_history only when empty — it has no natural unique key, so
    re-running would double rows on every bootstrap() call."""
    if not _SEED_PRICES.exists():
        return
    if conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0] == 0:
        conn.executescript(_SEED_PRICES.read_text())
        conn.commit()


def bootstrap(db_path=None):
    """Open a connection, create the schema if missing, load synthetic seeds."""
    conn = get_connection(db_path)
    _script(conn, _SCHEMA)
    _script(conn, _SEED_DATA)
    load_seed_prices(conn)
    _script(conn, _SEED_MACHINES)
    _script(conn, _PART_QUERIES)
    _script(conn, _AUCTION_WATCHES)
    _script(conn, _SEEN_LOTS)
    return conn


if __name__ == "__main__":
    c = bootstrap()
    n = c.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
    print(f"reference engine ready — {n} parts loaded")
    c.close()
