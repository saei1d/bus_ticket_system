# app/services/booking_queries.py
"""
SQL queries for booking operations.
Separated from endpoints for better organization.
"""
from sqlalchemy import text


# Query to get user's booking history
GET_USER_BOOKINGS = text("""
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
      AND b.status IN ('confirmed', 'cancelled')
    ORDER BY b.booking_date DESC
""")


# Query to get booking details for cancellation
# Security: Checks both booking_id AND user_id to ensure user can only cancel their own bookings
GET_BOOKING_FOR_CANCELLATION = text("""
    SELECT b.price_paid, t.departure_time, b.status, b.user_id
    FROM bookings b
    JOIN seats s ON b.seat_id = s.id
    JOIN trips t ON s.trip_id = t.id
    WHERE b.id = :bid AND b.user_id = :uid
""")


# Query to refund money to wallet
REFUND_TO_WALLET = text("""
    UPDATE wallets SET balance = balance + :amount WHERE user_id = :uid
""")


# Query to mark booking as cancelled
MARK_BOOKING_CANCELLED = text("""
    UPDATE bookings SET status = 'cancelled' WHERE id = :bid
""")


# Query to release seat
RELEASE_SEAT = text("""
    UPDATE seats 
    SET is_reserved = false 
    WHERE id = (SELECT seat_id FROM bookings WHERE id = :bid)
""")

