from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"

class BookingRequest(BaseModel):
    user_id: int

class WaitlistRequest(BaseModel):
    user_id: int

class WaitlistResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    position: int
    joined_at: datetime
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: UserRoleEnum = UserRoleEnum.USER  # Default to regular user

class EventCreate(BaseModel):
    name: str
    venue: str
    time: datetime
    capacity: int

class EventUpdate(BaseModel):
    name: Optional[str] = None
    venue: Optional[str] = None
    time: Optional[datetime] = None
    capacity: Optional[int] = None
