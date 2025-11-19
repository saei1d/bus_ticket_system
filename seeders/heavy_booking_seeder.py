# seeders/heavy_booking_seeder.py
import asyncio
import random
from app.db.session import AsyncSessionLocal
from sqlalchemy import text
from datetime import date

async def create_100k_bookings():
    print("شروع ساخت حداکثر ۱۰۰٬۰۰۰ رزرو (حدود ۶۵٪ صندلی‌ها پر میشه)...")
    async with AsyncSessionLocal() as db:
        users = [r[0] async for r in await db.stream(text("SELECT id FROM users"))]
        trips = [r[0] async for r in await db.stream(text("SELECT id FROM trips"))]

        if not users or not trips:
            print("خطا: ابتدا باید users و trips را بسازید (complete_seeder.py را اجرا کنید)")
            return

        count = 0
        target = 100_000
        failed_attempts = 0
        max_failed_attempts = 1000  # اگر 1000 بار متوالی صندلی پیدا نشد، متوقف شو

        while count < target:
            user_id = random.choice(users)
            trip_id = random.choice(trips)
            price = random.randint(600000, 4000000)

            result = await db.execute(text("""
                UPDATE seats 
                SET is_reserved = true 
                WHERE id = (
                    SELECT id FROM seats 
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
                """), {"u": user_id, "t": trip_id, "s": seat_id, "p": price, "d": date.today()})
                count += 1
                failed_attempts = 0  # reset counter
                if count % 10000 == 0:
                    print(f"   {count:,} رزرو ساخته شد...")
                    await db.commit()
                elif count == target:
                    break
            else:
                failed_attempts += 1
                if failed_attempts >= max_failed_attempts:
                    # بررسی تعداد صندلی‌های خالی باقی‌مانده
                    available_seats = await db.execute(text("""
                        SELECT COUNT(*) FROM seats WHERE is_reserved = false
                    """))
                    available_count = available_seats.scalar()
                    print(f"\n⚠️  هشدار: صندلی خالی پیدا نشد!")
                    print(f"   تعداد صندلی‌های خالی باقی‌مانده: {available_count:,}")
                    print(f"   تعداد رزروهای ساخته شده: {count:,}")
                    print(f"   هدف: {target:,}")
                    break

        await db.commit()
        if count >= target:
            print(f"✅ تمام! دقیقاً {count:,} رزرو ساخته شد!")
        else:
            print(f"⚠️  متوقف شد! {count:,} رزرو ساخته شد (هدف: {target:,})")

if __name__ == "__main__":
    asyncio.run(create_100k_bookings())