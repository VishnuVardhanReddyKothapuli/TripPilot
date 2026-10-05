from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class ChatRequest(BaseModel):
    trip_id: Optional[UUID] = None
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[UUID] = None


class AgentStep(BaseModel):
    node_name: str
    status: str  # pending, running, completed, failed
    message: str
    timestamp: Optional[datetime] = None


class AgentStatusResponse(BaseModel):
    status: str  # pending, running, completed, failed
    run_id: Optional[str] = None
    current_node: Optional[str] = None
    steps: List[AgentStep] = []
    itinerary: Optional[dict] = None  # The generated itinerary if completed
    error: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None
    agent_status: Optional[AgentStatusResponse] = None


class ModifyRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    instruction: str = Field(min_length=1, max_length=4000)
