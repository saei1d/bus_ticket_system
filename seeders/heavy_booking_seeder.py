import asyncio
import random
from datetime import date

from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def create_100k_bookings():
    print("Starting creation of up to 100,000 bookings (~65% seat occupancy)...")

    async with AsyncSessionLocal() as db:
        users = [row[0] async for row in await db.stream(text("SELECT id FROM users"))]
        trips = [row[0] async for row in await db.stream(text("SELECT id FROM trips"))]

        if not users or not trips:
            print("Error: No users or trips found. Run complete_seeder.py first.")
            return

        count = 0
        target = 100_000
        failed_attempts = 0
        max_failed_attempts = 1000

        while count < target:
            user_id = random.choice(users)
            trip_id = random.choice(trips)
            price = random.randint(600_000, 4_000_000)

            result = await db.execute(text("""
                UPDATE seats 
                SET is_reserved = true 
                WHERE id = (
                    SELECT id 
                    FROM seats 
                    WHERE trip_id = :tid AND is_reserved = false 
                    LIMIT 1
                )
                RETURNING id
            """), {"tid": trip_id})

            row = result.fetchone()
            if row:
                seat_id = row[0]
                await db.execute(text("""
                    INSERT INTO bookings (user_id, trip_id, seat_id, price_paid, booking_date, status)
                    VALUES (:u, :t, :s, :p, :d, 'confirmed')
                """), {
                    "u": user_id,
                    "t": trip_id,
                    "s": seat_id,
                    "p": price,
                    "d": date.today()
                })

                count += 1
                failed_attempts = 0

                if count % 10_000 == 0:
                    print(f"   {count:,} bookings created...")
                    await db.commit()

            else:
                failed_attempts += 1
                if failed_attempts >= max_failed_attempts:
                    avail_result = await db.execute(text("SELECT COUNT(*) FROM seats WHERE is_reserved = false"))
                    available_count = avail_result.scalar()

                    print("\nWarning: No more available seats found after multiple attempts.")
                    print(f"   Remaining empty seats: {available_count:,}")
                    print(f"   Bookings created: {count:,}")
                    print(f"   Target: {target:,}")
                    break

        await db.commit()

        if count >= target:
            print(f"Success: Successfully created {count:,} bookings!")
        else:
            print(f"Warning: Stopped early — {count:,} bookings created (target was {target:,})")


if __name__ == "__main__":
    asyncio.run(create_100k_bookings())