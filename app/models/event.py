from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    venue = Column(String, nullable=False)
    time = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False)
    booked_count = Column(Integer, default=0)  # to track filled seats

    bookings = relationship("Booking", back_populates="event")
