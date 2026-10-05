from pydantic import BaseModel
from typing import List, Dict, Optional
from .base import BaseAPIClient, simple_cache

class CurrencyInfo(BaseModel):
    code: str
    name: str
    symbol: str

class CountryInfo(BaseModel):
    name: str
    official_name: str
    capital: List[str]
    region: str
    subregion: str
    languages: Dict[str, str]
    currencies: Dict[str, CurrencyInfo]
    population: int
    area: float
    timezones: List[str]
    flag_emoji: str
    calling_codes: List[str]

client = BaseAPIClient(base_url="https://restcountries.com/v3.1")

@simple_cache(ttl_seconds=604800)
async def get_country_info(country_name_or_code: str) -> Optional[CountryInfo]:
    if len(country_name_or_code) in (2, 3):
        endpoint = f"/alpha/{country_name_or_code}"
    else:
        endpoint = f"/name/{country_name_or_code}"
        
    data = await client.get(endpoint)
    if not data or not isinstance(data, list) or len(data) == 0:
        return None
        
    country = data[0]
    
    currencies = {}
    for code, info in country.get("currencies", {}).items():
        currencies[code] = CurrencyInfo(
            code=code,
            name=info.get("name", ""),
            symbol=info.get("symbol", "")
        )
        
    return CountryInfo(
        name=country.get("name", {}).get("common", ""),
        official_name=country.get("name", {}).get("official", ""),
        capital=country.get("capital", []),
        region=country.get("region", ""),
        subregion=country.get("subregion", ""),
        languages=country.get("languages", {}),
        currencies=currencies,
        population=country.get("population", 0),
        area=country.get("area", 0.0),
        timezones=country.get("timezones", []),
        flag_emoji=country.get("flag", ""),
        calling_codes=[country.get("idd", {}).get("root", "")] + country.get("idd", {}).get("suffixes", [])
    )

async def get_currency_info(country_name: str) -> Optional[Dict[str, CurrencyInfo]]:
    info = await get_country_info(country_name)
    if info:
        return info.currencies
    return None
