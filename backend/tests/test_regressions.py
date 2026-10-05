"""Run: python -m unittest discover -s tests -v.

Set TEST_DATABASE_URL to a disposable PostgreSQL database ending in _test or
_audit to include persistence, authorization, and background-job checks.
"""
import asyncio
import copy
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

from pydantic import ValidationError
from app.schemas.trip import TripCreate, TripUpdate
from app.schemas.chat import ModifyRequest
from app.schemas.itinerary import GeneratedItinerary
from app.agents.nodes.planner import _generate_rule_based_itinerary, itinerary_planner
from app.integrations.places_service import find_nearby_places

DATA = dict(origin="Delhi", destination="Tokyo", start_date="2027-01-02", end_date="2027-01-03", num_travelers=2, budget_amount=1000, budget_currency="USD", travel_style="balanced", preferences=[], additional_notes="Vegetarian")


class ValidationTests(unittest.IsolatedAsyncioTestCase):
    def test_trip_bounds_and_patch_nulls(self):
        for change in ({"origin": " "}, {"num_travelers": 0}, {"num_travelers": 21}, {"budget_amount": float("inf")}, {"budget_amount": -1}, {"travel_style": "invalid"}, {"budget_currency": "BAD"}, {"end_date": "2026-01-01"}, {"end_date": "2027-03-01"}, {"additional_notes": "x" * 4001}):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                TripCreate(**{**DATA, **change})
        self.assertEqual(TripCreate(**{**DATA, "end_date": DATA["start_date"]}).start_date.isoformat(), DATA["start_date"])
        for change in ({"origin": None}, {"preferences": None}, {"status": "generated"}):
            with self.assertRaises(ValidationError):
                TripUpdate(**change)
        with self.assertRaises(ValidationError):
            ModifyRequest(instruction="   ")

    def test_fallback_currency_group_costs_and_schedule(self):
        single = _generate_rule_based_itinerary({**DATA, "num_travelers": 1})
        group = _generate_rule_based_itinerary({**DATA, "budget_currency": "INR"})
        GeneratedItinerary.model_validate(group)
        self.assertEqual(group["currency"], "USD")
        cost = lambda plan: sum(a["estimated_cost"] for d in plan["days"] for a in d["activities"])
        self.assertEqual(cost(group), cost(single) * 2)
        self.assertEqual(sum(a["estimated_cost"] for d in group["days"] for a in d["activities"] if a["category"] == "accommodation"), 200)
        GeneratedItinerary.model_validate(_generate_rule_based_itinerary({**DATA, "end_date": DATA["start_date"]}))

    async def test_modification_failure_keeps_original(self):
        original = _generate_rule_based_itinerary(DATA)
        state = {**DATA, "steps_completed": [], "itinerary": original, "is_modification": True, "modification_instruction": "Add a museum"}
        expected = copy.deepcopy(original)
        with patch("app.agents.nodes.planner._try_llm_planning", AsyncMock(return_value=None)):
            with self.assertRaises(ValueError):
                await itinerary_planner(state)
        self.assertEqual(state["itinerary"], expected)

    async def test_overpass_injection_rejected_before_network(self):
        with self.assertRaises(ValueError):
            await find_nearby_places(1, 1, place_types=['tourism"];out;'])
        with self.assertRaises(ValueError):
            await find_nearby_places(float("nan"), 1)


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "Set TEST_DATABASE_URL for real PostgreSQL integration tests")
class APITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        url = os.environ["TEST_DATABASE_URL"]
        if not url.split("?")[0].endswith(("_test", "_audit")):
            raise RuntimeError("Use a disposable database ending in _test or _audit")
        os.environ["DATABASE_URL"] = url
        os.environ["SECRET_KEY"] = "test-access-key-01234567890123456789"
        from app.config import get_settings
        get_settings.cache_clear()
        from app.main import app
        from app.database import engine, Base
        import httpx
        self.app, self.engine = app, engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", headers={"Authorization": "Bearer " + os.environ["SECRET_KEY"]})
        self.ids = []

    async def asyncTearDown(self):
        from app.database import async_session_maker
        from app.models.trip import Trip
        from sqlalchemy import delete
        async with async_session_maker() as db:
            await db.execute(delete(Trip).where(Trip.id.in_(self.ids)))
            await db.commit()
        await self.client.aclose()
        await self.engine.dispose()

    async def create(self):
        response = await self.client.post("/api/trips/", json=DATA)
        self.assertEqual(response.status_code, 201, response.text)
        self.ids.append(UUID(response.json()["id"]))
        return response.json()

    async def test_access_validation_and_body_limits(self):
        for path in ("/api/trips/", "/api/destinations/search?q=Tokyo", f"/api/trips/{uuid4()}/status"):
            response = await self.client.get(path, headers={"Authorization": "Bearer wrong"})
            self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual((await self.client.get("/api/trips/?limit=100000")).status_code, 422)
        self.assertEqual((await self.client.post("/api/trips/", content=b"x" * 65537)).status_code, 413)
        response = await self.client.options("/api/trips/", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
        self.assertNotIn("access-control-allow-origin", response.headers)
        self.assertEqual((await self.client.get(f"/api/trips/{uuid4()}/status")).status_code, 404)

    async def test_trip_notes_patch_pagination_and_delete(self):
        trip = await self.create()
        self.assertEqual(trip["additional_notes"], "Vegetarian")
        path = "/api/trips/" + trip["id"]
        response = await self.client.patch(path, json={"preferences": ["nature"], "additional_notes": "No stairs", "destination": "Kyoto"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["additional_notes"], "No stairs")
        self.assertEqual(response.json()["title"], "Trip to Kyoto")
        self.assertEqual((await self.client.patch(path, json={"start_date": "2027-02-01"})).status_code, 422)
        self.assertEqual((await self.client.get(path)).json()["start_date"], DATA["start_date"])
        response = await self.client.get("/api/trips/?limit=1&skip=1")
        self.assertGreaterEqual(response.json()["total"], 1)
        self.assertEqual((await self.client.delete(path)).status_code, 204)
        self.assertEqual((await self.client.get(path)).status_code, 404)

    async def test_planning_race_failure_recovery_and_last_good_plan(self):
        from app.database import async_session_maker
        from app.models.conversation import AgentRun
        from app.models.trip import Trip
        from sqlalchemy import select
        trip = await self.create()
        path = "/api/trips/" + trip["id"]
        started, release = asyncio.Event(), asyncio.Event()
        plan = _generate_rule_based_itinerary(DATA)
        async def slow_plan(state):
            started.set()
            await release.wait()
            return {**state, "itinerary": plan}
        with patch("app.agents.graph.plan_trip", slow_plan):
            first = asyncio.create_task(self.client.post(path + "/generate"))
            await asyncio.wait_for(started.wait(), 10)
            try:
                self.assertEqual((await self.client.post(path + "/generate")).status_code, 409)
                self.assertEqual((await self.client.delete(path)).status_code, 409)
                self.assertEqual((await self.client.get(path + "/status")).json()["status"], "running")
            finally:
                release.set()
                self.assertEqual((await first).status_code, 202)
        self.assertEqual((await self.client.get(path)).json()["status"], "generated")
        with patch("app.agents.graph.plan_trip", AsyncMock(side_effect=RuntimeError("private SQL details"))):
            self.assertEqual((await self.client.post(path + "/modify", json={"instruction": "Add a museum"})).status_code, 202)
        status = (await self.client.get(path + "/status")).json()
        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["itinerary"], plan)
        self.assertNotIn("private SQL", status["error"])
        modified = copy.deepcopy(plan)
        modified["summary"] = "A museum visit added"
        with patch("app.agents.graph.plan_trip", AsyncMock(return_value={"itinerary": modified, "steps_completed": []})):
            await self.client.post(path + "/modify", json={"instruction": "Add a museum"})
        self.assertEqual((await self.client.get(path + "/status")).json()["itinerary"], modified)
        async with async_session_maker() as db:
            db.add(AgentRun(trip_id=UUID(trip["id"]), status="running", started_at=datetime.now(timezone.utc) - timedelta(minutes=7)))
            obj = await db.get(Trip, UUID(trip["id"]))
            obj.status = "planning"
            # Make this interrupted run the latest one while still stale.
            for run in (await db.scalars(select(AgentRun).where(AgentRun.trip_id == obj.id))).all():
                if run.status != "running":
                    run.started_at = datetime.now(timezone.utc) - timedelta(minutes=10)
            await db.commit()
        self.assertEqual((await self.client.get(path + "/status")).json()["status"], "failed")
        self.assertEqual((await self.client.get(path)).json()["status"], "error")

    async def test_edited_trip_does_not_restore_outdated_plan(self):
        trip = await self.create()
        path = "/api/trips/" + trip["id"]
        plan = _generate_rule_based_itinerary(DATA)
        with patch("app.agents.graph.plan_trip", AsyncMock(return_value={"itinerary": plan})):
            await self.client.post(path + "/generate")
        await self.client.patch(path, json={})
        self.assertEqual((await self.client.get(path)).json()["status"], "generated")
        await self.client.patch(path, json={"destination": "Kyoto"})
        with patch("app.agents.graph.plan_trip", AsyncMock(side_effect=RuntimeError("offline"))):
            await self.client.post(path + "/generate")
        status = (await self.client.get(path + "/status")).json()
        self.assertEqual(status["status"], "failed")
        self.assertIsNone(status["itinerary"])
        self.assertEqual((await self.client.post(path + "/modify", json={"instruction": "Add a museum"})).status_code, 409)


if __name__ == "__main__":
    unittest.main()
