import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional

from app.models.trip import Trip, TripPreference
from app.models.user import User
from app.schemas.trip import TripCreate, TripUpdate
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update
from app.models.conversation import AgentRun

logger = logging.getLogger(__name__)


async def get_or_create_default_user(db: AsyncSession) -> User:
    """Get the default user or create one for MVP (no auth)."""
    await db.execute(insert(User).values(email="default@trippilot.ai", display_name="Traveler").on_conflict_do_nothing(index_elements=[User.email]))
    return (await db.execute(select(User).where(User.email == "default@trippilot.ai"))).scalar_one()


async def create_trip(db: AsyncSession, trip_data: TripCreate) -> Trip:
    """Create a new trip with preferences."""
    user = await get_or_create_default_user(db)

    trip = Trip(
        user_id=user.id,
        title=f"Trip to {trip_data.destination}",
        origin=trip_data.origin,
        destination=trip_data.destination,
        start_date=trip_data.start_date,
        end_date=trip_data.end_date,
        num_travelers=trip_data.num_travelers,
        budget_amount=trip_data.budget_amount,
        budget_currency=trip_data.budget_currency,
        travel_style=trip_data.travel_style,
        status="draft",
    )
    db.add(trip)
    await db.flush()

    if trip_data.preferences or trip_data.additional_notes:
        prefs = TripPreference(
            trip_id=trip.id,
            preferences=trip_data.preferences,
            additional_notes=trip_data.additional_notes,
        )
        db.add(prefs)

    await db.commit()
    trip = await get_trip(db, trip.id)
    logger.info(f"Created trip {trip.id}: {trip.title}")
    return trip


async def get_trip(db: AsyncSession, trip_id: UUID, *, lock: bool = False) -> Optional[Trip]:
    """Get a trip by ID with eager-loaded preferences."""
    query = (
        select(Trip)
        .options(selectinload(Trip.preferences))
        .where(Trip.id == trip_id)
    )
    result = await db.execute(query.with_for_update() if lock else query)
    return result.scalar_one_or_none()


async def list_trips(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> list[Trip]:
    """List trips with optional filters."""
    query = select(Trip).options(selectinload(Trip.preferences))
    if user_id:
        query = query.where(Trip.user_id == user_id)
    if status:
        query = query.where(Trip.status == status)
    query = query.order_by(Trip.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_trip(db: AsyncSession, trip_id: UUID, update_data: TripUpdate) -> Optional[Trip]:
    """Update a trip's fields."""
    trip = await get_trip(db, trip_id, lock=True)
    if not trip:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        return trip
    if trip.status == "planning":
        raise HTTPException(409, "Wait for planning to finish before editing this trip")
    current = {key: getattr(trip, key) for key in TripCreate.model_fields if key not in {"preferences", "additional_notes"}}
    current.update(preferences=(trip.preferences.preferences or []) if trip.preferences else [], additional_notes=trip.preferences.additional_notes if trip.preferences else None)
    try:
        validated = TripCreate.model_validate({**current, **update_dict})
    except ValidationError:
        raise HTTPException(422, "Invalid trip details: check dates, budget and preferences")

    # Handle preferences separately
    if "preferences" in update_dict or "additional_notes" in update_dict:
        if not trip.preferences:
            trip.preferences = TripPreference(preferences=[])
        trip.preferences.preferences = validated.preferences
        trip.preferences.additional_notes = validated.additional_notes
    update_dict.pop("preferences", None)
    update_dict.pop("additional_notes", None)

    for key, value in update_dict.items():
        if hasattr(trip, key):
            setattr(trip, key, value)
    trip.title = f"Trip to {trip.destination}"
    trip.status = "draft"
    # Keep history, but never reuse a plan built for different trip details.
    await db.execute(update(AgentRun).where(
        AgentRun.trip_id == trip_id, AgentRun.status == "completed"
    ).values(status="superseded"))

    await db.commit()
    trip = await get_trip(db, trip.id)
    logger.info(f"Updated trip {trip.id}")
    return trip


async def delete_trip(db: AsyncSession, trip_id: UUID) -> bool:
    """Delete a trip."""
    trip = await get_trip(db, trip_id, lock=True)
    if not trip:
        return False
    if trip.status == "planning":
        raise HTTPException(409, "Wait for planning to finish before deleting this trip")
    await db.delete(trip)
    await db.commit()
    logger.info(f"Deleted trip {trip_id}")
    return True
