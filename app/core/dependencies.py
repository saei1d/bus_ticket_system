# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.crud.user import get_user_by_mobile
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decode JWT token and return the authenticated user.
    Raises 401 if token is invalid, expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        mobile: str | None = payload.get("sub")
        if mobile is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_mobile(mobile)
    if user is None:
        raise credentials_exception

    return user


def require_role(*allowed_roles: str):
    """
    Dependency factory to restrict access based on user role.
    """
    def role_checker(current_user=Depends(get_current_user)):
        user_role = next(
            (profile.role for profile in current_user.profiles if profile.role in allowed_roles),
            None
        )
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied — insufficient role permissions"
            )
        return current_user

    return role_checker


# Pre-defined role-based dependencies
require_passenger = require_role("passenger", "operator", "admin")
require_operator = require_role("operator", "admin")
require_admin = require_role("admin")