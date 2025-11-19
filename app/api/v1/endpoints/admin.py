# app/api/v1/endpoints/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel,Field
from typing import List
from app.core.dependencies import get_current_user, require_admin
from app.db.session import AsyncSessionLocal
from sqlalchemy import text
from datetime import datetime


router = APIRouter(prefix="/admin", tags=["Admin"])

# Schemaها
class BusCreate(BaseModel):
    plate_number: str
    capacity: int = 44
    is_vip: bool = False

class BusResponse(BaseModel):
    id: int
    plate_number: str
    capacity: int
    is_vip: bool

class TripCreate(BaseModel):
    route_id: int
    bus_id: int
    departure_time: datetime
    arrival_time: datetime
    price: int

class TripResponse(BaseModel):
    id: int
    route_id: int
    bus_id: int
    departure_time: datetime
    arrival_time: datetime
    price: int
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# 6. API اضافه کردن اتوبوس جدید (فقط ادمین)
@router.post("/bus", response_model=BusResponse, status_code=status.HTTP_201_CREATED)
async def create_bus(bus: BusCreate, current_user = Depends(require_admin)):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # چک تکراری بودن پلاک
            exists = await db.execute(text("SELECT 1 FROM buses WHERE plate_number = :p"), {"p": bus.plate_number})
            if exists.fetchone():
                raise HTTPException(400, "این پلاک قبلاً ثبت شده")

            result = await db.execute(text("""
                INSERT INTO buses (plate_number, capacity, is_vip)
                VALUES (:p, :c, :v) RETURNING id
            """), {"p": bus.plate_number, "c": bus.capacity, "v": bus.is_vip})
            bus_id = result.scalar_one()

        return BusResponse(id=bus_id, **bus.dict())

# 7. API ایجاد سفر جدید (فقط ادمین)
@router.post("/trip", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(trip: TripCreate, current_user = Depends(require_admin)):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # چک وجود route و bus
            route_exists = await db.execute(text("SELECT 1 FROM routes WHERE id = :rid"), {"rid": trip.route_id})
            bus_exists = await db.execute(text("SELECT 1 FROM buses WHERE id = :bid"), {"bid": trip.bus_id})
            if not route_exists.fetchone() or not bus_exists.fetchone():
                raise HTTPException(404, "خط سیر یا اتوبوس یافت نشد")

            # چک زمان منطقی
            if trip.arrival_time <= trip.departure_time:
                raise HTTPException(400, "زمان رسیدن باید بعد از زمان حرکت باشد")

            result = await db.execute(text("""
                INSERT INTO trips (route_id, bus_id, departure_time, arrival_time, price)
                VALUES (:r, :b, :d, :a, :p) RETURNING id
            """), {
                "r": trip.route_id, "b": trip.bus_id,
                "d": trip.departure_time, "a": trip.arrival_time, "p": trip.price
            })
            trip_id = result.scalar_one()

            # ساخت خودکار صندلی‌ها
            bus_cap = await db.execute(text("SELECT capacity FROM buses WHERE id = :bid"), {"bid": trip.bus_id})
            capacity = bus_cap.scalar_one()
            for seat_num in range(1, capacity + 1):
                await db.execute(text("""
                    INSERT INTO seats (trip_id, seat_number, is_reserved)
                    VALUES (:tid, :sn, false)
                """), {"tid": trip_id, "sn": seat_num})

        return TripResponse(id=trip_id, **trip.dict())

# لیست تمام اتوبوس‌ها (اختیاری برای ادمین)
@router.get("/buses", response_model=List[BusResponse])
async def list_buses(current_user = Depends(require_admin)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT id, plate_number, capacity, is_vip FROM buses ORDER BY id"))
        buses = result.fetchall()
        return [BusResponse(id=b.id, plate_number=b.plate_number, capacity=b.capacity, is_vip=b.is_vip) for b in buses]
    


    

class ChargeWalletRequest(BaseModel):
    mobile: str = Field(..., pattern=r"^09\d{9}$")
    amount: int = Field(..., gt=0)

@router.post("/wallet/charge")
async def charge_wallet(
    request: ChargeWalletRequest,
    current_user = Depends(require_admin)
):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            user_result = await db.execute(text("SELECT id FROM users WHERE mobile = :m"), {"m": request.mobile})
            user = user_result.fetchone()
            if not user:
                raise HTTPException(404, "کاربری با این شماره موبایل یافت نشد.")
            
            await db.execute(text("""
                UPDATE wallets SET balance = balance + :amount 
                WHERE user_id = :uid
            """), {"amount": request.amount, "uid": user[0]})
            
            balance_result = await db.execute(text("SELECT balance FROM wallets WHERE user_id = :uid"), {"uid": user[0]})
            new_balance = balance_result.scalar_one()
            
            return {
                "message": f"کیف پول کاربر {request.mobile} با موفقیت {request.amount:,} تومان شارژ شد.",
                "new_balance": new_balance
            }