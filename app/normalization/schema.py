from datetime import datetime

from pydantic import BaseModel


class EventPayload(BaseModel):
    external_id: str
    source: str
    title: str
    description: str | None = None
    category: str
    location_name: str
    latitude: float
    longitude: float
    starts_at: datetime
    source_url: str | None = None
