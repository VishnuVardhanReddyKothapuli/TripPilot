"""CORS checks without a database connection: python -m unittest discover -s tests -p test_cors.py -v."""
import unittest

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings


class CORSTests(unittest.IsolatedAsyncioTestCase):
    async def test_preflight_for_exact_and_loopback_origins(self):
        for environment in ("development", "production"):
            settings = Settings(_env_file=None, DATABASE_URL="postgresql://unused/test", APP_ENV=environment,
                                FRONTEND_URL="http://localhost:3000/", CORS_ORIGINS=" https://trips.example.com/ ")
            app = FastAPI()
            app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                               allow_methods=["GET", "POST", "PATCH", "DELETE"],
                               allow_headers=["Content-Type", "Authorization"])
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://api") as client:
                for origin in ("http://localhost:3000", "http://127.0.0.1:3000", "http://[::1]:3000", "https://trips.example.com", "http://localhost:3001", "https://evil.example", "http://localhost.evil.example:3000"):
                    allowed = origin in {"http://localhost:3000", "https://trips.example.com"} or (
                        environment == "development" and origin in {"http://127.0.0.1:3000", "http://[::1]:3000"})
                    with self.subTest(environment=environment, origin=origin):
                        response = await client.options("/api/trips/", headers={
                            "Origin": origin, "Access-Control-Request-Method": "GET",
                            "Access-Control-Request-Headers": "authorization,content-type"})
                        self.assertEqual(response.status_code, 200 if allowed else 400)
                        self.assertEqual(response.headers.get("access-control-allow-origin"), origin if allowed else None)

    def test_other_ports_require_explicit_configuration(self):
        settings = Settings(_env_file=None, DATABASE_URL="postgresql://unused/test", APP_ENV="production",
                            FRONTEND_URL="https://trips.example.com", CORS_ORIGINS="http://localhost:3001")
        self.assertEqual(settings.cors_origins, ["http://localhost:3001", "https://trips.example.com"])
