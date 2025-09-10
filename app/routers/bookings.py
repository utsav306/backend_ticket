from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Event, Booking, BookingStatus, Waitlist
from app.schemas import BookingRequest
from app.routers.waitlist import move_from_waitlist_to_booking

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.get("")
def list_bookings():
    return {"bookings": []}

@router.post("/book/{event_id}")
def book_event(
    event_id: int,
    request: BookingRequest,
    db: Session = Depends(get_db)
):
    """Book an event or join waitlist if full."""
    
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user already has a booking
    existing_booking = db.query(Booking).filter(
        Booking.user_id == request.user_id,
        Booking.event_id == event_id,
        Booking.status == BookingStatus.BOOKED
    ).first()
    
    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a booking for this event"
        )
    
    # Check if user is on waitlist
    existing_waitlist = db.query(Waitlist).filter(
        Waitlist.user_id == request.user_id,
        Waitlist.event_id == event_id
    ).first()
    
    if existing_waitlist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already on the waitlist for this event"
        )
    
    # Check if event is full
    active_bookings = db.query(Booking).filter(
        Booking.event_id == event_id,
        Booking.status == BookingStatus.BOOKED
    ).count()
    
    if active_bookings >= event.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is full. Please join the waitlist instead."
        )
    
    # Create booking
    booking = Booking(
        user_id=request.user_id,
        event_id=event_id,
        status=BookingStatus.BOOKED
    )
    
    db.add(booking)
    event.booked_count = active_bookings + 1
    db.commit()
    db.refresh(booking)
    
    return {
        "message": "Event booked successfully",
        "booking_id": booking.id
    }

@router.delete("/cancel/{booking_id}")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    """Cancel a booking and process waitlist."""
    
    # Find the booking
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.status == BookingStatus.BOOKED
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active booking not found"
        )
    
    # Cancel the booking
    booking.status = BookingStatus.CANCELLED
    
    # Update event booked count
    event = db.query(Event).filter(Event.id == booking.event_id).first()
    if event:
        event.booked_count = max(0, event.booked_count - 1)
    
    db.commit()
    
    # Try to move someone from waitlist to booking
    moved = move_from_waitlist_to_booking(db, booking.event_id)
    
    response_message = "Booking cancelled successfully"
    if moved:
        response_message += ". Next person from waitlist has been moved to confirmed booking."
    
    return {"message": response_message}
