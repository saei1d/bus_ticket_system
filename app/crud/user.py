# app/crud/user.py
from sqlalchemy import text, func, select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models.user import User

async def get_user_by_mobile(mobile: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User)
            .options(selectinload(User.profiles))
            .where(User.mobile == mobile)
        )
        return result.scalar_one_or_none()

async def create_user_db(mobile: str, password_hash: str, role: str):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # user
            await db.execute(
                text("INSERT INTO users (mobile, password_hash) VALUES (:m, :p) RETURNING id"),
                {"m": mobile, "p": password_hash}
            )
            # profile
            await db.execute(text("""
                INSERT INTO profiles (user_id, role, full_name)
                VALUES ((SELECT id FROM users WHERE mobile = :m), :r, :n)
            """), {"m": mobile, "r": role, "n": f"کاربر {mobile}"})
            # wallet
            await db.execute(text("""
                INSERT INTO wallets (user_id, balance)
                VALUES ((SELECT id FROM users WHERE mobile = :m), 10000000)
            """), {"m": mobile})
        await db.commit()