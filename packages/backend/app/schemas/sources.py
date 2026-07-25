from typing import Literal

from pydantic import BaseModel, Field

SourceType = Literal["govdeals", "fb", "itad", "flea", "university", "other"]
LeadKind = Literal["itad", "university", "fb_search", "govdeals_search", "other"]


class SourceIn(BaseModel):
    name: str = Field(min_length=1)
    type: SourceType = "other"
    reliability_score: int = Field(default=3, ge=1, le=5)
    notes: str | None = None


class SourceUpdate(BaseModel):
    name: str | None = None
    type: SourceType | None = None
    reliability_score: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class LeadIn(BaseModel):
    kind: LeadKind
    name: str = Field(min_length=1)
    contact: str | None = None
    location: str | None = None
    schedule_note: str | None = None
    last_contacted: str | None = None
    url: str | None = None
    notes: str | None = None
