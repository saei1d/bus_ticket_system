# app/services/rate_limit.py
from app.core.redis import redis_client as redis
from fastapi import HTTPException
from datetime import datetime, timedelta

async def check_daily_limit(user_id: int):
    key = f"daily_limit:{user_id}:{datetime.now().date()}"
    current = await redis.get(key)
    if current is None:
        await redis.setex(key, 86400, 1)  # 24 ساعت
        return
    count = int(current)
    if count >= 20:
        raise HTTPException(429, "حداکثر ۲۰ رزرو در روز مجاز است")
    await redis.incr(key)