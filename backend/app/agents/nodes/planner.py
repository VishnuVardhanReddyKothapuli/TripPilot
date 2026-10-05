"""Itinerary planner node — generates a day-by-day itinerary using research data.

Falls back to a rule-based planner when no LLM is available.
"""
import logging
import re
from datetime import date, timedelta
from ..state import TripPlannerState

logger = logging.getLogger(__name__)

# ─── Cost estimation tables (per-person, per-day, in USD) ─────────────────────
BASE_COSTS = {
    "accommodation": {"budget": 40, "balanced": 100, "luxury": 250},
    "food_breakfast": {"budget": 5, "balanced": 12, "luxury": 30},
    "food_lunch": {"budget": 8, "balanced": 18, "luxury": 45},
    "food_dinner": {"budget": 12, "balanced": 25, "luxury": 60},
    "local_transport": {"budget": 5, "balanced": 15, "luxury": 40},
    "activity": {"budget": 0, "balanced": 15, "luxury": 35},
}


def _generate_rule_based_itinerary(state: TripPlannerState) -> dict:
    """Schedule researched places; keep missing research visible instead of inventing it."""
    destination = state["destination"]
    start, end = date.fromisoformat(state["start_date"]), date.fromisoformat(state["end_date"])
    num_days = (end - start).days + 1
    style = state.get("travel_style", "balanced")
    travelers = state.get("num_travelers", 1)
    attractions = list(state.get("attractions") or [])
    restaurants = list(state.get("restaurants") or [])
    restaurants.sort(key=lambda p: (not bool(re.search(r"local|traditional|specialt|famous|popular|known for", p.get("description", ""), re.I)), not bool(p.get("description"))))
    food_notes = (state.get("travel_research") or {}).get("food_notes", [])
    coords = (state.get("destination_info") or {}).get("coordinates", {})
    position = (coords.get("lat"), coords.get("lon"))
    days, visited = [], []
    meal_index = 0

    def activity(title, description, place, begin, finish, category, cost):
        hour, minute = map(int, begin.split(":"))
        end_hour, end_minute = map(int, finish.split(":"))
        return dict(title=title, description=description[:2000], location_name=place.get("name", destination),
                    latitude=place.get("lat"), longitude=place.get("lon"), start_time=begin, end_time=finish,
                    duration_minutes=(end_hour-hour)*60+end_minute-minute, category=category,
                    estimated_cost=cost*travelers, cost_currency="USD", data_source="estimated",
                    source_url=place.get("source_url"), notes=place.get("address", ""))

    def visit(begin, finish):
        nonlocal position
        if not attractions:
            return activity("Unscheduled time — more local research needed",
                            "No additional researched sights were found. Choose a nearby stop after checking a local guide; this block is not a confirmed recommendation.",
                            {}, begin, finish, "activity", 0)
        # Keep the guide's first highlight, then group nearby stops when coordinates exist.
        if visited and all(v is not None for v in position):
            attractions.sort(key=lambda p: sum((p[k]-v)**2 for k, v in zip(("lat", "lon"), position))
                             if p.get("lat") is not None and p.get("lon") is not None else float("inf"))
        place = attractions.pop(0)
        position = (place.get("lat"), place.get("lon"))
        visited.append(place["name"])
        detail = place.get("description") or f"Explore this mapped {place.get('type', 'sight').replace(':', ': ')}."
        detail += " Suggested visit window; check opening hours and tickets before going. Allow travel time between stops."
        return activity("Visit " + place["name"], detail, place, begin, finish, "sightseeing", BASE_COSTS["activity"][style])

    def meal(label, begin, finish):
        nonlocal meal_index
        place = restaurants[meal_index % len(restaurants)] if restaurants else {}
        note = food_notes[meal_index % len(food_notes)] if food_notes else ""
        meal_index += 1
        detail = place.get("description") or note or "Dish recommendations were unavailable from the travel guide. Check the menu for local specialties."
        if label == "Lunch" and food_notes and place.get("description"):
            detail += " Regional food to look for (availability at this venue is unconfirmed): " + food_notes[0]
        if place.get("cuisine"):
            detail += " Listed cuisine: " + place["cuisine"].replace(";", ", ") + "."
        detail += " Confirm today's menu, prices and dietary suitability with the restaurant."
        return activity(label + (" at " + place["name"] if place else " — choose a local restaurant"),
                        detail, place, begin, finish, "food", BASE_COSTS["food_" + label.lower()][style])

    for number in range(1, num_days + 1):
        current = start + timedelta(days=number-1)
        first, last = number == 1, number == num_days
        activities = []
        if first:
            activities.append(activity("Arrival and luggage drop", "Adjust this suggested arrival window to your actual booking. Ask your accommodation about luggage storage or early check-in.", {}, "08:00", "09:00", "transport", BASE_COSTS["local_transport"][style]*3))
        activities.append(meal("Breakfast", "09:00" if first else "08:00", "09:30" if first else "09:00"))
        activities.append(visit("10:00", "12:00"))
        activities.append(meal("Lunch", "12:30", "13:30"))
        activities.append(visit("14:00", "16:00"))
        if last and num_days > 1:
            activities.append(activity("Collect luggage and depart", "Arrange checkout and luggage storage in the morning. Adjust this departure window to your booked journey.", {}, "16:30", "18:30", "transport", BASE_COSTS["local_transport"][style]*3))
        else:
            activities.append(meal("Dinner", "18:30", "19:30"))
        if not last:
            activities.append(activity("Accommodation", "Suggested overnight stay; select and book your accommodation separately.", {}, "20:00", "23:59", "accommodation", BASE_COSTS["accommodation"][style]))
        stops = [a["location_name"] for a in activities if a["category"] == "sightseeing"]
        weather = next((w for w in (state.get("weather_data") or []) if w.get("date") == current.isoformat()), {})
        summary = " → ".join(stops) or "Local research is incomplete for this day."
        if weather.get("weather_description"):
            summary += " • Weather: " + weather["weather_description"]
        days.append(dict(day_number=number, date=current.isoformat(), title=f"Day {number} — {stops[0] if stops else destination}", summary=summary, activities=activities))
    highlights = ", ".join(visited[:8])
    summary = f"{num_days} days in {destination} for {travelers} traveler(s), at a {style} pace. "
    summary += f"Places to visit: {highlights}. " if highlights else "Named attractions could not be researched. "
    summary += "Stops are grouped by nearby coordinates where available, with gaps for transfers. Timings and costs are estimates; intercity fares and confirmed bookings are not included."
    if food_notes:
        summary += " Local food highlights are described in the food guide below."
    return {"summary": summary, "days": days, "currency": "USD"}


async def itinerary_planner(state: TripPlannerState) -> TripPlannerState:
    """Only report a modification as successful when the model produced a valid plan."""
    state["current_step"] = "itinerary_planner"
    itinerary = await _try_llm_planning(state)
    if itinerary is None:
        if state.get("is_modification"):
            raise ValueError("Modification requires a working Ollama model")
        itinerary = _generate_rule_based_itinerary(state)
    research = state.get("travel_research") or {}
    itinerary["food_guide"] = research.get("food_notes", [])
    itinerary["food_places"] = [
        {"name": p["name"], "description": p.get("description", ""), "source_url": p.get("source_url")}
        for p in (state.get("restaurants") or [])[:8]
    ]
    itinerary["research_sources"] = research.get("sources", [])
    warnings = []
    if not state.get("attractions"):
        warnings.append("Attraction research was unavailable. Sightseeing recommendations need further checking.")
    if not research.get("food_notes") and not any(p.get("description") for p in research.get("restaurants", [])):
        warnings.append("Local dish research was unavailable. No famous dish has been verified for this plan.")
    itinerary["research_warnings"] = warnings
    state["itinerary"] = itinerary
    state["steps_completed"].append("itinerary_planner")
    return state


async def _try_llm_planning(state: TripPlannerState) -> dict | None:
    import httpx
    from app.config import get_settings
    from app.prompts.templates import itinerary_generation_prompt, modification_prompt
    from app.schemas.itinerary import GeneratedItinerary

    settings = get_settings()
    if settings.LLM_PROVIDER != "ollama" or not settings.OLLAMA_MODEL:
        return None
    try:
        prompt = itinerary_generation_prompt(state)
        if state.get("is_modification"):
            prompt += "\n" + modification_prompt(state, state["modification_instruction"])
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(settings.OLLAMA_BASE_URL.rstrip("/") + "/api/chat", json={
                "model": settings.OLLAMA_MODEL, "stream": False,
                "format": GeneratedItinerary.model_json_schema(),
                "messages": [{"role": "user", "content": prompt}],
                "options": {"num_predict": 12000},
            })
            response.raise_for_status()
        itinerary = GeneratedItinerary.model_validate_json(response.json()["message"]["content"])
        start = date.fromisoformat(state["start_date"])
        count = (date.fromisoformat(state["end_date"]) - start).days + 1
        if len(itinerary.days) != count:
            raise ValueError("Incorrect day count")
        if state.get("attractions") and not state.get("is_modification"):
            researched_names = {p["name"].casefold() for p in state["attractions"]}
            scheduled_names = {a.location_name.casefold() for day in itinerary.days for a in day.activities
                               if a.category in {"sightseeing", "activity"}}
            if len(scheduled_names & researched_names) < min(count, len(researched_names)):
                raise ValueError("Plan omitted researched sights")
        for index, day in enumerate(itinerary.days):
            if day.day_number != index + 1 or day.date != start + timedelta(days=index):
                raise ValueError("Incorrect itinerary dates")
            for activity in day.activities:
                activity.cost_currency = state["budget_currency"]
                activity.data_source = "estimated"
                place = next((p for p in (state.get("attractions") or []) + (state.get("restaurants") or [])
                              if p["name"].casefold() == activity.location_name.casefold()), None)
                activity.source_url = place.get("source_url") if place else None
                if place:
                    activity.latitude, activity.longitude = place.get("lat"), place.get("lon")
        itinerary.currency = state["budget_currency"]
        return itinerary.model_dump(mode="json")
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        logger.warning("Model unavailable or returned an invalid itinerary")
        return None
