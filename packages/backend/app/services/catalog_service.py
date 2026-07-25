"""catalog_service.py — wraps Phase 1 parts/machines/prices + Phase 2 categories."""

from models.machine import fuzzy_match_machine, get_machine_profile, list_machines
from models.part import get_part, search_parts
from models.price import (
    get_current_price_summary,
    get_net_profit,
    sell_speed_label,
    update_price,
)

from app.errors import ApiError

# ── parts ────────────────────────────────────────────────────────────────────

def _part_with_price(conn, part: dict) -> dict:
    summary = get_current_price_summary(conn, part["id"])
    profit = get_net_profit(conn, part["id"])
    out = dict(part)
    out["price"] = summary  # None if no recent sales
    out["net_profit"] = profit["net_profit"] if profit else None
    out["sell_speed"] = sell_speed_label(summary["sample_count"] if summary else 0)
    return out


def list_parts(conn, search: str | None, category: str | None, limit: int = 200) -> dict:
    if search:
        parts = search_parts(conn, search)
    else:
        rows = conn.execute("SELECT * FROM parts ORDER BY category, name").fetchall()
        parts = [dict(r) for r in rows]
    if category:
        parts = [p for p in parts if (p.get("category") or "").lower() == category.lower()]
    parts = parts[:limit]
    return {"items": [_part_with_price(conn, p) for p in parts], "total": len(parts)}


def get_part_detail(conn, part_id: str) -> dict:
    part = get_part(conn, part_id)
    if not part:
        raise ApiError(404, "part_not_found", f"No part with id '{part_id}'.")
    return _part_with_price(conn, part)


def record_price(conn, part_id: str, price: float, source="manual", date=None,
                 condition="used", url=None) -> dict:
    if not get_part(conn, part_id):
        raise ApiError(404, "part_not_found", f"No part with id '{part_id}'.")
    update_price(conn, part_id, price, source, date, condition, url)
    return get_part_detail(conn, part_id)


# ── machines / profiles ──────────────────────────────────────────────────────

def list_machine_profiles(conn, search: str | None) -> dict:
    if search:
        models = fuzzy_match_machine(conn, search)
    else:
        models = list_machines(conn)
    return {"items": models, "total": len(models)}


def get_profile(conn, model: str) -> dict:
    profile = get_machine_profile(conn, model)
    if not profile:
        raise ApiError(404, "machine_not_found", f"No machine profile for '{model}'.")
    return profile


def upsert_profile(conn, data: dict, existing_model: str | None = None) -> dict:
    """Create or edit a machine profile + its parts list."""
    model = data["model"]
    fields = ("brand", "generation", "standard_ram", "standard_ssd", "standard_cpu",
              "standard_wifi", "standard_psu", "has_cooler", "estimated_total_value",
              "safe_max_bid", "notes")
    values = {f: data.get(f) for f in fields}
    if existing_model and existing_model != model:
        conn.execute("DELETE FROM machine_parts WHERE model = ?", (existing_model,))
        conn.execute("DELETE FROM machines WHERE model = ?", (existing_model,))
    conn.execute(
        "INSERT INTO machines (model, brand, generation, standard_ram, standard_ssd, "
        "standard_cpu, standard_wifi, standard_psu, has_cooler, estimated_total_value, "
        "safe_max_bid, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(model) DO UPDATE SET brand=excluded.brand, generation=excluded.generation, "
        "standard_ram=excluded.standard_ram, standard_ssd=excluded.standard_ssd, "
        "standard_cpu=excluded.standard_cpu, standard_wifi=excluded.standard_wifi, "
        "standard_psu=excluded.standard_psu, has_cooler=excluded.has_cooler, "
        "estimated_total_value=excluded.estimated_total_value, safe_max_bid=excluded.safe_max_bid, "
        "notes=excluded.notes",
        (model, values["brand"], values["generation"], values["standard_ram"], values["standard_ssd"],
         values["standard_cpu"], values["standard_wifi"], values["standard_psu"],
         1 if values["has_cooler"] else 0, values["estimated_total_value"],
         values["safe_max_bid"], values["notes"]),
    )
    conn.execute("DELETE FROM machine_parts WHERE model = ?", (model,))
    for part in data.get("parts", []):
        conn.execute(
            "INSERT INTO machine_parts (model, part_id, qty) VALUES (?,?,?)",
            (model, part["part_id"], part.get("qty", 1)),
        )
    conn.commit()
    return get_profile(conn, model)


def delete_profile(conn, model: str) -> None:
    if not get_machine_profile(conn, model):
        raise ApiError(404, "machine_not_found", f"No machine profile for '{model}'.")
    conn.execute("DELETE FROM machine_parts WHERE model = ?", (model,))
    conn.execute("DELETE FROM machines WHERE model = ?", (model,))
    conn.commit()


# ── categories ───────────────────────────────────────────────────────────────

def list_categories(conn) -> dict:
    rows = conn.execute("SELECT * FROM categories ORDER BY sort_order, name").fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def create_category(conn, name: str, icon=None, parent_id=None, sort_order=0) -> dict:
    cur = conn.execute(
        "INSERT INTO categories (name, icon, parent_id, sort_order) VALUES (?,?,?,?)",
        (name, icon, parent_id, sort_order),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM categories WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def delete_category(conn, cat_id: int) -> None:
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
