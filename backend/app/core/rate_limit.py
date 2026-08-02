"""
Simple sliding-window rate limiter backed by Redis.

Applied as FastAPI middleware, keyed by client IP (+ optionally user id
once authenticated). This is intentionally simple; swap for a proper
token-bucket implementation (e.g. via slowapi) if you need finer control.
"""
import time

import redis.asyncio as redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}:{int(time.time() // 60)}"

        try:
            r = get_redis()
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 60)

            if count > settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again shortly."},
                )
        except Exception:
            # If Redis is unavailable, fail open rather than blocking all traffic.
            pass

        return await call_next(request)
