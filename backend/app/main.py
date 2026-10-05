from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from app.api import trips, destinations, chat
from app.database import engine, Base
from app.config import get_settings
from app.security import require_access, RequestLimitMiddleware
# Import all models so they are registered with Base
from app.models import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    from app.integrations import countries_service, geocoding_service, places_service, weather_service
    for service in (countries_service, geocoding_service, places_service, weather_service):
        await service.client.close()
    await engine.dispose()


app = FastAPI(title="TripPilot AI API", lifespan=lifespan)
app.add_middleware(RequestLimitMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(trips.router, dependencies=[Depends(require_access)])
app.include_router(destinations.router, dependencies=[Depends(require_access)])
app.include_router(chat.router, dependencies=[Depends(require_access)])


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "name": "TripPilot AI API",
        "version": "1.0.0",
        "description": "Backend API for TripPilot AI Travel Planner"
    }
