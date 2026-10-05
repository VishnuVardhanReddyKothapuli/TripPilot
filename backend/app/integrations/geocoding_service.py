from pydantic import BaseModel
from typing import List, Optional, Tuple
from .base import BaseAPIClient, simple_cache

class GeoLocation(BaseModel):
    name: str
    latitude: float
    longitude: float
    country: Optional[str]
    country_code: Optional[str]
    admin1: Optional[str]
    population: Optional[int]
    timezone: Optional[str]

client = BaseAPIClient(base_url="https://geocoding-api.open-meteo.com/v1")

@simple_cache(ttl_seconds=86400)
async def search_location(query: str, count: int = 5) -> List[GeoLocation]:
    params = {
        "name": query,
        "count": count
    }
    data = await client.get("/search", params=params)
    if not data or "results" not in data:
        return []
    
    return [
        GeoLocation(
            name=res.get("name", ""),
            latitude=res.get("latitude", 0.0),
            longitude=res.get("longitude", 0.0),
            country=res.get("country"),
            country_code=res.get("country_code"),
            admin1=res.get("admin1"),
            population=res.get("population"),
            timezone=res.get("timezone")
        ) for res in data["results"]
    ]

async def get_coordinates(location_name: str) -> Optional[Tuple[float, float]]:
    locations = await search_location(location_name, count=1)
    if locations:
        return (locations[0].latitude, locations[0].longitude)
    return None
