# app/services/rate_limit.py
from app.core.redis import redis_client as redis
from fastapi import HTTPException
from datetime import datetime

async def check_daily_limit(user_id: int):
    """
    Check if user can make a booking (hasn't reached daily limit of 20).
    Only checks, doesn't increment. Increment should be done after successful booking.
    """
    key = f"daily_limit:{user_id}:{datetime.now().date()}"
    current = await redis.get(key)
    
    if current is None:
        count = 0
    else:
        count = int(current)
    
    # Check if limit reached - allow up to 20 bookings (count 0-19 = 20 total)
    if count >= 20:
        raise HTTPException(
            status_code=429,
            detail="حداکثر ۲۰ رزرو در روز مجاز است"
        )
    
    return True


async def increment_daily_limit(user_id: int):
    """
    Increment daily booking counter after successful booking.
    Should only be called after booking is confirmed in database.
    """
    key = f"daily_limit:{user_id}:{datetime.now().date()}"
    current = await redis.get(key)
    
    if current is None:
        # First booking of the day - set with 24 hour expiry
        await redis.setex(key, 86400, "1")
    else:
        # Increment existing counter
        await redis.incr(key)


async def check_rate_limit(identifier: str, limit: int, window_seconds: int = 60):
    """
    Generic rate limiter for IP or phone number.
    Args:
        identifier: IP address or phone number
        limit: Maximum number of requests
        window_seconds: Time window in seconds (default: 60 for 1 minute)
    """
    key = f"rate_limit:{identifier}"
    current = await redis.get(key)
    
    if current is None:
        await redis.setex(key, window_seconds, "0")
        count = 0
    else:
        count = int(current)
    
    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"تعداد درخواست‌ها بیش از حد مجاز است. لطفاً {window_seconds} ثانیه صبر کنید."
        )
    
    await redis.incr(key)
    return True