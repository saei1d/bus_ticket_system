
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from datetime import datetime, timezone

from app.schemas.booking import ReserveRequest
from app.services.booking_service import reserve_seat
from app.services.booking_queries import (
    GET_USER_BOOKINGS,
    GET_BOOKING_FOR_CANCELLATION,
    REFUND_TO_WALLET,
    MARK_BOOKING_CANCELLED,
    RELEASE_SEAT
)
from app.core.dependencies import get_current_user
from app.db.session import AsyncSessionLocal
from app.models.user import User


router = APIRouter(prefix="/booking", tags=["Booking"])


# Background task to refund money and cancel booking
async def refund_money(booking_id: int, amount: int, user_id: int):
    """Background task to process refund and cancellation."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            await db.execute(REFUND_TO_WALLET, {"amount": amount, "uid": user_id})
            await db.execute(MARK_BOOKING_CANCELLED, {"bid": booking_id})
            await db.execute(RELEASE_SEAT, {"bid": booking_id})


@router.post("/reserve", status_code=status.HTTP_201_CREATED)
async def reserve(
    request: ReserveRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Reserve a seat for a trip.
    Includes Redis lock for concurrency safety and daily rate limiting (20 bookings/day).
    """
    result = await reserve_seat(
        user_id=current_user.id,
        trip_id=request.trip_id,
        seat_number=request.seat_number
    )

    return {
        "message": "Ticket successfully reserved",
        "booking_id": result["booking_id"],
        "trip_id": request.trip_id,
        "seat_number": request.seat_number,
        "price_paid": result["price_paid"]
    }


@router.get("/my-bookings")
async def my_bookings(current_user: User = Depends(get_current_user)):
    """
    Get current user's booking history.
    Returns all confirmed and cancelled bookings.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(GET_USER_BOOKINGS, {"user_id": current_user.id})
        rows = result.fetchall()

        bookings = [
            {
                "id": row[0],
                "origin": row[1],
                "destination": row[2],
                "departure_time": row[3].isoformat() if row[3] else None,
                "seat_number": row[4],
                "price_paid": row[5],
                "status": row[6] or "pending",
                "can_cancel": bool(row[7])
            }
            for row in rows
        ]

        return {
            "bookings": bookings,
            "total": len(bookings)
        }


@router.post("/cancel/{booking_id}")
async def cancel_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a booking.
    Only allowed before departure time. Refund is processed in background.
    """
    async with AsyncSessionLocal() as db:
        async with db.begin():
            result = await db.execute(
                GET_BOOKING_FOR_CANCELLATION,
                {"bid": booking_id, "uid": current_user.id}
            )

            row = result.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail="Booking not found or does not belong to you."
                )

            price_paid, departure_time, current_status, booking_user_id = row
            
            # Additional security check: verify booking belongs to current user
            if booking_user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to cancel this booking."
                )

            if current_status == 'cancelled':
                raise HTTPException(
                    status_code=400,
                    detail="This booking has already been cancelled."
                )

            if departure_time <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=400,
                    detail="Sorry, cancellation is not allowed after the bus has departed. We wish you a safe trip."
                )

            # Schedule refund and cleanup in background
            background_tasks.add_task(refund_money, booking_id, price_paid, current_user.id)

            return {
                "message": "Cancellation request received. The amount will be refunded to your wallet shortly.",
                "booking_id": booking_id
            }