"""
Production-grade rate limiting using SlowAPI.
Simple, reliable, and battle-tested.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from core.logging_config import get_logger

logger = get_logger("rate_limiter")

# Initialize SlowAPI limiter with IP-based key function
limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    Returns a clean JSON response with retry information.
    """
    logger.warning(
        f"Rate limit exceeded: {request.client.host if request.client else 'unknown'} "
        f"on {request.url.path}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. {exc.detail}",
            "retry_after": "Please wait a few minutes before trying again",
        },
        headers={"Retry-After": "60"},  # Suggest retry after 60 seconds
    )


# Rate limit strings for different endpoint types
# Format: "X per Y" where Y can be: second, minute, hour, day
# ALIGNED WITH GROQ API LIMITS (30 RPM free tier)

RATE_LIMITS = {
    # Expensive AI operations (multiple Groq calls)
    "ai_heavy": "8/hour",       # Full analysis (6-7 Groq calls per request)
    "ai_medium": "15/hour",     # Cover letters, skill gaps (1 Groq call each)
    "ai_light": "20/hour",      # Auto-edit, rewrite (1 Groq call each)
    
    # File operations
    "upload": "20/hour",        # Resume uploads
    "download": "100/hour",     # File downloads
    
    # General API calls
    "api": "100/minute",        # Regular API endpoints
    
    # Auth operations (prevent brute force)
    "auth": "10/5minutes",      # Login attempts
}


# NOTE: Rate limits are aligned with Groq's 30 RPM limit
# - ai_heavy: 8 req/hr × 7 calls = 56 calls/hr (~1 call/min per user)
# - With 10 concurrent users: ~10-20 calls/min (safe under 30 RPM)
# - Throttling layer ensures we never exceed Groq's limit globally


def get_rate_limit(limit_type: str = "api") -> str:
    """
    Get rate limit string for a specific endpoint type.
    
    Args:
        limit_type: Type of rate limit (ai_heavy, ai_medium, upload, etc.)
    
    Returns:
        Rate limit string in format "X/timeperiod"
    """
    return RATE_LIMITS.get(limit_type, RATE_LIMITS["api"])
