from typing import TypedDict, Optional

class TripPlannerState(TypedDict):
    trip_id: str
    origin: str
    destination: str
    start_date: str
    end_date: str
    num_travelers: int
    budget_amount: float
    budget_currency: str
    travel_style: str  # budget/balanced/luxury
    preferences: list[str]  # adventure, nature, food, etc.
    additional_notes: Optional[str]
    
    destination_info: Optional[dict]  # country info, coordinates
    weather_data: Optional[list[dict]]
    attractions: Optional[list[dict]]
    restaurants: Optional[list[dict]]
    travel_research: Optional[dict]
    
    itinerary: Optional[dict]  # structured itinerary
    budget_breakdown: Optional[dict]
    
    messages: list
    current_step: str
    steps_completed: list[str]
    errors: list[str]
    needs_clarification: bool
    clarification_question: Optional[str]
    
    modification_instruction: Optional[str]
    is_modification: bool
    optimization_attempts: int
