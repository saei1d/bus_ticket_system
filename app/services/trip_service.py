from typing import Optional, Literal, Dict, Any

from sqlalchemy import text

from app.db.session import AsyncSessionLocal


async def list_available_trips(
    origin: Optional[str],
    destination: Optional[str],
    sort: Literal["cheapest", "expensive"],
    page: int,
    per_page: int,
) -> Dict[str, Any]:
    base_filter = "WHERE 1=1"
    filter_params: Dict[str, Any] = {}

    if origin:
        base_filter += " AND r.origin = :origin"
        filter_params["origin"] = origin
    if destination:
        base_filter += " AND r.destination = :destination"
        filter_params["destination"] = destination

    count_query = f"""
        SELECT COUNT(*)
        FROM trips t
        JOIN routes r ON t.route_id = r.id
        {base_filter}
    """

    data_query = f"""
        SELECT t.id,
               r.origin,
               r.destination,
               t.departure_time,
               t.price,
               b.capacity,
               (b.capacity - COUNT(s.id) FILTER (WHERE s.is_reserved)) AS available_seats
        FROM trips t
        JOIN routes r ON t.route_id = r.id
        JOIN buses b ON t.bus_id = b.id
        LEFT JOIN seats s ON s.trip_id = t.id AND s.is_reserved = true
        {base_filter}
        GROUP BY t.id, r.origin, r.destination, b.capacity
        ORDER BY t.price {"ASC" if sort == "cheapest" else "DESC"}
        LIMIT :limit OFFSET :offset
    """

    async with AsyncSessionLocal() as db:
        total_result = await db.execute(text(count_query), filter_params)
        total = total_result.scalar() or 0

        data_params = {**filter_params, "limit": per_page, "offset": (page - 1) * per_page}
        result = await db.execute(text(data_query), data_params)
        trips = result.fetchall()

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [
            {
                "trip_id": t.id,
                "origin": t.origin,
                "destination": t.destination,
                "departure": t.departure_time,
                "price": int(t.price),
                "available_seats": t.available_seats,
            }
            for t in trips
        ],
    }

