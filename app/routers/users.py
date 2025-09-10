from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Event, Booking, BookingStatus, UserRole
from app.schemas import BookingRequest, UserCreate
from app.cache.cache_utils import (
    get_cache, set_cache, 
    make_events_cache_key, make_user_bookings_cache_key,
    invalidate_event_caches, invalidate_user_booking_cache
)
from datetime import datetime

router = APIRouter(prefix="/users", tags=["users"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to check admin role
def check_admin(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# POST / - Create user
@router.post("/")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Convert string role to enum
    role = UserRole.ADMIN if user_data.role == "admin" else UserRole.USER
    
    user = User(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,  # In production, hash this!
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# GET / - List all users (Admin only for demo, could be public)
@router.get("/")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

# GET /events - Browse all events
@router.get("/events")
def get_events(db: Session = Depends(get_db)):
    # Check cache first
    cache_key = make_events_cache_key()
    cached_events = get_cache(cache_key)
    
    if cached_events is not None:
        return cached_events
    
    # If not in cache, get from database
    events = db.query(Event).all()
    
    # Convert to dict for JSON serialization
    events_data = [
        {
            "id": event.id,
            "name": event.name,
            "venue": event.venue,
            "time": event.time.isoformat() if event.time else None,
            "capacity": event.capacity,
            "booked_count": event.booked_count,
            "available_spots": event.capacity - event.booked_count
        }
        for event in events
    ]
    
    # Cache for 5 minutes
    set_cache(cache_key, events_data, ttl=300)
    
    return events_data

# POST /events/{id}/book - Book a ticket
@router.post("/events/{event_id}/book")
def book_ticket(event_id: int, booking_request: BookingRequest, db: Session = Depends(get_db)):
    # Lock event row
    event = db.query(Event).filter(Event.id == event_id).with_for_update().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.booked_count >= event.capacity:
        raise HTTPException(status_code=400, detail="Event fully booked")
    
    # Create booking
    booking = Booking(user_id=booking_request.user_id, event_id=event_id, status=BookingStatus.BOOKED)
    db.add(booking)
    event.booked_count += 1
    db.commit()
    db.refresh(booking)
    
    # Invalidate caches after booking
    invalidate_event_caches(event_id)
    invalidate_user_booking_cache(booking_request.user_id)
    
    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "event_id": booking.event_id,
        "status": booking.status.value,
        "created_at": booking.created_at.isoformat() if hasattr(booking, 'created_at') else None
    }

# POST /bookings/{id}/cancel - Cancel a ticket
@router.post("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == BookingStatus.cancelled:
        raise HTTPException(status_code=400, detail="Already cancelled")
    
    booking.status = BookingStatus.cancelled
    # Reduce booked_count
    event = db.query(Event).filter(Event.id == booking.event_id).first()
    event.booked_count -= 1
    db.commit()
    db.refresh(booking)
    
    # Invalidate caches after cancellation
    invalidate_event_caches(booking.event_id)
    invalidate_user_booking_cache(booking.user_id)
    
    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "event_id": booking.event_id,
        "status": booking.status.value,
        "updated_at": datetime.now().isoformat()
    }

# GET /users/{id}/bookings - View booking history
@router.get("/users/{user_id}/bookings")
def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    # Check cache first
    cache_key = make_user_bookings_cache_key(user_id)
    cached_bookings = get_cache(cache_key)
    
    if cached_bookings is not None:
        return cached_bookings
    
    # If not in cache, get from database
    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
    
    # Convert to dict for JSON serialization
    bookings_data = []
    for booking in bookings:
        event = db.query(Event).filter(Event.id == booking.event_id).first()
        booking_data = {
            "id": booking.id,
            "user_id": booking.user_id,
            "event_id": booking.event_id,
            "status": booking.status.value,
            "event_name": event.name if event else None,
            "event_venue": event.venue if event else None,
            "event_time": event.time.isoformat() if event and event.time else None,
            "created_at": booking.created_at.isoformat() if hasattr(booking, 'created_at') else None
        }
        bookings_data.append(booking_data)
    
    # Cache for 2 minutes
    set_cache(cache_key, bookings_data, ttl=120)
    
    return bookings_data
    return bookings
