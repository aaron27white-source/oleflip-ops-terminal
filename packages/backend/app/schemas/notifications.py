from pydantic import BaseModel, Field


class PrefUpdate(BaseModel):
    event_type: str
    channel: str
    enabled: bool | None = None
    min_headroom: float | None = None
    throttle_hours: int | None = Field(default=None, ge=0)


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushRegister(BaseModel):
    endpoint: str = Field(min_length=1)
    keys: PushKeys
    user_agent: str | None = None


class TestRequest(BaseModel):
    channels: list[str] = Field(default_factory=lambda: ["discord", "push"])
