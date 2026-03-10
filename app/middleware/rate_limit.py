# app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

def create_limiter():
    """Create and configure rate limiter"""
    settings = get_settings()
    
    if not settings.rate_limit_enabled:
        # Return a dummy limiter that doesn't actually limit
        return Limiter(
            key_func=lambda: "dummy",
            default_limits=[],
            enabled=False
        )
    
    # Create limiter with Redis backend
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_requests_per_minute} per minute"],
        storage_uri=settings.rate_limit_redis_url,
        enabled=True
    )
    
    return limiter

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded for IP: {get_remote_address(request)}")
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Please try again in {exc.retry_after} seconds.",
            "retry_after": exc.retry_after
        },
        headers={"Retry-After": str(exc.retry_after)}
    )