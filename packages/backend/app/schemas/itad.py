from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["not-contacted", "contacted", "active", "dead"]


class CompanyIn(BaseModel):
    name: str = Field(min_length=1)
    phone: str | None = None
    address: str | None = None
    city: str = "Houston"
    state: str = "TX"
    website: str | None = None
    contact_person: str | None = None
    status: Status = "not-contacted"
    reliability: int = Field(default=3, ge=1, le=5)
    sells_singles: bool = False
    typical_bare_price: float | None = Field(default=None, ge=0)
    typical_loaded_price: float | None = Field(default=None, ge=0)
    notes: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    website: str | None = None
    contact_person: str | None = None
    status: Status | None = None
    reliability: int | None = Field(default=None, ge=1, le=5)
    sells_singles: bool | None = None
    typical_bare_price: float | None = Field(default=None, ge=0)
    typical_loaded_price: float | None = Field(default=None, ge=0)
    notes: str | None = None


class CallIn(BaseModel):
    call_date: str | None = None
    spoke_with: str | None = None
    notes: str = Field(min_length=1)
    has_inventory: bool = False
    pricing_text: str | None = None
    follow_up: str | None = None


class PurchaseIn(BaseModel):
    purchase_date: str | None = None
    model: str | None = None
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)
    total_cost: float | None = Field(default=None, ge=0)
    had_ram: bool = False
    had_storage: bool = False
    working_count: int | None = Field(default=None, ge=0)
    notes: str | None = None
