"""A sequential planner: no graph/checkpoint framework is needed for this flow."""
from .nodes.research import destination_research, weather_research, attraction_research
from .nodes.planner import itinerary_planner
from .nodes.budget import budget_calculator


async def plan_trip(state):
    state["steps_completed"] = ["collect_preferences", "validate_preferences"]
    for step in (destination_research, weather_research, attraction_research, itinerary_planner):
        state = await step(state)
    state = budget_calculator(state)
    state["steps_completed"].extend(["validate_itinerary", "generate_final_response"])
    return state
