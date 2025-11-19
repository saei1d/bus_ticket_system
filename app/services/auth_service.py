# app/services/auth_service.py
from fastapi import HTTPException, status

from app.crud.user import get_user_by_mobile, create_user_db
from app.core.security import verify_password, get_password_hash, create_access_token


async def register_user(mobile: str, role: str = "passenger"):
    """
    Register a new user with the given mobile number.
    Default password is '123456' (hashed). Wallet starts with 10,000,000 IRR.
    """
    existing_user = await get_user_by_mobile(mobile)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This mobile number is already registered."
        )

    # Fixed default password: 123456 (securely hashed)
    password_hash = get_password_hash("123456")

    await create_user_db(mobile=mobile, password_hash=password_hash, role=role)

    return {
        "message": "User registered successfully",
        "mobile": mobile,
        "role": role,
        "initial_wallet_balance": 10_000_000,
        "default_password": "123456"  # Only shown during development/seeding
    }


async def login_user(mobile: str, password: str):
    """
    Authenticate user and return JWT access token.
    """
    user = await get_user_by_mobile(mobile)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile number or password"
        )

    access_token = create_access_token(data={"sub": mobile})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }