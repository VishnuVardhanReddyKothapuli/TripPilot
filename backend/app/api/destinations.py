import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date

from app.integrations import geocoding_service, weather_service, places_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/destinations", tags=["destinations"])


@router.get("/search")
async def search_destinations(q: str = Query(min_length=2, max_length=200)):
    """Search for destinations by name using geocoding API."""
    try:
        results = await geocoding_service.search_location(q, count=5)
        return {
            "results": [r.model_dump() for r in results],
            "data_source": "api",
        }
    except Exception as e:
        logger.error(f"Error searching destinations: {e}")
        raise HTTPException(502, "Destination lookup is unavailable")


@router.get("/{destination}/weather")
async def get_weather(
    destination: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """Get weather forecast for a destination."""
    try:
        # Geocode the destination first
        coords = await geocoding_service.get_coordinates(destination)
        if not coords:
            raise HTTPException(status_code=404, detail="Destination not found")

        lat, lon = coords

        # Parse dates or use defaults
        from datetime import datetime, timedelta

        if start_date:
            sd = start_date
        else:
            sd = datetime.now().date() + timedelta(days=1)

        if end_date:
            ed = end_date
        else:
            ed = sd + timedelta(days=7)

        if not 0 <= (ed - sd).days < 30:
            raise HTTPException(422, "Weather date range must be 1 to 30 days")
        weather_data = await weather_service.get_weather_forecast(lat, lon, sd, ed)
        return {
            "data": weather_data.model_dump() if weather_data else None,
            "data_source": "api",
            "location": {"latitude": lat, "longitude": lon},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching weather for {destination}: {e}")
        raise HTTPException(502, "Weather lookup is unavailable")


@router.get("/{destination}/places")
async def get_places(
    destination: str,
    types: Optional[str] = Query(None, max_length=100),
    radius: int = Query(5000, ge=100, le=15000),
):
    """Get nearby places and attractions for a destination."""
    try:
        coords = await geocoding_service.get_coordinates(destination)
        if not coords:
            raise HTTPException(status_code=404, detail="Destination not found")

        lat, lon = coords
        place_types = types.split(",") if types else None
        if place_types and not set(place_types) <= {"tourism", "amenity", "historic", "natural"}:
            raise HTTPException(422, "Invalid place types")
        places = await places_service.find_nearby_places(lat, lon, radius_meters=radius, place_types=place_types)
        return {
            "data": [p.model_dump() for p in places] if places else [],
            "data_source": "api",
            "location": {"latitude": lat, "longitude": lon},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching places for {destination}: {e}")
        raise HTTPException(502, "Places lookup is unavailable")
