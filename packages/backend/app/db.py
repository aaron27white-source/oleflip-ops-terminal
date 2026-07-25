"""db.py — the seam between Phase 2 (this backend) and Phase 1 (it-parts-system).

Startup:
  1. put PHASE1_PATH on sys.path (no Phase 1 edits, flat-layout friendly)
  2. call Phase 1's bootstrap(db_path=...) to create/seed its tables in OUR
     persistent db file
  3. run Phase 2 migrations (run-once, ledgered) on the same file

Per request: get_conn() yields a fresh sqlite3 connection (WAL, FK on, Row
factory) and closes it after. Handlers are sync `def` so FastAPI runs them in
its threadpool, letting them call Phase 1's synchronous sqlite code directly.
"""

import sqlite3
import sys
from pathlib import Path

from app.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _ensure_phase1_on_path() -> None:
    p = settings.phase1_path
    if p and p not in sys.path:
        sys.path.insert(0, p)


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or settings.oleflip_db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _apply_migrations(conn: sqlite3.Connection) -> str:
    """Run any *.sql in migrations/ not yet recorded, in filename order.
    Each runs in its own transaction; a failure aborts startup loudly."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    conn.commit()
    applied = {r[0] for r in conn.execute("SELECT version FROM schema_migrations").fetchall()}
    files = sorted(MIGRATIONS_DIR.glob("*.sql"), key=lambda f: f.name)
    latest = None
    for f in files:
        version = f.name
        latest = version
        if version in applied:
            continue
        try:
            conn.executescript(f.read_text())
            conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise RuntimeError(f"Migration failed: {version}")
    return latest or "none"


def init_database() -> dict:
    """Called once at app startup. Returns a small status dict for /api/health."""
    _ensure_phase1_on_path()
    from db.connection import bootstrap  # Phase 1

    # Seed Phase 1 tables into our persistent file (idempotent).
    conn = bootstrap(db_path=settings.oleflip_db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.commit()
        migration_version = _apply_migrations(conn)
        # Seed the agent registry + default prompts (idempotent, after migrations).
        from app.agents.seed import seed_agents

        seed_agents(conn)
        parts = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
    finally:
        conn.close()
    return {"phase1_parts": parts, "migration_version": migration_version}


def get_conn():
    """FastAPI dependency — a connection per request, closed afterwards."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
