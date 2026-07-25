from pydantic import BaseModel, Field


class ReorderRequest(BaseModel):
    item_id: int
    photo_ids: list[int] = Field(min_length=1)
