import logging
import uuid as uuid_mod
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatRequest, ChatResponse
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a chat message. For MVP, provides a helpful response."""
    conversation_id = request.conversation_id or uuid_mod.uuid4()
    if request.trip_id:
        from app.services.trip_service import get_trip
        if not await get_trip(db, request.trip_id):
            raise HTTPException(404, "Trip not found")

    # For MVP: Return a helpful message
    if request.trip_id:
        message = (
            "I can help you modify your trip! Try commands like:\n"
            "- 'Add more adventure activities'\n"
            "- 'Make the trip more budget-friendly'\n"
            "- 'Replace day 2 activities with beach activities'\n\n"
            "Use the 'Modify Itinerary' feature in the trip workspace for best results."
        )
    else:
        message = (
            "Welcome to TripPilot AI! To get started, create a new trip "
            "with your destination, dates, and preferences. I'll help you "
            "plan the perfect itinerary."
        )

    return ChatResponse(
        message=message,
        conversation_id=conversation_id,
    )
