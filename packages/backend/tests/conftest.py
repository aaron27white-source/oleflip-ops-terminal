"""Shared fixtures. Each test gets an isolated temp DB (Phase 1 seeds + Phase 2
migrations), so nothing touches the real oleflip.db."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import get_connection, init_database
from app.main import app


@pytest.fixture(autouse=True)
def _no_scheduler(monkeypatch):
    # Keep the APScheduler background loop out of the test process.
    monkeypatch.setattr(settings, "agents_scheduler_enabled", False)


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    dbfile = tmp_path / "test.db"
    monkeypatch.setattr(settings, "oleflip_db_path", str(dbfile))
    return str(dbfile)


@pytest.fixture
def client(temp_db):
    # TestClient context manager runs the lifespan → init_database against temp_db.
    with TestClient(app) as c:
        yield c


@pytest.fixture
def conn(temp_db):
    init_database()
    c = get_connection(temp_db)
    yield c
    c.close()
