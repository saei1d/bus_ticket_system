# app/crud/user.py
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.user import User


async def get_user_by_mobile(mobile: str) -> User | None:
    """
    Retrieve a user by mobile number with eager-loaded profiles.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User)
            .options(selectinload(User.profiles))
            .where(User.mobile == mobile)
        )
        return result.scalar_one_or_none()


async def create_user_db(mobile: str, password_hash: str, role: str = "passenger") -> None:
    """
    Create a new user with profile and wallet.
    - Default password: 123456 (hashed)
    - Initial wallet balance: 10,000,000 IRR
    - Default full name: "User <last 4 digits>"
    """
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # Insert user and get ID
            user_result = await db.execute(
                text("INSERT INTO users (mobile, password_hash) VALUES (:m, :p) RETURNING id"),
                {"m": mobile, "p": password_hash}
            )
            user_id = user_result.scalar_one()

            # Create profile
            display_name = f"User {mobile[-4:]}"
            await db.execute(
                text("""
                    INSERT INTO profiles (user_id, role, full_name)
                    VALUES (:uid, :role, :name)
                """),
                {"uid": user_id, "role": role, "name": display_name}
            )

            # Create wallet with initial balance
            await db.execute(
                text("""
                    INSERT INTO wallets (user_id, balance)
                    VALUES (:uid, 10000000)
                """),
                {"uid": user_id}
            )

        await db.commit()