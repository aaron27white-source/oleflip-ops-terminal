"""util.py — small helpers shared by agent impls."""

import json
import re
from datetime import date, timedelta


def week_start(d: date | None = None) -> str:
    """ISO date of the Monday of d's week (used to key weekly intel + scores)."""
    d = d or date.today()
    return (d - timedelta(days=d.weekday())).isoformat()


def extract_json(text: str):
    """Best-effort parse of a JSON array/object out of LLM text (tolerates ```json
    fences and surrounding prose). Returns the parsed value or None — never raises,
    so a malformed model response degrades gracefully instead of failing the run."""
    if not text:
        return None
    t = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if fence:
        t = fence.group(1).strip()
    try:
        return json.loads(t)
    except (ValueError, TypeError):
        pass
    m = re.search(r"(\[.*\]|\{.*\})", t, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except (ValueError, TypeError):
            return None
    return None
