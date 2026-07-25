from pydantic import BaseModel, Field


class VoiceLogRequest(BaseModel):
    transcript: str = Field(min_length=1)


class VoiceBatchRequest(BaseModel):
    entries: list[str] = Field(min_length=1)
