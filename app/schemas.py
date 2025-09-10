from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"

class BookingRequest(BaseModel):
    user_id: int

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
