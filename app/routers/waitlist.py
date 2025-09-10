from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models import User, Event, Booking, BookingStatus, Waitlist
from app.schemas import WaitlistRequest, WaitlistResponse

router = APIRouter(prefix="/waitlist", tags=["waitlist"])

def get_next_waitlist_position(db: Session, event_id: int) -> int:
    """Get the next position in the waitlist for an event."""
    max_position = db.query(func.max(Waitlist.position)).filter(
        Waitlist.event_id == event_id
    ).scalar()
    return (max_position or 0) + 1

def move_from_waitlist_to_booking(db: Session, event_id: int) -> bool:
    """
    Move the first person from waitlist to confirmed booking if space becomes available.
    Returns True if someone was moved, False otherwise.
    """
    # Check if event has available capacity
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return False
    
    active_bookings = db.query(Booking).filter(
        Booking.event_id == event_id,
        Booking.status == BookingStatus.BOOKED
    ).count()
    
    if active_bookings >= event.capacity:
        return False
    
    # Get the first person in waitlist (lowest position)
    first_waitlist = db.query(Waitlist).filter(
        Waitlist.event_id == event_id
    ).order_by(Waitlist.position).first()
    
    if not first_waitlist:
        return False
    
    # Create a booking for this user
    new_booking = Booking(
        user_id=first_waitlist.user_id,
        event_id=event_id,
        status=BookingStatus.BOOKED
    )
    db.add(new_booking)
    
    # Remove from waitlist
    db.delete(first_waitlist)
    
    # Update positions for remaining waitlist entries
    remaining_waitlist = db.query(Waitlist).filter(
        Waitlist.event_id == event_id,
        Waitlist.position > first_waitlist.position
    ).all()
    
    for waitlist_entry in remaining_waitlist:
        waitlist_entry.position -= 1
    
    # Update booked count
    event.booked_count = active_bookings + 1
    
    db.commit()
    return True

@router.post("/join/{event_id}", response_model=WaitlistResponse)
def join_waitlist(
    event_id: int,
    request: WaitlistRequest,
    db: Session = Depends(get_db)
):
    """Join waitlist for an event."""
    
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
    
    # Check if user already has a booking for this event
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
    
    # Check if user is already on waitlist
    existing_waitlist = db.query(Waitlist).filter(
        Waitlist.user_id == request.user_id,
        Waitlist.event_id == event_id
    ).first()
    
    if existing_waitlist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already on the waitlist for this event"
        )
    
    # Check if event is actually full
    active_bookings = db.query(Booking).filter(
        Booking.event_id == event_id,
        Booking.status == BookingStatus.BOOKED
    ).count()
    
    if active_bookings < event.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not full. Please book directly instead of joining waitlist."
        )
    
    # Add to waitlist
    position = get_next_waitlist_position(db, event_id)
    waitlist_entry = Waitlist(
        user_id=request.user_id,
        event_id=event_id,
        position=position
    )
    
    db.add(waitlist_entry)
    db.commit()
    db.refresh(waitlist_entry)
    
    return waitlist_entry

@router.delete("/leave/{event_id}")
def leave_waitlist(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Leave waitlist for an event."""
    
    # Find the waitlist entry
    waitlist_entry = db.query(Waitlist).filter(
        Waitlist.user_id == user_id,
        Waitlist.event_id == event_id
    ).first()
    
    if not waitlist_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not on the waitlist for this event"
        )
    
    # Update positions for users after this one
    users_after = db.query(Waitlist).filter(
        Waitlist.event_id == event_id,
        Waitlist.position > waitlist_entry.position
    ).all()
    
    for user_entry in users_after:
        user_entry.position -= 1
    
    # Remove from waitlist
    db.delete(waitlist_entry)
    db.commit()
    
    return {"message": "Successfully removed from waitlist"}

@router.get("/event/{event_id}", response_model=List[WaitlistResponse])
def get_event_waitlist(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get waitlist for a specific event."""
    
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    waitlist = db.query(Waitlist).filter(
        Waitlist.event_id == event_id
    ).order_by(Waitlist.position).all()
    
    return waitlist

@router.get("/user/{user_id}", response_model=List[WaitlistResponse])
def get_user_waitlists(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all waitlists for a specific user."""
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    waitlists = db.query(Waitlist).filter(
        Waitlist.user_id == user_id
    ).order_by(Waitlist.joined_at).all()
    
    return waitlists

@router.get("/position/{event_id}/{user_id}")
def get_waitlist_position(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's position in waitlist for an event."""
    
    waitlist_entry = db.query(Waitlist).filter(
        Waitlist.user_id == user_id,
        Waitlist.event_id == event_id
    ).first()
    
    if not waitlist_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not on the waitlist for this event"
        )
    
    return {
        "position": waitlist_entry.position,
        "total_in_waitlist": db.query(Waitlist).filter(
            Waitlist.event_id == event_id
        ).count()
    }

@router.post("/process/{event_id}")
def process_waitlist(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Process waitlist for an event (move people from waitlist to bookings if space available).
    This endpoint is typically called when a booking is cancelled.
    """
    
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    moved_count = 0
    while move_from_waitlist_to_booking(db, event_id):
        moved_count += 1
    
    return {
        "message": f"Processed waitlist for event {event_id}",
        "moved_to_bookings": moved_count
    }
