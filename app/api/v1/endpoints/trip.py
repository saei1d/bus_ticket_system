# app/api/v1/endpoints/trip.py
from fastapi import APIRouter, Query
from app.core.redis import redis_client as redis
import json
from typing import Optional

from app.services.trip_service import list_available_trips

router = APIRouter(prefix="/trips", tags=["Trips"])

@router.get("/available")
async def get_available_trips(
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    sort: str = Query("cheapest", regex="^(cheapest|expensive)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    cache_key = f"trips:{origin or '*'}:{destination or '*'}:{sort}:{page}:{per_page}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    response = await list_available_trips(
        origin=origin,
        destination=destination,
        sort=sort,
        page=page,
        per_page=per_page,
    )

    await redis.setex(cache_key, 60, json.dumps(response, default=str))
    return response