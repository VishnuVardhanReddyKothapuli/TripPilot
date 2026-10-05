import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker, get_db
from app.models.conversation import AgentRun
from app.models.trip import Trip
from app.schemas.chat import AgentStatusResponse, ModifyRequest
from app.schemas.trip import TripCreate, TripUpdate, TripResponse, TripListResponse
from app.services import trip_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post("/", response_model=TripResponse, status_code=201)
async def create_trip(data: TripCreate, db: AsyncSession = Depends(get_db)):
    return TripResponse.from_trip(await trip_service.create_trip(db, data))


@router.get("/", response_model=TripListResponse)
async def list_trips(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    items = await trip_service.list_trips(db, skip=skip, limit=limit)
    total = await db.scalar(select(func.count()).select_from(Trip))
    return TripListResponse(items=[TripResponse.from_trip(t) for t in items], total=total, skip=skip, limit=limit)


async def require_trip(db, trip_id, *, lock=False):
    trip = await trip_service.get_trip(db, trip_id, lock=lock)
    if trip is None:
        raise HTTPException(404, "Trip not found")
    return trip


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: UUID, db: AsyncSession = Depends(get_db)):
    return TripResponse.from_trip(await require_trip(db, trip_id))


@router.patch("/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: UUID, data: TripUpdate, db: AsyncSession = Depends(get_db)):
    trip = await trip_service.update_trip(db, trip_id, data)
    if trip is None:
        raise HTTPException(404, "Trip not found")
    return TripResponse.from_trip(trip)


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(trip_id: UUID, db: AsyncSession = Depends(get_db)):
    if not await trip_service.delete_trip(db, trip_id):
        raise HTTPException(404, "Trip not found")


async def last_success(db, trip_id):
    return await db.scalar(select(AgentRun).where(AgentRun.trip_id == trip_id, AgentRun.status == "completed").order_by(AgentRun.started_at.desc()).limit(1))


async def start_run(db, trip_id, tasks, instruction=None):
    trip = await require_trip(db, trip_id, lock=True)
    running = await db.scalar(select(AgentRun).where(AgentRun.trip_id == trip_id, AgentRun.status == "running").limit(1))
    if running:
        if running.started_at > datetime.now(timezone.utc) - timedelta(minutes=6):
            raise HTTPException(409, "Planning is already running for this trip")
        running.status = "failed"
        running.current_node = None
        running.error_message = "Planning was interrupted. Please retry."
        running.completed_at = datetime.now(timezone.utc)
    existing = await last_success(db, trip_id) if instruction else None
    if instruction and (not existing or trip.status == "draft"):
        raise HTTPException(409, "Generate an itinerary before modifying it")
    run = AgentRun(id=uuid4(), trip_id=trip_id, status="running", current_node="collect_preferences", started_at=datetime.now(timezone.utc))
    db.add(run)
    trip.status = "planning"
    await db.commit()  # Publish the run before the response can be polled.
    tasks.add_task(run_planner, trip_id, run.id, instruction)
    return AgentStatusResponse(status="running", run_id=str(run.id), current_node=run.current_node, steps=[])


@router.post("/{trip_id}/generate", response_model=AgentStatusResponse, status_code=202)
async def generate_itinerary(trip_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await start_run(db, trip_id, background_tasks)


@router.post("/{trip_id}/modify", response_model=AgentStatusResponse, status_code=202)
async def modify_itinerary(trip_id: UUID, data: ModifyRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await start_run(db, trip_id, background_tasks, data.instruction)


@router.get("/{trip_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(trip_id: UUID, db: AsyncSession = Depends(get_db)):
    trip = await require_trip(db, trip_id, lock=True)
    run = await db.scalar(select(AgentRun).where(AgentRun.trip_id == trip_id).order_by(AgentRun.started_at.desc()).limit(1))
    if run is None:
        return AgentStatusResponse(status="idle", steps=[])
    if run.status == "running" and run.started_at < datetime.now(timezone.utc) - timedelta(minutes=6):
        run.status = "failed"
        run.current_node = None
        run.error_message = "Planning was interrupted. Please retry."
        run.completed_at = datetime.now(timezone.utc)
        trip.status = "error"
        await db.commit()
    result = run.result_json or {}
    itinerary = result.get("itinerary")
    if not itinerary and trip.status != "draft":
        previous = await last_success(db, trip_id)
        itinerary = (previous.result_json or {}).get("itinerary") if previous else None
    if trip.status == "draft":
        return AgentStatusResponse(status="idle", steps=[])
    return AgentStatusResponse(status=run.status, run_id=str(run.id), current_node=run.current_node, steps=result.get("steps", []), itinerary=itinerary, error=run.error_message if run.status == "failed" else None)


async def run_planner(trip_id, run_id, instruction=None):
    from app.agents.graph import plan_trip
    async with async_session_maker() as db:
        try:
            trip = await require_trip(db, trip_id)
            previous = await last_success(db, trip_id) if instruction else None
            state = {
                **TripResponse.from_trip(trip).model_dump(mode="json"),
                "trip_id": str(trip_id), "messages": [], "steps_completed": [],
                "errors": [], "needs_clarification": False,
                "is_modification": instruction is not None,
                "modification_instruction": instruction,
                "itinerary": (previous.result_json or {}).get("itinerary") if previous else None,
            }
            await db.commit()
            result = await asyncio.wait_for(plan_trip(state), timeout=300)
            if not result.get("itinerary", {}).get("days"):
                raise ValueError("No itinerary was generated")
            trip = await require_trip(db, trip_id, lock=True)
            run = await db.get(AgentRun, run_id)
            if run.status != "running":
                return
            run.result_json = {
                "itinerary": result["itinerary"],
                "steps": [{"node_name": s, "status": "completed", "message": f"Completed {s}"} for s in dict.fromkeys(result.get("steps_completed", []))],
            }
            run.status = "completed"
            run.current_node = None
            run.completed_at = datetime.now(timezone.utc)
            trip.status = "generated"
            await db.commit()
        except Exception:
            logger.exception("Planning failed for trip %s", trip_id)
            await db.rollback()
            trip = await require_trip(db, trip_id, lock=True)
            run = await db.get(AgentRun, run_id)
            if run and run.status == "running":
                run.status = "failed"
                run.current_node = None
                run.error_message = "Could not modify the itinerary. Check the Ollama connection and retry." if instruction else "Planning failed or timed out. Please retry."
                run.completed_at = datetime.now(timezone.utc)
                trip.status = "error"
                await db.commit()
