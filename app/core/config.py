# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str = "super-secret-jwt-key-2025-saeid-shojaei"
    ALGORITHM: str = "HS256"

settings = Settings(_env_file=".env")