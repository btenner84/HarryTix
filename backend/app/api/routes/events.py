from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate, EventResponse

router = APIRouter()


@router.get("/", response_model=list[EventResponse])
async def list_events(db: AsyncSession = Depends(get_db)):
    """List all tracked events"""
    result = await db.execute(select(Event).order_by(Event.event_date))
    events = result.scalars().all()
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific event by ID"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/", response_model=EventResponse)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    """Create a new event to track"""
    db_event = Event(**event.model_dump())
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, event: EventUpdate, db: AsyncSession = Depends(get_db)):
    """Update an event"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    db_event = result.scalar_one_or_none()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = event.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)

    await db.commit()
    await db.refresh(db_event)
    return db_event


@router.delete("/{event_id}")
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an event"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    db_event = result.scalar_one_or_none()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(db_event)
    await db.commit()
    return {"message": "Event deleted"}
