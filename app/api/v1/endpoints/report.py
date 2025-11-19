# app/api/v1/endpoints/report.py
from fastapi import APIRouter, Depends
from app.core.dependencies import require_admin
from app.db.session import AsyncSessionLocal
from sqlalchemy import text


router = APIRouter(prefix="/admin/reports", tags=["Reports"])


@router.get("/top-driver")
async def top_driver(_=Depends(require_admin)):
    """
    Returns the most active bus (by number of confirmed bookings).
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT b.plate_number, COUNT(*) AS bookings
            FROM bookings bk
            JOIN seats s ON bk.seat_id = s.id
            JOIN trips t ON s.trip_id = t.id
            JOIN buses b ON t.bus_id = b.id
            WHERE bk.status = 'confirmed' OR bk.status IS NULL
            GROUP BY b.id, b.plate_number
            ORDER BY bookings DESC
            LIMIT 1
        """))

        row = result.fetchone()
        if not row:
            return {
                "message": "No bookings found",
                "top_driver_bus": None,
                "total_bookings": 0
            }

        return {
            "top_driver_bus": row.plate_number,
            "total_bookings": row.bookings,
            "message": f"Bus {row.plate_number} is the most active with {row.bookings:,} bookings"
        }


@router.get("/bus-monthly-income")
async def bus_monthly_income(_=Depends(require_admin)):
    """
    Monthly booking count and total income per bus.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT 
                b.plate_number,
                TO_CHAR(DATE_TRUNC('month', bk.created_at), 'YYYY-MM') AS month,
                COUNT(*) AS bookings,
                COALESCE(SUM(bk.price_paid), 0) AS income
            FROM bookings bk
            JOIN seats s ON bk.seat_id = s.id
            JOIN trips t ON s.trip_id = t.id
            JOIN buses b ON t.bus_id = b.id
            WHERE bk.status = 'confirmed' OR bk.status IS NULL
            GROUP BY b.id, b.plate_number, DATE_TRUNC('month', bk.created_at)
            ORDER BY month DESC, income DESC
        """))

        rows = result.fetchall()

        data = [
            {
                "bus": row.plate_number,
                "month": row.month,
                "bookings": row.bookings,
                "income": float(row.income or 0)
            }
            for row in rows
        ]

        return {
            "data": data,
            "total_buses": len({row.plate_number for row in rows}),
            "total_records": len(data)
        }


@router.get("/hourly-success-bookings")
async def hourly_success_bookings(
    date: str = None,  # Format: YYYY-MM-DD
    hour: int = None,  # 0-23
    _=Depends(require_admin)
):
    """
    Number of successful bookings per hour for a specific date.
    If date is provided, returns bookings for that date only.
    If hour is also provided, returns bookings for that specific hour only.
    """
    async with AsyncSessionLocal() as db:
        # Build query with proper parameter binding
        base_query = """
            SELECT 
                DATE(created_at AT TIME ZONE 'UTC') AS booking_date,
                EXTRACT(HOUR FROM created_at AT TIME ZONE 'UTC')::int AS hour,
                COUNT(*) AS bookings
            FROM bookings 
            WHERE (status = 'confirmed' OR status IS NULL)
        """
        params = {}
        conditions = []
        
        if date:
            conditions.append("DATE(created_at AT TIME ZONE 'UTC') = CAST(:date AS DATE)")
            params["date"] = date
            
        if hour is not None:
            conditions.append("EXTRACT(HOUR FROM created_at AT TIME ZONE 'UTC')::int = CAST(:hour AS INTEGER)")
            params["hour"] = hour
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += """
            GROUP BY booking_date, hour 
            ORDER BY booking_date DESC, hour
        """
        
        result = await db.execute(text(base_query), params)
        rows = result.fetchall()

        if not rows:
            return {
                "message": "No successful bookings found for the specified criteria",
                "data": [],
                "total": 0,
                "date": date,
                "hour": hour
            }

        data = [
            {
                "date": str(row.booking_date),
                "hour": int(row.hour),
                "bookings": row.bookings
            }
            for row in rows
        ]

        return {
            "data": data,
            "total": sum(row.bookings for row in rows),
            "date": date,
            "hour": hour,
            "peak_hour": max(data, key=lambda x: x["bookings"])["hour"] if data else None
        }