import uuid
from sqlalchemy import Column, String, Date, Integer, Numeric, DateTime, ForeignKey, Text, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title = Column(String)
    origin = Column(String)
    destination = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    num_travelers = Column(Integer, default=1)
    budget_amount = Column(Numeric(12, 2))
    budget_currency = Column(String, default="USD")
    travel_style = Column(String)
    status = Column(String, default="draft", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="trips")
    preferences = relationship("TripPreference", back_populates="trip", uselist=False, cascade="all, delete-orphan")
    itinerary = relationship("Itinerary", back_populates="trip", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="trip", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trip {self.title}>"

class TripPreference(Base):
    __tablename__ = "trip_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), unique=True)
    preferences = Column(ARRAY(String))
    additional_notes = Column(Text, nullable=True)

    trip = relationship("Trip", back_populates="preferences")

    def __repr__(self):
        return f"<TripPreference {self.trip_id}>"
