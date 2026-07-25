"""Pydantic request models for the bid calculator endpoints."""

from pydantic import BaseModel, Field


class BidRequest(BaseModel):
    machine: str = Field(min_length=1)
    price: float = Field(ge=0)
    shipping: float = Field(default=0.0, ge=0)
    specs: str | None = None


class WhatIfRequest(BaseModel):
    machine: str = Field(min_length=1)
    buy_price: float = Field(ge=0)
    sell_discount: float = Field(default=0.0, ge=0, le=100)
    shipping_override: float | None = Field(default=None, ge=0)


class ScrapRequest(BaseModel):
    count: int = Field(ge=1)
    price: float = Field(ge=0)
    shipping: float = Field(default=0.0, ge=0)
    expected_working_pct: float = Field(default=40.0, ge=0, le=100)
    value_per_working: float = Field(default=40.0, ge=0)


class Lot(BaseModel):
    name: str
    price: float = Field(ge=0)
    shipping: float = Field(default=0.0, ge=0)


class CompareRequest(BaseModel):
    lots: list[Lot] = Field(min_length=1)
