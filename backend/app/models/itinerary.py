import uuid
from sqlalchemy import Column, String, Date, Integer, Numeric, DateTime, ForeignKey, Text, Float, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    version = Column(Integer, default=1)
    total_estimated_cost = Column(Numeric(12, 2), nullable=True)
    currency = Column(String)
    summary = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    trip = relationship("Trip", back_populates="itinerary")
    days = relationship("ItineraryDay", back_populates="itinerary", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Itinerary {self.id} for Trip {self.trip_id}>"

class ItineraryDay(Base):
    __tablename__ = "itinerary_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    itinerary_id = Column(UUID(as_uuid=True), ForeignKey("itineraries.id", ondelete="CASCADE"), index=True)
    day_number = Column(Integer)
    date = Column(Date)
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)

    itinerary = relationship("Itinerary", back_populates="days")
    activities = relationship("Activity", back_populates="day", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ItineraryDay {self.day_number}>"

class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_id = Column(UUID(as_uuid=True), ForeignKey("itinerary_days.id", ondelete="CASCADE"), index=True)
    order_index = Column(Integer)
    title = Column(String)
    description = Column(Text, nullable=True)
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    category = Column(String)
    estimated_cost = Column(Numeric(10, 2), nullable=True)
    cost_currency = Column(String, nullable=True)
    data_source = Column(String)
    notes = Column(Text, nullable=True)

    day = relationship("ItineraryDay", back_populates="activities")

    def __repr__(self):
        return f"<Activity {self.title}>"

class SavedPlace(Base):
    __tablename__ = "saved_places"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    place_type = Column(String)
    rating = Column(Float, nullable=True)
    source = Column(String)
    metadata_json = Column(JSON, nullable=True)

    trip = relationship("Trip")

    def __repr__(self):
        return f"<SavedPlace {self.name}>"
