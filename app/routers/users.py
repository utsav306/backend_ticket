from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Event, Booking, BookingStatus, UserRole
from app.schemas import BookingRequest, UserCreate
from datetime import datetime

router = APIRouter()

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

# POST /users - Create user
@router.post("/users")
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

# GET /users - List all users (Admin only for demo, could be public)
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

# GET /events - Browse all events
@router.get("/events")
def get_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    return events

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
    return booking

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
    return booking

# GET /users/{id}/bookings - View booking history
@router.get("/users/{user_id}/bookings")
def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
    return bookings
