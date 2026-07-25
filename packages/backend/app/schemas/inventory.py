from pydantic import BaseModel, Field


class InventoryCreate(BaseModel):
    title: str = Field(min_length=1)
    product_id: int | None = None
    machine_model: str | None = None
    condition: str | None = None
    buy_price: float = Field(ge=0)
    buy_shipping: float = Field(default=0.0, ge=0)
    buy_date: str | None = None
    source_id: int | None = None
    notes: str | None = None


class InventoryUpdate(BaseModel):
    title: str | None = None
    product_id: int | None = None
    machine_model: str | None = None
    condition: str | None = None
    buy_price: float | None = Field(default=None, ge=0)
    buy_shipping: float | None = Field(default=None, ge=0)
    buy_date: str | None = None
    source_id: int | None = None
    status: str | None = None  # in_stock | listed | sold | scrapped
    sell_price: float | None = Field(default=None, ge=0)
    sell_fees: float | None = Field(default=None, ge=0)
    sell_shipping: float | None = Field(default=None, ge=0)
    sell_date: str | None = None
    sold_on: str | None = None
    notes: str | None = None
