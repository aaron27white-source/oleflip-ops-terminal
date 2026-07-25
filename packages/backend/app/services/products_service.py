"""products_service.py — the expanded resale catalog (phones, monitors, …).

specs_json / condition_tiers are stored as JSON text; parsed to real
structures on the way out so the API returns clean objects.
"""

import json

from app.errors import ApiError


def _row_to_product(row) -> dict:
    p = dict(row)
    for field in ("specs_json", "condition_tiers"):
        raw = p.pop(field)
        key = "specs" if field == "specs_json" else "condition_tiers"
        try:
            p[key] = json.loads(raw) if raw else None
        except (json.JSONDecodeError, TypeError):
            p[key] = raw
    return p


def list_products(conn, category: str | None, search: str | None,
                  limit: int = 100, offset: int = 0) -> dict:
    where, params = [], []
    if category:
        where.append("(c.name = ? OR c.id = ?)")
        params.extend([category, category if category.isdigit() else -1])
    if search:
        where.append("(p.brand LIKE ? OR p.model LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM products p JOIN categories c ON c.id = p.category_id {clause}",
        params,
    ).fetchone()[0]
    rows = conn.execute(
        f"SELECT p.*, c.name AS category_name FROM products p "
        f"JOIN categories c ON c.id = p.category_id {clause} "
        f"ORDER BY c.sort_order, p.brand, p.model LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()
    return {"items": [_row_to_product(r) for r in rows], "total": total}


def get_product(conn, product_id: int) -> dict:
    row = conn.execute(
        "SELECT p.*, c.name AS category_name FROM products p "
        "JOIN categories c ON c.id = p.category_id WHERE p.id = ?",
        (product_id,),
    ).fetchone()
    if not row:
        raise ApiError(404, "product_not_found", f"No product with id {product_id}.")
    return _row_to_product(row)


def create_product(conn, data: dict) -> dict:
    specs = json.dumps(data.get("specs")) if data.get("specs") is not None else None
    tiers = json.dumps(data.get("condition_tiers")) if data.get("condition_tiers") is not None else None
    cur = conn.execute(
        "INSERT INTO products (category_id, brand, model, specs_json, condition_tiers, "
        "est_low, est_high, notes) VALUES (?,?,?,?,?,?,?,?)",
        (data["category_id"], data.get("brand"), data["model"], specs, tiers,
         data.get("est_low"), data.get("est_high"), data.get("notes")),
    )
    conn.commit()
    return get_product(conn, cur.lastrowid)


def update_product(conn, product_id: int, data: dict) -> dict:
    get_product(conn, product_id)  # 404 if missing
    specs = json.dumps(data.get("specs")) if data.get("specs") is not None else None
    tiers = json.dumps(data.get("condition_tiers")) if data.get("condition_tiers") is not None else None
    conn.execute(
        "UPDATE products SET category_id=?, brand=?, model=?, specs_json=?, condition_tiers=?, "
        "est_low=?, est_high=?, notes=? WHERE id=?",
        (data["category_id"], data.get("brand"), data["model"], specs, tiers,
         data.get("est_low"), data.get("est_high"), data.get("notes"), product_id),
    )
    conn.commit()
    return get_product(conn, product_id)


def delete_product(conn, product_id: int) -> None:
    get_product(conn, product_id)
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
