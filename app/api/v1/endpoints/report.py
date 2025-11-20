# app/api/v1/endpoints/report.py
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import require_admin
from app.db.session import AsyncSessionLocal
from app.services.report_service import (
    get_current_hour_report,
    get_daily_hourly_breakdown_report,
    get_bus_monthly_income_report,
    get_hourly_booking_report,
    get_top_driver_report,
)


router = APIRouter(prefix="/admin/reports", tags=["Reports"])


@router.get("/top-driver")
async def top_driver(_=Depends(require_admin)):
    """
    Returns the most active bus (by number of confirmed bookings).
    """
    async with AsyncSessionLocal() as db:
        report = await get_top_driver_report(db)
        if not report:
            return {
                "message": "No bookings found",
                "top_driver_bus": None,
                "total_bookings": 0
            }

        return report


@router.get("/bus-monthly-income")
async def bus_monthly_income(_=Depends(require_admin)):
    """
    Monthly booking count and total income per bus.
    """
    async with AsyncSessionLocal() as db:
        return await get_bus_monthly_income_report(db)


@router.get("/hourly-success-bookings")
async def hourly_success_bookings(
    target_date: Optional[date] = Query(
        None, alias="date", description="Date in YYYY-MM-DD format"
    ),
    hour: Optional[int] = Query(
        None, ge=0, le=23, description="Hour block (0-23)"
    ),
    _=Depends(require_admin)
):
    """
    Flexible hourly booking report:
    - No params: shows current hour statistics for today.
    - Only date: returns 24-hour breakdown for that date.
    - Date + hour: returns the 60-minute window for that hour.
    """
    if hour is not None and target_date is None:
        raise HTTPException(
            status_code=400,
            detail="When 'hour' is provided, 'date' must also be provided."
        )

    async with AsyncSessionLocal() as db:
        if target_date is None:
            return await get_current_hour_report(db)

        if hour is None:
            return await get_daily_hourly_breakdown_report(db, target_date)

        return await get_hourly_booking_report(db, target_date=target_date, hour=hour)