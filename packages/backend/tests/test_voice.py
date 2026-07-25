"""Tier 2 — voice logging. No live network: the LLM transport is injected, so
the extraction is deterministic and item creation goes through the real
inventory_service."""

import json

import pytest

from app.errors import ApiError
from app.services import voice_service


def fake_llm(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)

    def t(provider, model, system, messages, max_tokens):
        return {"text": text, "tokens_in": 15, "tokens_out": 8}

    return t


def _voice_source_id(conn):
    return conn.execute("SELECT id FROM sources WHERE name = 'Voice Log'").fetchone()["id"]


def test_voice_log_parses_dell(conn):
    t = fake_llm([{"title": "Dell Optiplex 7080", "model": "OptiPlex 7080",
                   "quantity": 2, "acquisition_cost": 45.0}])
    res = voice_service.log_transcript(conn, "Dell Optiplex 7080, 45 bucks, two of them", transport=t)

    assert res["items_created"] == 2
    rows = conn.execute("SELECT * FROM inventory WHERE source_id = ?", (_voice_source_id(conn),)).fetchall()
    assert len(rows) == 2
    assert rows[0]["buy_price"] == 45.0
    assert rows[0]["machine_model"] == "OptiPlex 7080"  # matched a known machine profile


def test_voice_log_default_quantity(conn):
    res = voice_service.log_transcript(conn, "HP monitor 30",
                                       transport=fake_llm([{"title": "HP Monitor", "acquisition_cost": 30}]))
    assert res["items_created"] == 1


def test_voice_log_unknown_item(conn):
    res = voice_service.log_transcript(conn, "weird thing no idea 10",
                                       transport=fake_llm([{"title": "weird thing", "acquisition_cost": 10}]))
    assert res["items_created"] == 1
    assert res["items"][0]["title"] == "weird thing"


def test_voice_batch_logs_multiple(conn):
    t = fake_llm([{"title": "Assorted cables", "quantity": 1, "acquisition_cost": 5}])
    res = voice_service.log_batch(conn, ["cables 5", "   ", "more cables 5"], transport=t)
    assert res["processed"] == 2  # the blank entry is skipped
    assert res["items_created"] == 2


def test_voice_log_preserves_transcript(conn):
    voice_service.log_transcript(conn, "the raw spoken words",
                                 transport=fake_llm([{"title": "Thing", "acquisition_cost": 1}]))
    row = conn.execute("SELECT raw_transcript, items_created FROM voice_logs ORDER BY id DESC LIMIT 1").fetchone()
    assert row["raw_transcript"] == "the raw spoken words"
    assert row["items_created"] == 1


def test_voice_empty_transcript_rejected(conn):
    with pytest.raises(ApiError):
        voice_service.log_transcript(conn, "   ", transport=fake_llm([]))
