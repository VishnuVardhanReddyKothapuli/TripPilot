from pydantic import BaseModel
from typing import List, Optional, Dict
from .base import BaseAPIClient, simple_cache
import math

class Place(BaseModel):
    name: str
    type: str
    latitude: float
    longitude: float
    tags: Dict[str, str]
    rating: Optional[float] = None
    data_source: str = "api"
    source_url: Optional[str] = None

client = BaseAPIClient(base_url="https://overpass-api.de/api", timeout=25.0)

@simple_cache(ttl_seconds=21600)
async def find_nearby_places(latitude: float, longitude: float, radius_meters: int = 5000, place_types: Optional[List[str]] = None) -> List[Place]:
    if not place_types:
        place_types = ["tourism", "amenity", "historic", "natural"]
    if not set(place_types) <= {"tourism", "amenity", "historic", "natural"}:
        raise ValueError("Unsupported place types")
    if not (math.isfinite(latitude) and math.isfinite(longitude) and -90 <= latitude <= 90 and -180 <= longitude <= 180 and 100 <= radius_meters <= 15000):
        raise ValueError("Invalid coordinates or radius")
        
    values = {
        "tourism": "attraction|museum|gallery|viewpoint|zoo|aquarium|theme_park|hotel|hostel|guest_house|motel",
        "historic": "castle|monument|memorial|ruins|fort|archaeological_site|palace",
        "natural": "beach|peak|waterfall|cave_entrance",
        "amenity": "restaurant|cafe|fast_food|food_court",
    }
    filters = "".join(f'nwr["{pt}"~"^({values[pt]})$"]["name"]'
                      f'(around:{radius_meters},{latitude},{longitude});' for pt in place_types)
    query = f'[out:json][timeout:25];({filters});out center 500;'
    
    data = await client.get("/interpreter", params={"data": query}, rate_limit_delay=1.0)
    if not data or "elements" not in data:
        return []
        
    places = []
    for el in data["elements"]:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
            
        place_type = "unknown"
        for pt in place_types:
            if pt in tags:
                place_type = f"{pt}:{tags[pt]}"
                break
                
        places.append(Place(
            name=name,
            type=place_type,
            latitude=el.get("lat", el.get("center", {}).get("lat", latitude)),
            longitude=el.get("lon", el.get("center", {}).get("lon", longitude)),
            tags=tags,
            source_url=f'https://www.openstreetmap.org/{el.get("type", "node")}/{el["id"]}',
        ))
        
    return places

async def find_attractions(lat: float, lon: float, radius: int = 10000) -> List[Place]:
    places = await find_nearby_places(lat, lon, radius, ["tourism", "historic", "natural"])
    return [p for p in places if p.tags.get("tourism") not in {"hotel", "hostel", "guest_house", "motel"}]

async def find_restaurants(lat: float, lon: float, radius: int = 3000) -> List[Place]:
    return [p for p in await find_nearby_places(lat, lon, radius, ["amenity"]) if p.tags.get("amenity") in {"restaurant", "cafe", "fast_food", "food_court"}]
