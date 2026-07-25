from typing import Any

from pydantic import BaseModel, Field


class ProductIn(BaseModel):
    category_id: int
    brand: str | None = None
    model: str = Field(min_length=1)
    specs: dict[str, Any] | None = None
    condition_tiers: list[str] | None = None
    est_low: float | None = Field(default=None, ge=0)
    est_high: float | None = Field(default=None, ge=0)
    notes: str | None = None
