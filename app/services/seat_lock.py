# app/services/seat_lock.py
import uuid
from fastapi import HTTPException, status

from app.core.redis import redis_client as redis


async def acquire_seat_lock(
    trip_id: int,
    seat_number: int,
    timeout: int = 10
) -> tuple[str, str]:
    """
    Acquire a distributed lock for a specific seat using Redis.
    Prevents race conditions during concurrent booking attempts.

    Args:
        trip_id: ID of the trip
        seat_number: Seat number in the bus
        timeout: Lock expiry in seconds (default: 10)

    Returns:
        Tuple of (lock_key, lock_value) if acquired

    Raises:
        HTTPException 409 if lock is already held by another request
    """
    lock_key = f"lock:seat:{trip_id}:{seat_number}"
    lock_value = str(uuid.uuid4())

    # SET with NX (only if not exists) and EX (expiry)
    acquired = await redis.set(lock_key, lock_value, nx=True, ex=timeout)

    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This seat is currently being processed by another request. Please try again in a few seconds."
        )

    return lock_key, lock_value


async def release_seat_lock(lock_key: str, lock_value: str) -> None:
    """
    Release the seat lock only if the current process still owns it.
    Prevents accidental release by expired or concurrent requests.
    """
    # Use Lua script for atomic compare-and-delete (recommended for production)
    lua_script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """
    await redis.eval(lua_script, 1, lock_key, lock_value)