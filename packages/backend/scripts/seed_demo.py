#!/usr/bin/env python3
"""seed_demo.py — populate a running backend with synthetic demo data so the UI
shows a realistic populated state (inventory, P&L, ITAD suppliers) with no real
business data. Idempotent-ish: intended for a fresh demo DB.

Usage (backend must be running):
    python scripts/seed_demo.py                 # default http://localhost:8000
    API_BASE=http://localhost:8000 python scripts/seed_demo.py
"""

import os
import sys
import urllib.request
import json

BASE = os.environ.get("API_BASE", "http://localhost:8000").rstrip("/")


def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:  # nosec B310 — local demo server
        return json.loads(r.read() or "{}")


ITAD_COMPANIES = [
    {"name": "Gulf Coast ITAD", "city": "Houston", "state": "TX", "phone": "555-0101",
     "status": "active", "reliability": 5, "sells_singles": True,
     "notes": "Reliable pallets of SFF desktops; good on singles."},
    {"name": "Piney Woods IT Assets", "city": "Tyler", "state": "TX", "phone": "555-0134",
     "status": "contacted", "reliability": 4, "notes": "East TX; monthly decommission lots."},
    {"name": "Razorback Recyclers", "city": "Little Rock", "state": "AR", "phone": "555-0177",
     "status": "active", "reliability": 4, "sells_singles": True,
     "notes": "Central AR; universities + county surplus."},
    {"name": "Bayou Data Recovery", "city": "Baton Rouge", "state": "LA", "phone": "555-0199",
     "status": "not-contacted", "reliability": 3, "notes": "North LA corridor; unverified."},
    {"name": "Ark-La-Tex Asset Mgmt", "city": "Shreveport", "state": "LA", "phone": "555-0143",
     "status": "contacted", "reliability": 4, "notes": "Covers the AR/LA/TX tri-state corridor."},
]

# (title, machine_model, buy_price, buy_shipping, [sell_price if sold])
INVENTORY = [
    ("OptiPlex 7080 SFF", "OptiPlex 7080", 55.0, 12.0, 148.0),
    ("EliteDesk 800 G6",  "EliteDesk 800 G6", 62.0, 14.0, 175.0),
    ("16GB DDR4 Desktop RAM x4", None, 22.0, 0.0, 96.0),
    ("Intel Core i7-10700", None, 40.0, 0.0, 118.0),
    ("512GB NVMe SSD x3", None, 45.0, 0.0, None),
    ("OptiPlex 7080 SFF (parts)", "OptiPlex 7080", 48.0, 12.0, None),
    ("256GB NVMe SSD x5", None, 55.0, 0.0, 92.0),
]


def main():
    try:
        _req("GET", "/api/health")
    except Exception as e:  # noqa: BLE001
        print(f"Backend not reachable at {BASE} ({e}). Start it first.", file=sys.stderr)
        return 1

    for c in ITAD_COMPANIES:
        try:
            _req("POST", "/api/itad/companies", c)
        except Exception as e:  # noqa: BLE001
            print(f"  itad '{c['name']}' skipped: {e}")
    print(f"seeded {len(ITAD_COMPANIES)} ITAD suppliers")

    sold = 0
    for title, model, buy, ship, *rest in INVENTORY:
        try:
            item = _req("POST", "/api/inventory", {
                "title": title, "machine_model": model,
                "buy_price": buy, "buy_shipping": ship,
            })
            sell = rest[0] if rest else None
            if sell:
                _req("PATCH", f"/api/inventory/{item['id']}",
                     {"status": "sold", "sell_price": sell})
                sold += 1
        except Exception as e:  # noqa: BLE001
            print(f"  inventory '{title}' skipped: {e}")
    print(f"seeded {len(INVENTORY)} inventory items ({sold} sold → populates P&L)")
    print("demo data ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
