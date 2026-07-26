"""geocode.py — turn a supplier address into (latitude, longitude).

Uses OpenStreetMap's Nominatim (no API key, free). Nominatim's usage policy asks
for a descriptive User-Agent and <=1 request/second, so callers geocoding many
rows should space requests out. `transport` is injectable so tests run offline.
Any failure returns None — geocoding is best-effort and never fatal.
"""

from urllib.parse import urlencode

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "oleflip-ops-terminal/1.0 (ITAD supplier CRM)"
REQUEST_TIMEOUT = 10


def build_query(address: str | None, city: str | None, state: str | None) -> str:
    """A single-line query from whatever location fields are present."""
    return ", ".join(p for p in (address, city, state) if p)


def _default_transport(url: str) -> list:
    import requests

    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def geocode(query: str, *, transport=None) -> tuple[float, float] | None:
    """Resolve a location string to (lat, lng), or None if unresolvable.
    Never raises — network/parse errors yield None."""
    query = (query or "").strip()
    if not query:
        return None
    url = f"{NOMINATIM_URL}?{urlencode({'q': query, 'format': 'json', 'limit': 1})}"
    try:
        results = (transport or _default_transport)(url)
        if not results:
            return None
        lat = float(results[0]["lat"])
        lng = float(results[0]["lon"])
        return lat, lng
    except Exception:  # noqa: BLE001 — geocoding is best-effort
        return None
