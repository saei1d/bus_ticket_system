# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.crud.user import get_user_by_mobile  # ← فقط mobile می‌گیره
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="توکن نامعتبر یا منقضی شده",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        mobile: str = payload.get("sub")
        if mobile is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # درست: فقط mobile می‌دیم، خودش db می‌سازه
    user = await get_user_by_mobile(mobile)
    if user is None:
        raise credentials_exception
    return user


# محافظت بر اساس نقش
def require_role(*allowed_roles: str):
    def role_checker(current_user = Depends(get_current_user)):
        user_role = None
        for profile in current_user.profiles:
            if profile.role in allowed_roles:
                user_role = profile.role
                break
        if not user_role:
            raise HTTPException(status_code=403, detail="دسترسی ممنوع — نقش کافی نیست")
        return current_user
    return role_checker


# نقش‌های آماده برای استفاده
require_passenger = require_role("passenger", "operator", "admin")
require_operator = require_role("operator", "admin")
require_admin = require_role("admin")