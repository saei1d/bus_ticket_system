"""
High-level helpers for report endpoints.
Includes caching so repeated heavy queries do not hit the database every time.
"""
import json
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client as redis
from app.services.report_queries import (
    BUS_MONTHLY_INCOME_QUERY,
    DAILY_HOURLY_BREAKDOWN_QUERY,
    HOURLY_BOOKINGS_QUERY,
    TOP_DRIVER_QUERY,
)

CACHE_TTL_SECONDS = 60


async def _get_cached_report(key: str) -> Optional[Dict[str, Any]]:
    if not redis:
        return None
    try:
        cached = await redis.get(key)
        if cached:
            return json.loads(cached)
    except Exception:
        return None
    return None


async def _set_cached_report(key: str, data: Dict[str, Any]) -> None:
    if not redis:
        return
    try:
        await redis.set(key, json.dumps(data), ex=CACHE_TTL_SECONDS)
    except Exception:
        pass


async def get_top_driver_report(db: AsyncSession) -> Optional[Dict[str, Any]]:
    cache_key = "report:top-driver"
    cached = await _get_cached_report(cache_key)
    if cached is not None:
        return cached

    result = await db.execute(TOP_DRIVER_QUERY)
    row = result.fetchone()
    if not row:
        return None

    report = {
        "top_driver_bus": row.plate_number,
        "total_bookings": row.bookings,
        "message": f"Bus {row.plate_number} is the most active with {row.bookings:,} bookings",
    }
    await _set_cached_report(cache_key, report)
    return report


async def get_bus_monthly_income_report(db: AsyncSession) -> Dict[str, Any]:
    cache_key = "report:bus-monthly-income"
    cached = await _get_cached_report(cache_key)
    if cached is not None:
        return cached

    result = await db.execute(BUS_MONTHLY_INCOME_QUERY)
    rows = result.fetchall()
    data = [
        {
            "bus": row.plate_number,
            "month": row.month,
            "bookings": row.bookings,
            "income": float(row.income or 0),
        }
        for row in rows
    ]
    report = {
        "data": data,
        "total_buses": len({row.plate_number for row in rows}),
        "total_records": len(data),
    }
    await _set_cached_report(cache_key, report)
    return report


async def get_hourly_booking_report(
    db: AsyncSession,
    target_date: date,
    hour: int,
) -> Dict[str, Any]:
    cache_key = f"report:hourly:{target_date}:{hour}"
    cached = await _get_cached_report(cache_key)
    if cached is not None:
        return cached

    start_dt = datetime.combine(target_date, time(hour=hour, tzinfo=timezone.utc))
    end_dt = start_dt + timedelta(hours=1)

    result = await db.execute(
        HOURLY_BOOKINGS_QUERY,
        {"start_ts": start_dt, "end_ts": end_dt},
    )
    total = result.scalar() or 0
    next_hour = (hour + 1) % 24
    end_date = target_date if hour < 23 else target_date + timedelta(days=1)

    report = {
        "date": str(target_date),
        "end_date": str(end_date),
        "hour_start": hour,
        "hour_end": next_hour,
        "start_time_utc": start_dt.isoformat(),
        "end_time_utc": end_dt.isoformat(),
        "window_label": f"{hour:02d}:00-{next_hour:02d}:00",
        "bookings": total,
    }
    await _set_cached_report(cache_key, report)
    return report


async def get_daily_hourly_breakdown_report(
    db: AsyncSession,
    target_date: date,
) -> Dict[str, Any]:
    cache_key = f"report:hourly-breakdown:{target_date}"
    cached = await _get_cached_report(cache_key)
    if cached is not None:
        return cached

    result = await db.execute(
        DAILY_HOURLY_BREAKDOWN_QUERY,
        {"target_date": target_date},
    )
    rows = result.fetchall()
    counts = {int(row.hour): row.bookings for row in rows}

    hours_data = [
        {
            "hour": hour,
            "window_label": f"{hour:02d}:00-{(hour + 1) % 24:02d}:00",
            "bookings": counts.get(hour, 0),
        }
        for hour in range(24)
    ]
    total = sum(entry["bookings"] for entry in hours_data)
    peak_entry = max(hours_data, key=lambda x: x["bookings"]) if hours_data else None

    report = {
        "date": str(target_date),
        "hours": hours_data,
        "total_bookings": total,
        "peak_hour": peak_entry["hour"] if peak_entry else None,
    }
    await _set_cached_report(cache_key, report)
    return report


async def get_current_hour_report(db: AsyncSession) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    target_date = now.date()
    hour = now.hour
    return await get_hourly_booking_report(db, target_date=target_date, hour=hour)

