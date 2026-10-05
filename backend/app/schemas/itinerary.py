from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Optional
from datetime import date


class GeneratedActivity(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=2000)
    location_name: str = Field(default="", max_length=300)
    start_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    duration_minutes: int = Field(ge=0, le=1440)
    category: Literal["transport", "accommodation", "food", "activity", "sightseeing"]
    estimated_cost: float = Field(ge=0, le=100000000, allow_inf_nan=False)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    cost_currency: str = "USD"
    data_source: str = "estimated"
    source_url: Optional[str] = None
    notes: str = ""


class GeneratedDay(BaseModel):
    day_number: int = Field(ge=1, le=30)
    date: date
    title: str = Field(min_length=1, max_length=300)
    summary: str = Field(default="", max_length=2000)
    activities: List[GeneratedActivity] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def valid_schedule(self):
        self.activities.sort(key=lambda a: a.start_time)
        end = "00:00"
        for activity in self.activities:
            if activity.start_time < end or activity.end_time < activity.start_time:
                raise ValueError("Activities must not overlap")
            end = activity.end_time
        return self


class GeneratedItinerary(BaseModel):
    summary: str = Field(default="", max_length=4000)
    days: List[GeneratedDay] = Field(min_length=1, max_length=30)
    currency: str = "USD"
