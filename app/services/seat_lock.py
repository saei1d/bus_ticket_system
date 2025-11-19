# app/services/seat_lock.py
import uuid
from app.core.redis import redis_client as redis
from fastapi import HTTPException

async def acquire_seat_lock(trip_id: int, seat_number: int, timeout: int = 10):
    lock_key = f"lock:seat:{trip_id}:{seat_number}"
    lock_value = str(uuid.uuid4())
    acquired = await redis.set(lock_key, lock_value, nx=True, ex=timeout)
    if not acquired:
        raise HTTPException(409, "صندلی در حال پردازش است، لطفاً دوباره تلاش کنید")
    return lock_key, lock_value

async def release_seat_lock(lock_key: str, lock_value: str):
    current = await redis.get(lock_key)
    if current == lock_value:
        await redis.delete(lock_key)