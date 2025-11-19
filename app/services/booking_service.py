# app/services/booking_service.py
from fastapi import HTTPException
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.services.rate_limit import check_daily_limit, increment_daily_limit
from app.services.seat_lock import acquire_seat_lock, release_seat_lock
from datetime import date

async def reserve_seat(user_id: int, trip_id: int, seat_number: int):
    # ------------------------------------------------------
    # 1) چک محدودیت روزانه (Redis) - فقط چک می‌کند، increment نمی‌کند
    # ------------------------------------------------------
    await check_daily_limit(user_id)
    
    # ------------------------------------------------------
    # 2) قفل‌گذاری صندلی (Redis)
    # ------------------------------------------------------
    lock_key, lock_value = await acquire_seat_lock(trip_id, seat_number)

    try:
        async with AsyncSessionLocal() as db:
            async with db.begin():

                # ------------------------------------------------------
                # 3) گرفتن وضعیت صندلی، قیمت و موجودی کیف پول (با LOCK)
                # ------------------------------------------------------
                seat_result = await db.execute(text("""
                    SELECT s.id AS seat_id, s.is_reserved, t.price
                    FROM seats s
                    JOIN trips t ON t.id = s.trip_id
                    WHERE s.trip_id = :tid AND s.seat_number = :sn
                    FOR UPDATE
                """), {"tid": trip_id, "sn": seat_number})

                seat_row = seat_result.fetchone()

                # ------------------------------------------------------
                # 4) اگر صندلی وجود نداشت یا رزرو شده بود → لیست صندلی‌های آزاد را بده
                # ------------------------------------------------------
                if not seat_row or seat_row.is_reserved:

                    available_q = await db.execute(text("""
                        SELECT seat_number
                        FROM seats
                        WHERE trip_id = :tid AND is_reserved = false
                        ORDER BY seat_number
                    """), {"tid": trip_id})

                    available_seats = [s.seat_number for s in available_q.fetchall()]

                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": "صندلی موجود نیست",
                            "available_seats": available_seats
                        }
                    )

                wallet_result = await db.execute(text("""
                    SELECT balance
                    FROM wallets
                    WHERE user_id = :uid
                    FOR UPDATE
                """), {"uid": user_id})

                wallet_row = wallet_result.fetchone()
                if not wallet_row:
                    raise HTTPException(404, "کیف پول یافت نشد")

                # ------------------------------------------------------
                # 5) چک موجودی کیف پول
                # ------------------------------------------------------
                if wallet_row.balance < seat_row.price:
                    raise HTTPException(400, "موجودی کافی نیست")

                # ------------------------------------------------------
                # 6) کسر پول
                # ------------------------------------------------------
                await db.execute(text("""
                    UPDATE wallets SET balance = balance - :p WHERE user_id = :uid
                """), {"p": seat_row.price, "uid": user_id})

                # ------------------------------------------------------
                # 7) ثبت رزرو صندلی
                # ------------------------------------------------------
                await db.execute(text("""
                    UPDATE seats SET is_reserved = true WHERE id = :sid
                """), {"sid": seat_row.seat_id})

                # ------------------------------------------------------
                # 8) ثبت رکورد در bookings
                # ------------------------------------------------------
                booking_result = await db.execute(text("""
                    INSERT INTO bookings (user_id, trip_id, seat_id, price_paid, booking_date, status)
                    VALUES (:uid, :tid, :sid, :price, :date, 'confirmed')
                    RETURNING id
                """), {
                    "uid": user_id,
                    "tid": trip_id,
                    "sid": seat_row.seat_id,
                    "price": seat_row.price,
                    "date": date.today()
                })
                booking_id = booking_result.scalar_one()

        # ------------------------------------------------------
        # 9) Increment daily limit counter - فقط بعد از موفقیت کامل
        # ------------------------------------------------------
        await increment_daily_limit(user_id)

        # ------------------------------------------------------
        # 10) خروجی موفق
        # ------------------------------------------------------
        return {
            "message": "رزرو با موفقیت انجام شد",
            "price": seat_row.price,
            "booking_id": booking_id
        }

    finally:
        # ------------------------------------------------------
        # 10) آزاد کردن قفل Redis
        # ------------------------------------------------------
        await release_seat_lock(lock_key, lock_value)
