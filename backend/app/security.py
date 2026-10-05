"""Access control for a private, single-owner TripPilot installation."""
import secrets
import asyncio
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import JSONResponse
from app.config import get_settings


def require_access(credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))):
    key = get_settings().SECRET_KEY
    if len(key) < 32 or key in {"change-me-in-production", "supersecretkey"}:
        raise HTTPException(503, "Set a random SECRET_KEY of at least 32 characters on the server.")
    if credentials is None or not secrets.compare_digest(credentials.credentials.encode(), key.encode()):
        raise HTTPException(401, "Enter your access key in Settings.", headers={"WWW-Authenticate": "Bearer"})


class RequestLimitMiddleware:
    """Bound JSON bodies, including chunked requests, before parsing."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        body = bytearray()
        try:
            async with asyncio.timeout(15):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > 65536:
                        return await JSONResponse({"detail": "Request body too large"}, status_code=413)(scope, receive, send)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            return await JSONResponse({"detail": "Request body timed out"}, status_code=408)(scope, receive, send)
        delivered = False
        async def replay():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}
        await self.app(scope, replay, send)
