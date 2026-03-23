import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import settings


class RateLimitStore:
    """In-memory rate limit store. In production, use Redis."""

    def __init__(self) -> None:
        self._store: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> tuple[bool, int]:
        """Check if a key is rate limited. Returns (is_limited, retry_after_seconds)."""
        now = time.time()
        window_start = now - window_seconds

        # Clean old entries
        self._store[key] = [t for t in self._store[key] if t > window_start]

        if len(self._store[key]) >= max_requests:
            # Calculate retry-after
            oldest = min(self._store[key]) if self._store[key] else now
            retry_after = int(oldest + window_seconds - now) + 1
            return True, max(1, retry_after)

        self._store[key].append(now)
        return False, 0

    def reset(self) -> None:
        """Reset all rate limit data."""
        self._store.clear()


# Global store instance
rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/api/health"):
            return await call_next(request)

        # Get client identifier
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        # Choose rate limit based on path
        if "/upload" in request.url.path:
            max_requests = settings.RATE_LIMIT_UPLOAD_PER_MINUTE
        else:
            max_requests = settings.RATE_LIMIT_PER_MINUTE

        key = f"rate:{client_ip}"
        is_limited, retry_after = rate_limit_store.is_rate_limited(key, max_requests, 60)

        if is_limited:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        return response
