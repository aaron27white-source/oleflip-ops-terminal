"""voice_service.py — Tier 2 voice logging.

Turn a spoken/typed transcript ("Dell Optiplex 7080, 45 bucks, two of them")
into inventory rows. The LLM does the extraction (reusing agents/llm.complete +
the injectable transport seam so tests never hit the network); item creation
reuses inventory_service.create_item — no duplicated inventory logic. Every call
is audited in voice_logs.
"""

import json

from app.agents import llm
from app.agents.util import extract_json
from app.config import settings
from app.errors import ApiError
from app.services import inventory_service

SYSTEM_PROMPT = (
    "You are a flea-market inventory assistant. Extract purchase details from spoken notes.\n"
    "The user is at an auction/flea market naming items they just bought.\n\n"
    "Rules:\n"
    "- Extract: title, estimated model (if identifiable), quantity, price PER UNIT.\n"
    "- Quantity defaults to 1 if not mentioned.\n"
    '- Price is per-unit. If they say "45 for 2" that is 22.50 each.\n'
    "- If the item is IT hardware (computer, server, monitor, switch, etc.), keep the model.\n"
    "- If price is unclear, set acquisition_cost to null.\n"
    'Return ONLY a JSON array of objects: '
    '{"title": str, "model": str|null, "quantity": int, "acquisition_cost": number|null, '
    '"condition": str|null, "notes": str|null}. No prose, no code fences.'
)


def _match_machine(conn, model: str | None) -> str | None:
    """Return a canonical machine model if the spoken model maps to a known
    profile, else the raw string (still useful as free-text machine_model)."""
    if not model:
        return None
    hit = conn.execute(
        "SELECT model FROM machines WHERE lower(model) = lower(?) LIMIT 1", (model.strip(),)
    ).fetchone()
    return hit["model"] if hit else model.strip()


def _voice_source_id(conn) -> int | None:
    row = conn.execute("SELECT id FROM sources WHERE name = 'Voice Log' LIMIT 1").fetchone()
    return row["id"] if row else None


def _coerce_items(parsed) -> list[dict]:
    """Accept either a bare array or a {"items": [...]} wrapper."""
    if isinstance(parsed, dict):
        parsed = parsed.get("items", [])
    return [it for it in parsed if isinstance(it, dict)] if isinstance(parsed, list) else []


def log_transcript(conn, transcript: str, transport=None) -> dict:
    """Parse one transcript, create inventory rows, and audit the run."""
    transcript = (transcript or "").strip()
    if not transcript:
        raise ApiError(422, "empty_transcript", "Nothing to log — the transcript was empty.")

    result = llm.complete(
        settings.voice_provider, settings.voice_model, SYSTEM_PROMPT,
        [{"role": "user", "content": transcript}], max_tokens=800, transport=transport,
    )
    items = _coerce_items(extract_json(result.text))
    source_id = _voice_source_id(conn)

    created: list[dict] = []
    for it in items:
        title = str(it.get("title") or "").strip()
        if not title:
            continue
        qty = it.get("quantity") or 1
        try:
            qty = max(1, min(int(qty), 50))  # clamp a bad parse to a sane range
        except (TypeError, ValueError):
            qty = 1
        cost = it.get("acquisition_cost")
        try:
            cost = round(float(cost), 2) if cost is not None else 0.0
        except (TypeError, ValueError):
            cost = 0.0
        row = {
            "title": title,
            "machine_model": _match_machine(conn, it.get("model")),
            "condition": (str(it.get("condition")).strip() if it.get("condition") else None),
            "buy_price": cost,
            "buy_shipping": 0,
            "source_id": source_id,
            "notes": f"Voice log: “{transcript}”",
        }
        for _ in range(qty):
            created.append(inventory_service.create_item(conn, row))

    conn.execute(
        "INSERT INTO voice_logs (raw_transcript, parsed_json, items_created, provider, model, "
        "tokens_in, tokens_out, cost_usd) VALUES (?,?,?,?,?,?,?,?)",
        (transcript, json.dumps(items), len(created), result.provider, result.model,
         result.tokens_in, result.tokens_out, result.cost_usd),
    )
    conn.commit()

    return {
        "transcript": transcript,
        "items": created,
        "items_created": len(created),
        "cost_usd": result.cost_usd,
    }


def log_batch(conn, entries: list[str], transport=None) -> dict:
    """Process several transcript entries; skips empties, aggregates results."""
    all_created: list[dict] = []
    processed = 0
    for entry in entries:
        if not (entry or "").strip():
            continue
        processed += 1
        res = log_transcript(conn, entry, transport=transport)
        all_created.extend(res["items"])
    return {"processed": processed, "items": all_created, "items_created": len(all_created)}
