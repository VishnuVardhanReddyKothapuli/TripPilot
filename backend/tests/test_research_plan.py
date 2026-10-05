import unittest
from unittest.mock import AsyncMock, patch
from app.integrations.travel_guide_service import GuideParser, research_destination
from app.integrations.places_service import find_attractions
from app.agents.nodes.planner import itinerary_planner
from app.schemas.itinerary import GeneratedItinerary


class ResearchPlanTests(unittest.IsolatedAsyncioTestCase):
    async def test_guide_to_plan_keeps_places_dishes_and_sources(self):
        parser = GuideParser()
        parser.feed('''<h2 id="See">See</h2><li><bdi class="vcard">
          <span class="listing-name">Amber Fort</span><abbr class="latitude">26.98</abbr>
          <abbr class="longitude">75.85</abbr><bdi class="listing-content">Explore the palace courtyards.</bdi>
          </bdi></li><h2 id="Eat">Eat</h2><p>Try <b>dal baati churma</b>.<sup class="reference">[1]</sup></p>
          <li><bdi class="vcard"><span class="listing-name">Local Kitchen</span>
          <bdi class="listing-content">Known for dal baati churma.</bdi></bdi></li>
          <div class="reflist"><ol><li>Do not show reference bibliography.</li></ol></div>''')
        self.assertEqual(parser.food_notes, ["Try dal baati churma."])
        self.assertEqual(parser.attractions[0]["lat"], 26.98)
        self.assertEqual(parser.restaurants[0]["name"], "Local Kitchen")
        source = "https://en.wikivoyage.org/wiki/Jaipur"
        for place in parser.attractions + parser.restaurants:
            place["source_url"] = source
        state = dict(destination="Jaipur", origin="Delhi", start_date="2027-01-02", end_date="2027-01-02",
                     travel_style="balanced", num_travelers=2, attractions=parser.attractions,
                     restaurants=parser.restaurants, steps_completed=[], travel_research={
                         "food_notes": parser.food_notes, "restaurants": parser.restaurants,
                         "sources": [{"title": "Jaipur guide", "url": source}]})
        with patch("app.agents.nodes.planner._try_llm_planning", AsyncMock(return_value=None)):
            plan = (await itinerary_planner(state))["itinerary"]
        GeneratedItinerary.model_validate(plan)
        activities = plan["days"][0]["activities"]
        visit = next(a for a in activities if a["category"] == "sightseeing")
        self.assertEqual(visit["source_url"], source)
        self.assertIn("courtyards", visit["description"])
        self.assertTrue(any("dal baati churma" in a["description"] for a in activities if a["category"] == "food"))
        self.assertIn("Amber Fort", plan["summary"])
        self.assertEqual(plan["research_sources"][0]["url"], source)

    async def test_missing_research_is_explicit(self):
        state = dict(destination="Unknown", start_date="2027-01-02", end_date="2027-01-02", steps_completed=[])
        with patch("app.agents.nodes.planner._try_llm_planning", AsyncMock(return_value=None)):
            plan = (await itinerary_planner(state))["itinerary"]
        self.assertEqual(len(plan["research_warnings"]), 2)
        self.assertFalse(any(a["category"] == "sightseeing" for a in plan["days"][0]["activities"]))

    async def test_overpass_includes_area_landmarks_and_excludes_hotels(self):
        payload = {"elements": [
            {"id": 1, "type": "way", "center": {"lat": 12, "lon": 77}, "tags": {"name": "Palace", "historic": "palace"}},
            {"id": 2, "type": "node", "lat": 12, "lon": 77, "tags": {"name": "Hotel", "tourism": "hotel"}},
        ]}
        with patch("app.integrations.places_service.client.get", AsyncMock(return_value=payload)) as request:
            places = await find_attractions(12.123, 77.456)
        self.assertEqual([p.name for p in places], ["Palace"])
        self.assertEqual(places[0].latitude, 12)
        self.assertEqual(places[0].source_url, "https://www.openstreetmap.org/way/1")
        self.assertIn("nwr", request.call_args.kwargs["params"]["data"])

    async def test_cuisine_sources_are_preserved_when_guide_is_empty(self):
        empty = {"attractions": [], "restaurants": [], "food_notes": [], "sources": []}
        cuisine = {"food_notes": ["Try dosa."], "source": {"title": "Cuisine", "url": "https://en.wikipedia.org/wiki/Chennai#Cuisine"}}
        with patch("app.integrations.travel_guide_service._research_travel_guide", AsyncMock(return_value=empty)), patch("app.integrations.travel_guide_service._research_cuisine", AsyncMock(return_value=cuisine)):
            result = await research_destination("Test cuisine destination")
        self.assertEqual(result["food_notes"], ["Try dosa."])
        self.assertEqual(result["sources"], [cuisine["source"]])
