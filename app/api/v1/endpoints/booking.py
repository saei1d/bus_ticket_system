# app/api/v1/endpoints/booking.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from app.schemas.booking import ReserveRequest
from app.services.booking_service import reserve_seat
from app.core.dependencies import get_current_user
from app.db.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import text
from datetime import datetime, timezone

router = APIRouter(prefix="/booking", tags=["Booking"])


# ۱. رزرو صندلی (کاملاً امن با Redis Lock + Rate Limit)
@router.post("/reserve", status_code=status.HTTP_201_CREATED)
async def reserve(
    request: ReserveRequest,
    current_user: User = Depends(get_current_user)
):
    result = await reserve_seat(
        user_id=current_user.id,
        trip_id=request.trip_id,
        seat_number=request.seat_number
    )
    return {
        "message": "بلیط با موفقیت رزرو شد",
        "booking_id": result["booking_id"],
        "trip_id": request.trip_id,
        "seat_number": request.seat_number,
        "price_paid": result["price"]
    }


# ۲. تابع پس‌زمینه برای بازگشت پول (BackgroundTasks — دقیقاً خواسته سعید شجاعی)
async def refund_money(booking_id: int, amount: int, user_id: int):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # بازگشت پول به کیف پول
            await db.execute(
                text("UPDATE wallets SET balance = balance + :amount WHERE user_id = :uid"),
                {"amount": amount, "uid": user_id}
            )
            # لغو بلیط
            await db.execute(
                text("UPDATE bookings SET status = 'cancelled' WHERE id = :bid"),
                {"bid": booking_id}
            )
            # آزاد کردن صندلی
            await db.execute(
                text("UPDATE seats SET is_reserved = false WHERE id = (SELECT seat_id FROM bookings WHERE id = :bid)"),
                {"bid": booking_id}
            )


# ۳. لیست تمام رزروهای کاربر (حالا ۱۰۰٪ کار می‌کنه!)
@router.get("/my-bookings")
async def my_bookings(current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        query = text("""
            SELECT 
                b.id,
                r.origin,
                r.destination,
                t.departure_time,
                s.seat_number,
                b.price_paid,
                b.status,
                t.departure_time > NOW() AT TIME ZONE 'UTC' AS can_cancel
            FROM bookings b
            JOIN seats s ON b.seat_id = s.id
            JOIN trips t ON s.trip_id = t.id
            JOIN routes r ON t.route_id = r.id
            WHERE b.user_id = :user_id
              AND (b.status IN ('confirmed', 'cancelled') OR b.status IS NULL)
            ORDER BY b.booking_date DESC
        """)

        result = await db.execute(query, {"user_id": current_user.id})
        rows = result.fetchall()

        bookings = []
        for row in rows:
            bookings.append({
                "id": row[0],
                "origin": row[1],
                "destination": row[2],
                "departure_time": row[3].isoformat() if row[3] else None,
                "seat_number": row[4],
                "price_paid": row[5],
                "status": row[6],
                "can_cancel": bool(row[7])
            })

        return {"bookings": bookings, "total": len(bookings)}


# ۴. لغو بلیط با پیام محترمانه (فقط قبل از حرکت!)
@router.post("/cancel/{booking_id}")
async def cancel_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # چک کردن مالکیت + وضعیت + زمان حرکت
            result = await db.execute(text("""
                SELECT b.price_paid, t.departure_time, b.status
                FROM bookings b
                JOIN seats s ON b.seat_id = s.id
                JOIN trips t ON s.trip_id = t.id
                WHERE b.id = :bid AND b.user_id = :uid
            """), {"bid": booking_id, "uid": current_user.id})

            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="بلیط یافت نشد یا متعلق به شما نیست.")

            price_paid, departure_time, current_status = row

            if current_status == 'cancelled':
                raise HTTPException(status_code=400, detail="این بلیط قبلاً لغو شده است.")

            if departure_time <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=400,
                    detail="با عرض پوزش، امکان لغو بلیط وجود ندارد زیرا اتوبوس حرکت کرده است. امیدواریم سفر خوبی داشته باشید."
                )

            # ثبت درخواست لغو در پس‌زمینه
            background_tasks.add_task(refund_money, booking_id, price_paid, current_user.id)

            return {
                "message": "درخواست لغو بلیط با موفقیت ثبت شد. مبلغ طی چند ثانیه به کیف پول شما بازگردانده خواهد شد.",
                "booking_id": booking_id
            }