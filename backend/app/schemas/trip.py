from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing import Annotated, List, Literal, Optional
from datetime import date, datetime
from uuid import UUID


Location = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Currency = Literal["USD", "EUR", "GBP", "INR", "JPY", "AUD", "CAD", "THB"]
Style = Literal["budget", "balanced", "luxury"]
Preference = Literal["adventure", "nature", "food", "historical", "beaches", "shopping", "relaxation", "nightlife"]


class TripCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: Location
    destination: Location
    start_date: date
    end_date: date
    num_travelers: int = Field(default=1, ge=1, le=20)
    budget_amount: float = Field(gt=0, le=100000000, allow_inf_nan=False)
    budget_currency: Currency = "USD"
    travel_style: Style
    preferences: List[Preference] = Field(default_factory=list, max_length=8)
    additional_notes: Optional[str] = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def valid_dates(self):
        if not 0 <= (self.end_date - self.start_date).days < 30:
            raise ValueError("Trips must last 1 to 30 days, with end date on or after start date")
        self.preferences = list(dict.fromkeys(self.preferences))
        return self


class TripUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: Optional[Location] = None
    destination: Optional[Location] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    num_travelers: Optional[int] = Field(default=None, ge=1, le=20)
    budget_amount: Optional[float] = Field(default=None, gt=0, le=100000000, allow_inf_nan=False)
    budget_currency: Optional[Currency] = None
    travel_style: Optional[Style] = None
    preferences: Optional[List[Preference]] = Field(default=None, max_length=8)
    additional_notes: Optional[str] = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def reject_null_fields(self):
        if any(getattr(self, key) is None for key in self.model_fields_set - {"additional_notes"}):
            raise ValueError("Only additional_notes may be null")
        return self


class TripPreferencesResponse(BaseModel):
    preferences: List[str] = []
    additional_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TripResponse(BaseModel):
    id: UUID
    title: str
    origin: str
    destination: str
    start_date: date
    end_date: date
    num_travelers: int
    budget_amount: float
    budget_currency: str
    travel_style: str
    status: str
    preferences: List[str] = []
    additional_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_trip(cls, trip) -> "TripResponse":
        """Create a TripResponse from a Trip ORM object."""
        prefs = []
        notes = None
        if trip.preferences:
            prefs = trip.preferences.preferences or []
            notes = trip.preferences.additional_notes
        return cls(
            id=trip.id,
            title=trip.title or f"Trip to {trip.destination}",
            origin=trip.origin,
            destination=trip.destination,
            start_date=trip.start_date,
            end_date=trip.end_date,
            num_travelers=trip.num_travelers,
            budget_amount=float(trip.budget_amount) if trip.budget_amount else 0,
            budget_currency=trip.budget_currency or "USD",
            travel_style=trip.travel_style or "balanced",
            status=trip.status or "draft",
            preferences=prefs,
            additional_notes=notes,
            created_at=trip.created_at,
            updated_at=trip.updated_at,
        )


class TripListResponse(BaseModel):
    items: List[TripResponse]
    total: int
    skip: int = 0
    limit: int = 10
