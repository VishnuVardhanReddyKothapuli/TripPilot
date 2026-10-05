import logging
import time
import asyncio
from typing import Dict, Any, Optional, Callable
import httpx
from functools import wraps

logger = logging.getLogger(__name__)

def simple_cache(ttl_seconds: int):
    """Simple in-memory TTL cache decorator"""
    cache: Dict[str, Dict[str, Any]] = {}
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            now = time.monotonic()
            if key in cache and now - cache[key]["timestamp"] < ttl_seconds:
                return cache[key]["value"]
            result = await func(*args, **kwargs)
            # ponytail: bounded per-process cache; use shared storage only for multiple workers.
            if len(cache) >= 256:
                cache.pop(next(iter(cache)))
            cache[key] = {"value": result, "timestamp": now}
            return result
        return async_wrapper
    return decorator

class BaseAPIClient:
    """Base API client with retry logic, rate limiting helper, and logging."""
    def __init__(self, base_url: str, timeout: float = 10.0, max_retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        self.last_request_time = 0.0
        
    async def _rate_limit_delay(self, min_delay: float):
        """Helper to ensure at least min_delay seconds between requests."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < min_delay:
            await asyncio.sleep(min_delay - elapsed)
        self.last_request_time = time.time()

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                  rate_limit_delay: float = 0.0) -> Optional[Dict[str, Any]]:
        """Perform a GET request with exponential backoff retries."""
        for attempt in range(self.max_retries):
            try:
                if rate_limit_delay > 0:
                    await self._rate_limit_delay(rate_limit_delay)
                
                logger.debug("Request to external integration")
                response = await self.client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    break
            except httpx.RequestError as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
            
            if attempt < self.max_retries - 1:
                delay = 2 ** attempt
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                
        logger.error(f"Failed to fetch {endpoint} after {self.max_retries} attempts")
        return None

    async def close(self):
        await self.client.aclose()
