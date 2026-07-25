from typing import Literal

from pydantic import BaseModel, Field


class RefreshCompsRequest(BaseModel):
    part: str | None = None          # keyword/id; None with all=False is rejected
    all: bool = False
    source: Literal["rapidapi", "api", "scrape"] = "rapidapi"
    dry_run: bool = False
    limit: int = Field(default=25, ge=1, le=100)


class PriceRecord(BaseModel):
    price: float = Field(ge=0)
    source: str = "manual"
    date: str | None = None
    condition: str = "used"
    url: str | None = None


class MachinePart(BaseModel):
    part_id: str
    qty: int = Field(default=1, ge=1)


class MachineProfileIn(BaseModel):
    model: str = Field(min_length=1)
    brand: str = "Unknown"
    generation: str | None = None
    standard_ram: str | None = None
    standard_ssd: str | None = None
    standard_cpu: str | None = None
    standard_wifi: str | None = None
    standard_psu: str | None = None
    has_cooler: bool = True
    estimated_total_value: float | None = None
    safe_max_bid: float | None = None
    notes: str | None = None
    parts: list[MachinePart] = Field(default_factory=list)


class CategoryIn(BaseModel):
    name: str = Field(min_length=1)
    icon: str | None = None
    parent_id: int | None = None
    sort_order: int = 0
