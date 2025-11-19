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
from app.db.session import engine, AsyncSessionLocal
from app.core.security import get_password_hash
from sqlalchemy import text

cities = [
    "Tehran", "Mashhad", "Isfahan", "Shiraz", "Tabriz",
    "Karaj", "Ahvaz", "Qom", "Kermanshah", "Rasht",
    "Yazd", "Kerman", "Arak", "Hamedan", "BandarAbbas"
]

async def seed_everything():
    print("Dropping and recreating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        async with db.begin():
            print("1. Creating admin + 25 regular users...")
            await db.execute(text("INSERT INTO users (mobile, password_hash) VALUES ('09990000001', :ph)"),
                             {"ph": get_password_hash("123456")})
            await db.execute(text("""
                INSERT INTO profiles (user_id, role, full_name) 
                VALUES ((SELECT id FROM users WHERE mobile='09990000001'), 'admin', 'Admin System')
            """))
            await db.execute(text("""
                INSERT INTO wallets (user_id, balance) 
                VALUES ((SELECT id FROM users WHERE mobile='09990000001'), 999999999)
            """))

            for i in range(25):
                mobile = f"09{random.randint(10,99)}{random.randint(1000000,9999999)}"
                await db.execute(text("INSERT INTO users (mobile, password_hash) VALUES (:m, :ph)"),
                                 {"m": mobile, "ph": get_password_hash("123456")})
                await db.execute(text("""
                    INSERT INTO profiles (user_id, role, full_name) 
                    VALUES ((SELECT id FROM users WHERE mobile=:m), 'passenger', :n)
                """), {"m": mobile, "n": f"User {mobile[-4:]}"})
                await db.execute(text("""
                    INSERT INTO wallets (user_id, balance) 
                    VALUES ((SELECT id FROM users WHERE mobile=:m), 50000000)
                """), {"m": mobile})

            print("2. Creating 15 round-trip routes (30 routes total)...")
            route_ids = []
            for _ in range(15):
                origin = random.choice(cities)
                destination = random.choice([c for c in cities if c != origin])
                distance = random.randint(300, 1800)

                # Outbound
                res1 = await db.execute(text("""
                    INSERT INTO routes (origin, destination, distance_km) 
                    VALUES (:o, :d, :dist) RETURNING id
                """), {"o": origin, "d": destination, "dist": distance})
                route_ids.append(res1.scalar_one())

                # Return
                res2 = await db.execute(text("""
                    INSERT INTO routes (origin, destination, distance_km) 
                    VALUES (:o, :d, :dist) RETURNING id
                """), {"o": destination, "d": origin, "dist": distance})
                route_ids.append(res2.scalar_one())

            print("3. Creating 40 buses (20–35 seats, some VIP)...")
            for i in range(1, 41):
                plate = f"IR{random.randint(10,99)}{chr(65+random.randint(0,25))}{random.randint(100,999)}"
                capacity = random.randint(20, 35)
                is_vip = random.random() > 0.7
                await db.execute(text("""
                    INSERT INTO buses (plate_number, capacity, is_vip) 
                    VALUES (:p, :c, :v)
                """), {"p": plate, "c": capacity, "v": is_vip})

            print("4. Creating trips (generating 150,000+ seats)...")
            base_date = datetime.now(timezone.utc) + timedelta(days=1)
            for _ in range(5000):
                route_id = random.choice(route_ids)
                bus_id = random.randint(1, 40)
                departure = base_date + timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
                duration_hours = random.randint(6, 28)
                price = random.randint(600000, 4000000)

                await db.execute(text("""
                    INSERT INTO trips (route_id, bus_id, departure_time, arrival_time, price)
                    VALUES (:r, :b, :d, :a, :p)
                """), {
                    "r": route_id,
                    "b": bus_id,
                    "d": departure,
                    "a": departure + timedelta(hours=duration_hours),
                    "p": price
                })

            print("5. Creating seats (target: at least 150,000 for ~100k bookings)...")
            MAX_SEATS = 150_000
            seat_counter = 0

            result = await db.execute(text("""
                SELECT t.id, b.capacity 
                FROM trips t 
                JOIN buses b ON t.bus_id = b.id
                ORDER BY t.id
            """))

            for trip_id, capacity in result.fetchall():
                if seat_counter >= MAX_SEATS:
                    print(f"   Seat limit reached: {seat_counter} seats created.")
                    break

                seats_to_create = min(capacity, MAX_SEATS - seat_counter)

                for n in range(1, seats_to_create + 1):
                    await db.execute(text("""
                        INSERT INTO seats (trip_id, seat_number, is_reserved) 
                        VALUES (:t, :n, false)
                    """), {"t": trip_id, "n": n})

                seat_counter += seats_to_create

            print(f"   Total seats created: {seat_counter:,}")

        await db.commit()
        print(f"Seeding completed successfully! {seat_counter:,} seats ready for bookings.")

if __name__ == "__main__":
    asyncio.run(seed_everything())