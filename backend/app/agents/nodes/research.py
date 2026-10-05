"""Research nodes that call real external APIs for destination, weather, and attraction data."""
import logging
from ..state import TripPlannerState

logger = logging.getLogger(__name__)


async def destination_research(state: TripPlannerState) -> TripPlannerState:
    """Research destination: geocode, get country info."""
    state["current_step"] = "destination_research"
    destination = state.get("destination", "Unknown")

    try:
        from app.integrations import geocoding_service, countries_service


        # Geocode destination
        coords = await geocoding_service.get_coordinates(destination)
        locations = await geocoding_service.search_location(destination, count=1)

        if coords:
            lat, lon = coords
            location_info = locations[0].model_dump() if locations else {}
            country_name = location_info.get("country", "")

            # Get country info
            country_info = None
            if country_name:
                try:
                    country_info = await countries_service.get_country_info(country_name)
                    if country_info:
                        country_info = country_info.model_dump()
                except Exception as e:
                    logger.warning(f"Country info lookup failed: {e}")

            state["destination_info"] = {
                "name": destination,
                "coordinates": {"lat": lat, "lon": lon},
                "country": country_name,
                "country_code": location_info.get("country_code", ""),
                "timezone": location_info.get("timezone", "UTC"),
                "population": location_info.get("population"),
                "country_info": country_info,
                "data_source": "api",
            }
        else:
            logger.warning(f"Could not geocode {destination}, using fallback")
            state["destination_info"] = {
                "name": destination,
                "coordinates": {"lat": 0.0, "lon": 0.0},
                "country": "Unknown",
                "timezone": "UTC",
                "data_source": "estimated",
            }

    except Exception as e:
        logger.error(f"Destination research failed: {e}")
        state["destination_info"] = {
            "name": destination,
            "coordinates": {"lat": 0.0, "lon": 0.0},
            "country": "Unknown",
            "timezone": "UTC",
            "data_source": "estimated",
        }
        state["errors"].append(f"destination_research: {str(e)}")

    state["steps_completed"].append("destination_research")
    return state


async def weather_research(state: TripPlannerState) -> TripPlannerState:
    """Fetch weather forecast from Open-Meteo API."""
    state["current_step"] = "weather_research"

    dest_info = state.get("destination_info", {})
    coords = dest_info.get("coordinates", {})
    lat = coords.get("lat", 0.0)
    lon = coords.get("lon", 0.0)

    if lat == 0.0 and lon == 0.0:
        state["weather_data"] = []
        state["steps_completed"].append("weather_research")
        return state

    try:
        from app.integrations import weather_service
        from datetime import date

        start = date.fromisoformat(state.get("start_date", "2025-01-01"))
        end = date.fromisoformat(state.get("end_date", "2025-01-07"))

        weather = await weather_service.get_weather_forecast(lat, lon, start, end)

        if weather and weather.forecast:
            state["weather_data"] = [day.model_dump() for day in weather.forecast]
        else:
            state["weather_data"] = []

    except Exception as e:
        logger.error(f"Weather research failed: {e}")
        state["weather_data"] = []
        state["errors"].append(f"weather_research: {str(e)}")

    state["steps_completed"].append("weather_research")
    return state


async def attraction_research(state: TripPlannerState) -> TripPlannerState:
    """Find nearby attractions and restaurants using Overpass API."""
    state["current_step"] = "attraction_research"
    from app.integrations.travel_guide_service import research_destination
    guide = await research_destination(state["destination"])
    state["travel_research"] = guide

    dest_info = state.get("destination_info", {})
    coords = dest_info.get("coordinates", {})
    lat = coords.get("lat", 0.0)
    lon = coords.get("lon", 0.0)

    if lat == 0.0 and lon == 0.0:
        state["attractions"] = guide["attractions"]
        state["restaurants"] = guide["restaurants"]
        state["steps_completed"].append("attraction_research")
        return state

    try:
        from app.integrations import places_service


        # Find attractions
        try:
            attractions = await places_service.find_attractions(lat, lon, radius=15000)
            state["attractions"] = [
                {
                    "name": p.name,
                    "type": p.type,
                    "lat": p.latitude,
                    "lon": p.longitude,
                    "data_source": p.data_source,
                    "source_url": p.source_url,
                    "description": p.tags.get("description", ""),
                    "address": ", ".join(p.tags[k] for k in ("addr:street", "addr:city") if k in p.tags),
                    "opening_hours": p.tags.get("opening_hours", ""),
                }
                for p in (attractions or [])[:80]
            ]
        except Exception as e:
            logger.warning(f"Attraction search failed: {e}")
            state["attractions"] = []

        # Find restaurants
        try:
            restaurants = await places_service.find_restaurants(lat, lon, radius=5000)
            state["restaurants"] = [
                {
                    "name": p.name,
                    "type": p.type,
                    "lat": p.latitude,
                    "lon": p.longitude,
                    "data_source": p.data_source,
                    "source_url": p.source_url,
                    "description": p.tags.get("description", ""),
                    "cuisine": p.tags.get("cuisine", ""),
                    "address": ", ".join(p.tags[k] for k in ("addr:street", "addr:city") if k in p.tags),
                }
                for p in (restaurants or [])[:60]
            ]
        except Exception as e:
            logger.warning(f"Restaurant search failed: {e}")
            state["restaurants"] = []


    except Exception as e:
        logger.error(f"Attraction research failed: {e}")
        state["attractions"] = []
        state["restaurants"] = []
        state["errors"].append(f"attraction_research: {str(e)}")

    for key in ("attractions", "restaurants"):
        combined = guide[key] + (state.get(key) or [])
        seen = set()
        state[key] = []
        for place in combined:
            name = place["name"].casefold()
            if name not in seen:
                state[key].append(place)
                seen.add(name)
    state["steps_completed"].append("attraction_research")
    return state
