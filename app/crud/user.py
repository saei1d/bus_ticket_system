# app/crud/user.py
from sqlalchemy import text, func
from app.db.session import AsyncSessionLocal

async def get_user_by_mobile(mobile: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT * FROM users WHERE mobile = :m"), {"m": mobile})
        return result.fetchone()

async def create_user_db(mobile: str, password_hash: str, role: str):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # کاربر
            await db.execute(
                text("INSERT INTO users (mobile, password_hash) VALUES (:m, :p) RETURNING id"),
                {"m": mobile, "p": password_hash}
            )
            # پروفایل
            await db.execute(text("""
                INSERT INTO profiles (user_id, role, full_name)
                VALUES ((SELECT id FROM users WHERE mobile = :m), :r, :n)
            """), {"m": mobile, "r": role, "n": f"کاربر {mobile}"})
            # کیف پول
            await db.execute(text("""
                INSERT INTO wallets (user_id, balance)
                VALUES ((SELECT id FROM users WHERE mobile = :m), 10000000)
            """), {"m": mobile})
        await db.commit()