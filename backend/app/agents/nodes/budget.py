from ..state import TripPlannerState

def budget_calculator(state: TripPlannerState) -> TripPlannerState:
    state["current_step"] = "budget_calculator"
    
    itinerary = state.get("itinerary", {})
    days = itinerary.get("days", [])
    
    total_cost = 0
    categories = {"accommodation": 0, "food": 0, "transport": 0, "activities": 0}
    
    for day in days:
        for activity in day.get("activities", []):
            cost = activity.get("estimated_cost", 0)
            total_cost += cost
            cat = activity.get("category", "other")
            if cat in categories:
                categories[cat] += cost
            else:
                categories["activities"] += cost
                
    state["budget_breakdown"] = {
        "total_cost": total_cost,
        "categories": categories
    }
    
    if "optimization_attempts" not in state:
        state["optimization_attempts"] = 0
        
    state["steps_completed"].append("budget_calculator")
    return state