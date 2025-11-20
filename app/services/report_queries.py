"""
Prepared SQL statements for admin report endpoints.
Separating them here keeps FastAPI endpoint files clean and easier to test.
"""
from sqlalchemy import text


TOP_DRIVER_QUERY = text("""
    WITH confirmed_bookings AS (
        SELECT id, trip_id
        FROM bookings
        WHERE status = 'confirmed' OR status IS NULL
    )
    SELECT b.plate_number, COUNT(*) AS bookings
    FROM confirmed_bookings bk
    JOIN trips t ON bk.trip_id = t.id
    JOIN buses b ON t.bus_id = b.id
    GROUP BY b.id, b.plate_number
    ORDER BY bookings DESC
    LIMIT 1
""")


BUS_MONTHLY_INCOME_QUERY = text("""
    WITH confirmed_bookings AS (
        SELECT id, trip_id, price_paid, created_at
        FROM bookings
        WHERE status = 'confirmed' OR status IS NULL
    )
    SELECT 
        b.plate_number,
        TO_CHAR(DATE_TRUNC('month', bk.created_at), 'YYYY-MM') AS month,
        COUNT(*) AS bookings,
        COALESCE(SUM(bk.price_paid), 0) AS income
    FROM confirmed_bookings bk
    JOIN trips t ON bk.trip_id = t.id
    JOIN buses b ON t.bus_id = b.id
    GROUP BY b.id, b.plate_number, DATE_TRUNC('month', bk.created_at)
    ORDER BY month DESC, income DESC
""")


HOURLY_BOOKINGS_QUERY = text("""
    SELECT COUNT(*) AS bookings
    FROM bookings
    WHERE (status = 'confirmed' OR status IS NULL)
      AND created_at >= :start_ts
      AND created_at < :end_ts
""")

DAILY_HOURLY_BREAKDOWN_QUERY = text("""
    SELECT 
        EXTRACT(HOUR FROM created_at AT TIME ZONE 'UTC')::int AS hour,
        COUNT(*) AS bookings
    FROM bookings
    WHERE (status = 'confirmed' OR status IS NULL)
      AND DATE(created_at AT TIME ZONE 'UTC') = :target_date
    GROUP BY hour
""")

