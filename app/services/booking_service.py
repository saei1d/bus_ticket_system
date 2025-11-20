# app/services/booking_service.py
from fastapi import HTTPException, status
from sqlalchemy import text
from datetime import date

from app.db.session import AsyncSessionLocal
from app.services.rate_limit import check_daily_limit, increment_daily_limit
from app.services.seat_lock import acquire_seat_lock, release_seat_lock


async def reserve_seat(user_id: int, trip_id: int, seat_number: int) -> dict:
    """
    Atomically reserve a specific seat for a trip.
    Features:
    - Redis-based daily booking limit
    - Redis distributed lock for seat concurrency safety
    - Database row-level locking (FOR UPDATE)
    - Wallet balance check and deduction
    - Returns helpful available seats on conflict
    """
    # 1. Check daily booking limit (Redis)
    await check_daily_limit(user_id)

    # 2. Acquire distributed lock for this specific seat
    lock_key, lock_value = await acquire_seat_lock(trip_id, seat_number)

    try:
        async with AsyncSessionLocal() as db:
            async with db.begin():
                # 3. Fetch seat status and trip price (with row lock)
                seat_result = await db.execute(text("""
                    SELECT s.id AS seat_id, s.is_reserved, t.price
                    FROM seats s
                    JOIN trips t ON t.id = s.trip_id
                    WHERE s.trip_id = :trip_id AND s.seat_number = :seat_number
                    FOR UPDATE
                """), {"trip_id": trip_id, "seat_number": seat_number})

                seat_row = seat_result.fetchone()

                # 4. Seat not found or already reserved → return available seats
                if not seat_row or seat_row.is_reserved:
                    available_result = await db.execute(text("""
                        SELECT seat_number
                        FROM seats
                        WHERE trip_id = :trip_id AND is_reserved = false
                        ORDER BY seat_number
                    """), {"trip_id": trip_id})

                    available_seats = [row.seat_number for row in available_result.fetchall()]

                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": "This seat is no longer available.",
                            "available_seats": available_seats,
                            "tip": "Please select one of the available seats."
                        }
                    )

                seat_id = seat_row.seat_id
                price = seat_row.price

                # 5. Check wallet balance (with lock)
                wallet_result = await db.execute(text("""
                    SELECT balance FROM wallets WHERE user_id = :user_id FOR UPDATE
                """), {"user_id": user_id})

                wallet_row = wallet_result.fetchone()
                if not wallet_row:
                    raise HTTPException(status_code=404, detail="Wallet not found.")

                if wallet_row.balance < price:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": "Insufficient wallet balance.",
                            "required": price,
                            "current_balance": wallet_row.balance
                        }
                    )

                # 6. Deduct payment
                await db.execute(text("""
                    UPDATE wallets SET balance = balance - :price WHERE user_id = :user_id
                """), {"price": price, "user_id": user_id})

                # 7. Reserve the seat
                await db.execute(text("""
                    UPDATE seats SET is_reserved = true WHERE id = :seat_id
                """), {"seat_id": seat_id})

                # 8. Create booking record
                booking_result = await db.execute(text("""
                    INSERT INTO bookings (
                        user_id, trip_id, seat_id, price_paid, booking_date, status
                    ) VALUES (:user_id, :trip_id, :seat_id, :price, :date, 'confirmed')
                    RETURNING id
                """), {
                    "user_id": user_id,
                    "trip_id": trip_id,
                    "seat_id": seat_id,
                    "price": price,
                    "date": date.today()
                })

                booking_id = booking_result.scalar_one()

        # 9. Increment daily booking counter (only on full success)
        await increment_daily_limit(user_id)

        # 10. Success response
        return {
            "message": "Seat successfully reserved!",
            "booking_id": booking_id,
            "trip_id": trip_id,
            "seat_number": seat_number,
            "price_paid": price
        }

    finally:
        # Always release the Redis lock
        await release_seat_lock(lock_key, lock_value)