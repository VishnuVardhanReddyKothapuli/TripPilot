from pydantic import BaseModel
from typing import List
from datetime import date, timedelta
from .base import BaseAPIClient, simple_cache

class WeatherDay(BaseModel):
    date: str
    temp_high: float
    temp_low: float
    precipitation_mm: float
    weather_code: int
    weather_description: str
    wind_speed_max: float

class WeatherData(BaseModel):
    data_source: str = "api"
    forecast: List[WeatherDay]

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Drizzle: Light intensity", 53: "Drizzle: Moderate intensity", 55: "Drizzle: Dense intensity",
    56: "Freezing Drizzle: Light intensity", 57: "Freezing Drizzle: Dense intensity",
    61: "Rain: Slight intensity", 63: "Rain: Moderate intensity", 65: "Rain: Heavy intensity",
    66: "Freezing Rain: Light intensity", 67: "Freezing Rain: Heavy intensity",
    71: "Snow fall: Slight intensity", 73: "Snow fall: Moderate intensity", 75: "Snow fall: Heavy intensity",
    77: "Snow grains",
    80: "Rain showers: Slight", 81: "Rain showers: Moderate", 82: "Rain showers: Violent",
    85: "Snow showers slight", 86: "Snow showers heavy",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}

client = BaseAPIClient(base_url="https://api.open-meteo.com/v1")

@simple_cache(ttl_seconds=3600)
async def get_weather_forecast(latitude: float, longitude: float, start_date: date, end_date: date) -> WeatherData:
    start_date = max(start_date, date.today())
    end_date = min(end_date, date.today() + timedelta(days=15))
    if start_date > end_date:
        return WeatherData(forecast=[])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weathercode", "windspeed_10m_max"],
        "timezone": "auto"
    }
    
    data = await client.get("/forecast", params=params)
    if not data or "daily" not in data:
        return WeatherData(forecast=[])
    
    daily = data["daily"]
    forecast = []
    
    for i in range(len(daily["time"])):
        code = daily["weathercode"][i]
        forecast.append(WeatherDay(
            date=daily["time"][i],
            temp_high=daily["temperature_2m_max"][i],
            temp_low=daily["temperature_2m_min"][i],
            precipitation_mm=daily["precipitation_sum"][i],
            weather_code=code,
            weather_description=WMO_CODES.get(code, "Unknown"),
            wind_speed_max=daily["windspeed_10m_max"][i]
        ))
        
    return WeatherData(forecast=forecast)
