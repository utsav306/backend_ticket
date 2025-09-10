from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Event, Booking
from app.schemas import EventCreate, EventUpdate
from datetime import datetime

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# POST /events - Create event
@router.post("/events")
def create_event(event_data: EventCreate, db: Session = Depends(get_db)):
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
    return event

# PUT /events/{id} - Update event
@router.put("/events/{event_id}")
def update_event(event_id: int, event_data: EventUpdate, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event_data.name is not None:
        event.name = event_data.name
    if event_data.venue is not None:
        event.venue = event_data.venue
    if event_data.time is not None:
        event.time = event_data.time
    if event_data.capacity is not None:
        event.capacity = event_data.capacity
    
    db.commit()
    db.refresh(event)
    return event

# GET /admin/analytics - Simple analytics
@router.get("/admin/analytics")
def analytics(db: Session = Depends(get_db)):
    total_bookings = db.query(Booking).count()
    popular_events = db.query(Event).order_by(Event.booked_count.desc()).limit(5).all()
    utilization = []
    for e in db.query(Event).all():
        util = (e.booked_count / e.capacity) * 100 if e.capacity else 0
        utilization.append({"event_id": e.id, "utilization_percent": util})
    return {"total_bookings": total_bookings, "popular_events": popular_events, "utilization": utilization}
