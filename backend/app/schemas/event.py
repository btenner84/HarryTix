from datetime import datetime
from pydantic import BaseModel


class EventBase(BaseModel):
    name: str
    venue: str
    event_date: datetime
    stubhub_event_id: str | None = None
    seatgeek_event_id: str | None = None
    vividseats_event_id: str | None = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: str | None = None
    venue: str | None = None
    event_date: datetime | None = None
    stubhub_event_id: str | None = None
    seatgeek_event_id: str | None = None
    vividseats_event_id: str | None = None


class EventResponse(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
