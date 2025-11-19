# app/api/v1/endpoints/report.py
from fastapi import APIRouter, Depends
from app.core.dependencies import require_admin
from app.db.session import AsyncSessionLocal
from sqlalchemy import text
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin/reports", tags=["Reports"])

@router.get("/top-driver")
async def top_driver(_=Depends(require_admin)):
    """
    شناسایی فعال‌ترین (پرکارترین) راننده/اتوبوس بر اساس تعداد رزروها
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT b.plate_number, COUNT(*) as bookings
            FROM bookings bk
            JOIN seats s ON bk.seat_id = s.id
            JOIN trips t ON s.trip_id = t.id
            JOIN buses b ON t.bus_id = b.id
            WHERE (bk.status = 'confirmed' OR bk.status IS NULL)
            GROUP BY b.id, b.plate_number
            ORDER BY bookings DESC LIMIT 1
        """))
        row = result.fetchone()
        if not row:
            return {"message": "هیچ رزروی یافت نشد", "top_driver_bus": None, "total_bookings": 0}
        return {
            "top_driver_bus": row[0],
            "total_bookings": row[1],
            "message": f"اتوبوس {row[0]} با {row[1]} رزرو، فعال‌ترین اتوبوس است"
        }

@router.get("/bus-monthly-income")
async def bus_monthly_income(_=Depends(require_admin)):
    """
    تعداد رزروها و درآمد هر اتوبوس در هر ماه
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT 
                b.plate_number,
                TO_CHAR(DATE_TRUNC('month', bk.created_at), 'YYYY-MM') as month,
                COUNT(*) as bookings,
                SUM(bk.price_paid)::numeric(15,2) as income
            FROM bookings bk
            JOIN seats s ON bk.seat_id = s.id
            JOIN trips t ON s.trip_id = t.id
            JOIN buses b ON t.bus_id = b.id
            WHERE (bk.status = 'confirmed' OR bk.status IS NULL)
            GROUP BY b.id, b.plate_number, DATE_TRUNC('month', bk.created_at)
            ORDER BY month DESC, income DESC
        """))
        rows = result.fetchall()
        return {
            "data": [
                {
                    "bus": r[0],
                    "month": r[1],
                    "bookings": r[2],
                    "income": float(r[3]) if r[3] else 0
                }
                for r in rows
            ],
            "total_buses": len(set(r[0] for r in rows))
        }

@router.get("/hourly-success-bookings")
async def hourly_bookings(_=Depends(require_admin)):
    """
    تعداد رزروهای موفق در هر ساعت (از created_at استفاده می‌کند)
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT EXTRACT(HOUR FROM created_at)::int as hour, COUNT(*) as bookings
            FROM bookings 
            WHERE status = 'confirmed' OR status IS NULL
            GROUP BY hour 
            ORDER BY hour
        """))
        rows = result.fetchall()
        if not rows:
            return {"message": "هیچ رزروی یافت نشد", "data": []}
        return {
            "data": [{"hour": int(r[0]), "bookings": r[1]} for r in rows],
            "total": sum(r[1] for r in rows)
        }