# seeders/complete_seeder.py
import asyncio
import os
import sys
import random
from datetime import datetime, timedelta, timezone

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from app.db.base import Base
from app.db.session import engine
from app.core.security import get_password_hash
from sqlalchemy import text

# شهرها به صورت فینگلیش (دقیقاً برای JSON قابل سریالایز شدن)
cities = [
    "Tehran", "Mashhad", "Isfahan", "Shiraz", "Tabriz",
    "Karaj", "Ahvaz", "Qom", "Kermanshah", "Rasht",
    "Yazd", "Kerman", "Arak", "Hamedan", "BandarAbbas"
]

async def seed_everything():
    print("در حال ریست و ساخت دیتابیس کامل...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        async with db.begin():
            print("۱. ساخت ادمین + ۲۵ کاربر...")
            await db.execute(text("INSERT INTO users (mobile, password_hash) VALUES ('09990000001', :ph)"),
                             {"ph": get_password_hash("123456")})
            await db.execute(text("INSERT INTO profiles (user_id, role, full_name) VALUES ((SELECT id FROM users WHERE mobile='09990000001'), 'admin', 'Admin System')"))
            await db.execute(text("INSERT INTO wallets (user_id, balance) VALUES ((SELECT id FROM users WHERE mobile='09990000001'), 999999999)"))

            for i in range(25):
                mobile = f"09{random.randint(10,99)}{random.randint(1000000,9999999)}"
                await db.execute(text("INSERT INTO users (mobile, password_hash) VALUES (:m, :ph)"),
                                 {"m": mobile, "ph": get_password_hash("123456")})
                await db.execute(text("INSERT INTO profiles (user_id, role, full_name) VALUES ((SELECT id FROM users WHERE mobile=:m), 'passenger', :n)"),
                                 {"m": mobile, "n": f"User {mobile[-4:]}"})
                await db.execute(text("INSERT INTO wallets (user_id, balance) VALUES ((SELECT id FROM users WHERE mobile=:m), 50000000)"), {"m": mobile})

            print("۲. ساخت مسیرهای رفت و برگشت (۱۵ مسیر × ۲ = ۳۰ مسیر)...")
            route_ids = []
            for _ in range(15):
                origin = random.choice(cities)
                destination = random.choice([c for c in cities if c != origin])
                dist = random.randint(300, 1800)
                # رفت
                result1 = await db.execute(text("""
                    INSERT INTO routes (origin, destination, distance_km) 
                    VALUES (:o, :d, :dist) RETURNING id
                """), {"o": origin, "d": destination, "dist": dist})
                route_ids.append(result1.scalar_one())
                # برگشت
                result2 = await db.execute(text("""
                    INSERT INTO routes (origin, destination, distance_km) 
                    VALUES (:o, :d, :dist) RETURNING id
                """), {"o": destination, "d": origin, "dist": dist})
                route_ids.append(result2.scalar_one())

            print("۳. ساخت ۴۰ اتوبوس با ظرفیت ۲۰ تا ۳۵ صندلی...")
            for i in range(1, 41):
                plate = f"IR{random.randint(10,99)}{chr(65+random.randint(0,25))}{random.randint(100,999)}"
                capacity = random.randint(20, 35)
                await db.execute(text("INSERT INTO buses (plate_number, capacity, is_vip) VALUES (:p, :c, :v)"),
                                 {"p": plate, "c": capacity, "v": random.random() > 0.7})

            print("۴. ساخت سفرها (برای ۱۵۰٬۰۰۰+ صندلی)...")
            base = datetime.now(timezone.utc) + timedelta(days=1)
            # افزایش تعداد سفرها برای ساخت صندلی‌های کافی
            for _ in range(5000):
                route_id = random.choice(route_ids)
                bus_id = random.randint(1, 40)
                dep = base + timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
                duration = random.randint(6, 28)
                await db.execute(text("""
                    INSERT INTO trips (route_id, bus_id, departure_time, arrival_time, price)
                    VALUES (:r, :b, :d, :a, :p)
                """), {
                    "r": route_id, "b": bus_id,
                    "d": dep, "a": dep + timedelta(hours=duration),
                    "p": random.randint(600000, 4000000)
                })

            print("۵. ساخت صندلی‌ها (حداکثر ۱۵۰٬۰۰۰ صندلی برای ۱۰۰٬۰۰۰ رزرو)...")

            # برای ساخت 100,000 رزرو، نیاز به حداقل 150,000 صندلی داریم
            # (چون حدود 65-70% صندلی‌ها پر می‌شوند)
            MAX_SEATS = 150_000
            seat_counter = 0

            result = await db.execute(text("""
                SELECT t.id, b.capacity 
                FROM trips t 
                JOIN buses b ON t.bus_id = b.id
            """))

            for trip_id, capacity in result.fetchall():

                # اگر به سقف رسیدیم → کاملاً متوقف شو
                if seat_counter >= MAX_SEATS:
                    print(f"   ظرفیت تکمیل شد! {seat_counter} صندلی ساخته شد.")
                    break

                # محاسبه تعداد مجاز باقی‌مانده
                remaining = MAX_SEATS - seat_counter
                seats_to_create = min(capacity, remaining)

                for n in range(1, seats_to_create + 1):
                    await db.execute(text("""
                        INSERT INTO seats (trip_id, seat_number, is_reserved) 
                        VALUES (:t, :n, false)
                    """), {"t": trip_id, "n": n})

                seat_counter += seats_to_create

            print(f"   مجموع صندلی‌های ساخته‌شده: {seat_counter}")


            await db.commit()
            print(f"Seeder کامل شد! {seat_counter:,} صندلی ساخته شد — آماده برای ساخت ۱۰۰٬۰۰۰ رزرو")

if __name__ == "__main__":
    asyncio.run(seed_everything())