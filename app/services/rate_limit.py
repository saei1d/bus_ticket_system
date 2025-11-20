# app/services/rate_limit.py
from datetime import datetime

from fastapi import HTTPException, status

from app.core.redis import redis_client as redis


async def check_daily_limit(user_id: int) -> None:
    """
    Check if the user has reached the daily booking limit (20 bookings per day).
    This function only checks — increment is performed separately after successful booking.
    """
    key = f"daily_limit:{user_id}:{datetime.now().date()}"
    current = await redis.get(key)

    count = int(current) if current is not None else 0

    if count >= 20:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have reached the daily booking limit of 20 reservations."
        )


async def increment_daily_limit(user_id: int) -> None:
    """
    Increment the user's daily booking counter.
    Must be called only after a booking has been successfully confirmed in the database.
    Sets a 24-hour expiry on first use.
    """
    key = f"daily_limit:{user_id}:{datetime.now().date()}"

    current = await redis.get(key)

    if current is None:
        # First booking today — initialize counter with 24h TTL
        await redis.setex(key, 86_400, "1")
    else:
        await redis.incr(key)


async def check_rate_limit(
    identifier: str,
    limit: int,
    window_seconds: int = 60,
    *,
    resource: str = "request"
) -> None:
    """
    Generic sliding-window rate limiter (e.g., for login attempts, SMS, or API calls).

    Args:
        identifier: Unique identifier (e.g., IP address, mobile number)
        limit: Maximum allowed requests in the time window
        window_seconds: Time window in seconds (default: 60)
        resource: Human-readable name of the resource being limited (for error message)

    Raises:
        HTTPException 429 if limit exceeded
    """
    key = f"rate_limit:{identifier}:{resource}"
    current = await redis.get(key)

    count = int(current) if current is not None else 0

    if count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many {resource}s. Please try again in {window_seconds} seconds."
        )

    # Increment counter and set expiry on first request
    if current is None:
        await redis.setex(key, window_seconds, "1")
    else:
        await redis.incr(key)