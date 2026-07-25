"""products.py — expanded resale catalog CRUD."""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.schemas.products import ProductIn
from app.security import require_api_key
from app.services import products_service as svc

router = APIRouter(prefix="/api", tags=["products"])
guard = [Depends(require_api_key)]


@router.get("/products")
def list_products(category: str | None = None, search: str | None = None,
                  limit: int = 100, offset: int = 0, conn=Depends(get_conn)):
    return svc.list_products(conn, category, search, limit, offset)


@router.get("/products/{product_id}")
def get_product(product_id: int, conn=Depends(get_conn)):
    return svc.get_product(conn, product_id)


@router.post("/products", dependencies=guard)
def create_product(body: ProductIn, conn=Depends(get_conn)):
    return svc.create_product(conn, body.model_dump())


@router.put("/products/{product_id}", dependencies=guard)
def update_product(product_id: int, body: ProductIn, conn=Depends(get_conn)):
    return svc.update_product(conn, product_id, body.model_dump())


@router.delete("/products/{product_id}", dependencies=guard)
def delete_product(product_id: int, conn=Depends(get_conn)):
    svc.delete_product(conn, product_id)
    return {"deleted": product_id}
