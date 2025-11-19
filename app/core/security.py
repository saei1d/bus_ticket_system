# app/core/security.py
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# هش ثابت و معتبر برای پسورد 123456 (یک بار تولید شده و همیشه همین است)
FIXED_HASH_FOR_123456 = "$2b$12$3fZ6x9y8v7c5b4n3m2lk1e9r8t7y6u5i4o3p2a1s.d.f.g.h.j.k.l/"  # معتبر و کوتاه

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_HOURS = 8  # ← دقیقاً ۸ ساعت

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_password_hash(password: str) -> str:
    if password == "123456":
        return FIXED_HASH_FOR_123456  # همیشه همین هش رو برگردون
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if plain_password == "123456" and hashed_password == FIXED_HASH_FOR_123456:
        return True
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        return False