from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Event, Booking
from app.schemas import EventCreate, EventUpdate
from app.cache.cache_utils import (
    get_cache, set_cache, 
    make_analytics_cache_key, make_event_cache_key,
    invalidate_event_caches, clear_cache_pattern
)
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])

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
    
    # Invalidate events cache after creating new event
    invalidate_event_caches()
    
    return {
        "id": event.id,
        "name": event.name,
        "venue": event.venue,
        "time": event.time.isoformat() if event.time else None,
        "capacity": event.capacity,
        "booked_count": event.booked_count
    }

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
    
    # Invalidate caches after updating event
    invalidate_event_caches(event_id)
    
    return {
        "id": event.id,
        "name": event.name,
        "venue": event.venue,
        "time": event.time.isoformat() if event.time else None,
        "capacity": event.capacity,
        "booked_count": event.booked_count
    }

# GET /admin/analytics - Simple analytics
@router.get("/admin/analytics")
def analytics(db: Session = Depends(get_db)):
    # Check cache first
    cache_key = make_analytics_cache_key()
    cached_analytics = get_cache(cache_key)
    
    if cached_analytics is not None:
        return cached_analytics
    
    # If not in cache, calculate analytics
    total_bookings = db.query(Booking).count()
    popular_events = db.query(Event).order_by(Event.booked_count.desc()).limit(5).all()
    
    utilization = []
    for e in db.query(Event).all():
        util = (e.booked_count / e.capacity) * 100 if e.capacity else 0
        utilization.append({
            "event_id": e.id,
            "event_name": e.name,
            "utilization_percent": round(util, 2),
            "booked_count": e.booked_count,
            "capacity": e.capacity
        })
    
    # Convert popular events to dict
    popular_events_data = [
        {
            "id": event.id,
            "name": event.name,
            "venue": event.venue,
            "booked_count": event.booked_count,
            "capacity": event.capacity,
            "utilization_percent": round((event.booked_count / event.capacity) * 100, 2) if event.capacity else 0
        }
        for event in popular_events
    ]
    
    analytics_data = {
        "total_bookings": total_bookings,
        "popular_events": popular_events_data,
        "utilization": utilization,
        "generated_at": datetime.now().isoformat()
    }
    
    # Cache for 10 minutes
    set_cache(cache_key, analytics_data, ttl=600)
    
    return analytics_data

# GET /admin/cache/status - Cache status and management
@router.get("/admin/cache/status")
def cache_status():
    from app.cache.redis_client import redis_client
    
    if redis_client:
        try:
            info = redis_client.info()
            return {
                "cache_type": "Redis",
                "status": "connected",
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed")
            }
        except Exception as e:
            return {
                "cache_type": "Redis",
                "status": "error",
                "error": str(e)
            }
    else:
        return {
            "cache_type": "In-Memory",
            "status": "active",
            "note": "Redis not available, using fallback cache"
        }

# DELETE /cache/clear - Clear all cache
@router.delete("/cache/clear")
def clear_all_cache():
    try:
        # Clear all cache patterns
        clear_cache_pattern("*")
        return {"message": "All cache cleared successfully"}
    except Exception as e:
        return {"error": f"Failed to clear cache: {str(e)}"}

# DELETE /cache/events - Clear event-related cache
@router.delete("/cache/events")
def clear_events_cache():
    try:
        invalidate_event_caches()
        return {"message": "Events cache cleared successfully"}
    except Exception as e:
        return {"error": f"Failed to clear events cache: {str(e)}"}
