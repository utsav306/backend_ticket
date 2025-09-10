from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Event, Booking, BookingStatus
from app.schemas import EventCreate

router = APIRouter(prefix="/events", tags=["events"])

@router.get("")
def list_events(db: Session = Depends(get_db)):
    """Get list of all events with availability info."""
    events = db.query(Event).all()
    
    events_data = []
    for event in events:
        active_bookings = db.query(Booking).filter(
            Booking.event_id == event.id,
            Booking.status == BookingStatus.BOOKED
        ).count()
        
        events_data.append({
            "id": event.id,
            "name": event.name,
            "venue": event.venue,
            "time": event.time.isoformat() if event.time else None,
            "capacity": event.capacity,
            "booked_count": active_bookings,
            "available_spots": event.capacity - active_bookings,
            "is_full": active_bookings >= event.capacity
        })
    
    return {"events": events_data}

@router.get("/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get details of a specific event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    active_bookings = db.query(Booking).filter(
        Booking.event_id == event.id,
        Booking.status == BookingStatus.BOOKED
    ).count()
    
    return {
        "id": event.id,
        "name": event.name,
        "venue": event.venue,
        "time": event.time.isoformat() if event.time else None,
        "capacity": event.capacity,
        "booked_count": active_bookings,
        "available_spots": event.capacity - active_bookings,
        "is_full": active_bookings >= event.capacity
    }

@router.post("/", response_model=dict)
def create_event_public(event_data: EventCreate, db: Session = Depends(get_db)):
    """Create a new event (public endpoint)."""
    event = Event(
        name=event_data.name,
        venue=event_data.venue,
        time=event_data.time,
        capacity=event_data.capacity,
        booked_count=0
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return {
        "id": event.id,
        "name": event.name,
        "venue": event.venue,
        "time": event.time.isoformat() if event.time else None,
        "capacity": event.capacity,
        "booked_count": 0
    }
