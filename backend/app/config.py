from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from urllib.parse import urlsplit

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "TripPilot AI"
    DATABASE_URL: str
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = ""
    BACKEND_URL: str = "http://localhost:8001"
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    OPEN_METEO_GEOCODING_URL: str = "https://geocoding-api.open-meteo.com/v1"
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    REST_COUNTRIES_URL: str = "https://restcountries.com/v3.1"
    SECRET_KEY: str = ""

    @property
    def cors_origins(self) -> list[str]:
        origins = {url.strip().rstrip("/") for url in [self.FRONTEND_URL, *self.CORS_ORIGINS.split(",")] if url.strip()}
        if self.APP_ENV == "development":
            frontend = urlsplit(self.FRONTEND_URL.strip())
            if frontend.hostname in {"localhost", "127.0.0.1", "::1"}:
                port = f":{frontend.port}" if frontend.port else ""
                origins.update(f"{frontend.scheme}://{host}{port}" for host in ("localhost", "127.0.0.1", "[::1]"))
        return sorted(origins)

    @field_validator("DATABASE_URL")
    @classmethod
    def async_database_url(cls, value: str) -> str:
        for prefix in ("postgres://", "postgresql://", "postgresql+psycopg://"):
            if value.startswith(prefix):
                return value.replace(prefix, "postgresql+asyncpg://", 1)
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
