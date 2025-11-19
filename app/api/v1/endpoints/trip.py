# app/api/v1/endpoints/trip.py
from fastapi import APIRouter, Query
from app.core.redis import redis_client as redis
import json

router = APIRouter(prefix="/trips", tags=["Trips"])

@router.get("/available")
async def get_available_trips(
    origin: str = Query(None),
    destination: str = Query(None),
    sort: str = Query("cheapest", regex="^(cheapest|expensive)$")
):
    cache_key = f"trips:{origin or '*'}:{destination or '*'}:{sort}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text

    query = """
        SELECT t.id, r.origin, r.destination, t.departure_time, t.price, b.capacity,
               (b.capacity - COUNT(s.id) FILTER (WHERE s.is_reserved)) as available_seats
        FROM trips t
        JOIN routes r ON t.route_id = r.id
        JOIN buses b ON t.bus_id = b.id
        LEFT JOIN seats s ON s.trip_id = t.id AND s.is_reserved = true
        WHERE 1=1
    """
    params = {}
    if origin:
        query += " AND r.origin = :origin"
        params["origin"] = origin
    if destination:
        query += " AND r.destination = :destination"
        params["destination"] = destination

    query += " GROUP BY t.id, r.origin, r.destination, b.capacity"
    query += " ORDER BY t.price ASC" if sort == "cheapest" else " ORDER BY t.price DESC"

    async with AsyncSessionLocal() as db:
        result = await db.execute(text(query), params)
        trips = result.fetchall()

    response = [
        {
            "trip_id": t.id,
            "origin": t.origin,
            "destination": t.destination,
            "departure": t.departure_time,
            "price": int(t.price),
            "available_seats": t.available_seats
        }
        for t in trips
    ]

    await redis.setex(cache_key, 60, json.dumps(response, default=str))
    return response