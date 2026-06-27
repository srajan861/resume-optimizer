"""
Throttling layer for Groq API calls.
Ensures we never exceed Groq's 30 RPM (Requests Per Minute) limit.

This is a GLOBAL throttle (shared across all users) to protect the Groq API,
separate from per-user rate limiting which protects our API.
"""
import asyncio
import time
from typing import Callable, TypeVar, Any
from functools import wraps
from core.logging_config import get_logger

logger = get_logger("throttle")

# Groq API limits (free tier as of 2026)
GROQ_RPM_LIMIT = 30  # Requests per minute
GROQ_BUFFER = 5  # Safety buffer to avoid hitting limit

# Maximum concurrent Groq API calls
# Set to 25 (30 - 5 buffer) to stay under limit
MAX_CONCURRENT_GROQ_CALLS = GROQ_RPM_LIMIT - GROQ_BUFFER

# Global semaphore to limit concurrent Groq API calls
# This ensures we never exceed Groq's RPM limit
groq_semaphore = asyncio.Semaphore(MAX_CONCURRENT_GROQ_CALLS)

# Track Groq API call metrics
_call_metrics = {
    "total_calls": 0,
    "throttled_calls": 0,
    "failed_calls": 0,
    "last_reset": time.time(),
}


def reset_metrics_if_needed():
    """Reset metrics every hour for monitoring."""
    current_time = time.time()
    if current_time - _call_metrics["last_reset"] >= 3600:  # 1 hour
        logger.info(
            f"📊 Groq API metrics (last hour): "
            f"total={_call_metrics['total_calls']}, "
            f"throttled={_call_metrics['throttled_calls']}, "
            f"failed={_call_metrics['failed_calls']}"
        )
        _call_metrics["total_calls"] = 0
        _call_metrics["throttled_calls"] = 0
        _call_metrics["failed_calls"] = 0
        _call_metrics["last_reset"] = current_time


T = TypeVar('T')


def groq_throttle(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to throttle Groq API calls using a semaphore.
    
    This ensures that no more than MAX_CONCURRENT_GROQ_CALLS (25)
    Groq API calls are active at any given time, preventing us from
    exceeding Groq's 30 RPM limit.
    
    Usage:
        @groq_throttle
        async def my_groq_call():
            return await groq_client.chat.completions.create(...)
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        reset_metrics_if_needed()
        
        # Check if throttling is needed
        active_calls = MAX_CONCURRENT_GROQ_CALLS - groq_semaphore._value
        
        if active_calls >= MAX_CONCURRENT_GROQ_CALLS * 0.8:  # 80% capacity
            logger.warning(
                f"⏳ Groq API throttling: {active_calls}/{MAX_CONCURRENT_GROQ_CALLS} "
                f"calls active (80%+ capacity)"
            )
            _call_metrics["throttled_calls"] += 1
        
        # Acquire semaphore slot (will wait if all slots are taken)
        async with groq_semaphore:
            _call_metrics["total_calls"] += 1
            
            try:
                # Log when we're at high utilization
                if active_calls >= MAX_CONCURRENT_GROQ_CALLS * 0.9:
                    logger.warning(
                        f"🚨 High Groq API utilization: {active_calls}/{MAX_CONCURRENT_GROQ_CALLS} calls"
                    )
                
                # Make the actual API call
                result = await func(*args, **kwargs)
                return result
            
            except Exception as e:
                _call_metrics["failed_calls"] += 1
                logger.error(f"Groq API call failed: {type(e).__name__}: {e}")
                raise
    
    return wrapper


def get_groq_metrics() -> dict:
    """
    Get current Groq API call metrics.
    
    Returns:
        dict with total_calls, throttled_calls, failed_calls, available_slots
    """
    return {
        "total_calls": _call_metrics["total_calls"],
        "throttled_calls": _call_metrics["throttled_calls"],
        "failed_calls": _call_metrics["failed_calls"],
        "available_slots": groq_semaphore._value,
        "max_concurrent": MAX_CONCURRENT_GROQ_CALLS,
        "utilization_percent": round(
            ((MAX_CONCURRENT_GROQ_CALLS - groq_semaphore._value) / MAX_CONCURRENT_GROQ_CALLS) * 100,
            1
        ),
    }


async def wait_for_groq_capacity(min_slots: int = 5) -> None:
    """
    Wait until at least min_slots are available in the Groq semaphore.
    
    Useful for batch operations that need multiple API calls.
    
    Args:
        min_slots: Minimum number of available slots to wait for
    """
    while groq_semaphore._value < min_slots:
        logger.info(f"⏳ Waiting for Groq capacity: {groq_semaphore._value}/{MAX_CONCURRENT_GROQ_CALLS} available")
        await asyncio.sleep(0.5)  # Wait 500ms and check again


# Export for use in other modules
__all__ = [
    "groq_throttle",
    "get_groq_metrics",
    "wait_for_groq_capacity",
    "MAX_CONCURRENT_GROQ_CALLS",
    "GROQ_RPM_LIMIT",
]
