# app/main.py
from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.api.v1.router import router as v1_router
from app.models import *

app = FastAPI(
    title="Bus Ticket System - Saeid Shojaei Task",
    version="1.0.0",
    description="پروژه حرفه‌ای با Clean Architecture + Concurrency Safe"
)

@app.on_event("startup")
async def startup_event():
    # استفاده از Alembic برای migration‌ها
    # برای ساخت دستی جدول‌ها، از دستور زیر استفاده کنید:
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    print("API آماده است! برای migration از Alembic استفاده کنید.")

app.include_router(v1_router)

@app.get("/")
async def root():
    return {"message": "Bus Ticket System API - آماده برای رزرو بلیت!"}