# app/api/v1/endpoints/admin.py
"""
Admin endpoints - REST API for bus and trip management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List

from app.core.dependencies import require_admin
from app.db.session import AsyncSessionLocal
from app.schemas.admin import BusCreate, BusResponse, TripCreate, TripResponse, ChargeWalletRequest
from app.services.admin_queries import (
    CHECK_BUS_PLATE,
    CREATE_BUS,
    CHECK_ROUTE,
    CHECK_BUS,
    CREATE_TRIP,
    GET_BUS_CAPACITY,
    CREATE_SEAT,
    LIST_BUSES,
    GET_USER_BY_MOBILE,
    CHARGE_WALLET,
    GET_WALLET_BALANCE
)


router = APIRouter(prefix="/admin", tags=["Admin"])



# Create new bus (Admin only)
@router.post("/bus", response_model=BusResponse, status_code=status.HTTP_201_CREATED)
async def create_bus(bus: BusCreate, current_user=Depends(require_admin)):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            exists = await db.execute(CHECK_BUS_PLATE, {"p": bus.plate_number})
            if exists.fetchone():
                raise HTTPException(status_code=400, detail="Plate number already registered.")

            result = await db.execute(CREATE_BUS, {
                "p": bus.plate_number,
                "c": bus.capacity,
                "v": bus.is_vip
            })
            bus_id = result.scalar_one()

        return BusResponse(id=bus_id, **bus.dict())


# Create new trip and auto-generate seats (Admin only)
@router.post("/trip", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(trip: TripCreate, current_user=Depends(require_admin)):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            route_exists = await db.execute(CHECK_ROUTE, {"rid": trip.route_id})
            bus_exists = await db.execute(CHECK_BUS, {"bid": trip.bus_id})

            if not route_exists.fetchone() or not bus_exists.fetchone():
                raise HTTPException(status_code=404, detail="Route or bus not found.")

            if trip.arrival_time <= trip.departure_time:
                raise HTTPException(status_code=400, detail="Arrival time must be after departure time.")

            result = await db.execute(CREATE_TRIP, {
                "r": trip.route_id,
                "b": trip.bus_id,
                "d": trip.departure_time,
                "a": trip.arrival_time,
                "p": trip.price
            })
            trip_id = result.scalar_one()

            capacity_result = await db.execute(GET_BUS_CAPACITY, {"bid": trip.bus_id})
            capacity = capacity_result.scalar_one()

            for seat_number in range(1, capacity + 1):
                await db.execute(CREATE_SEAT, {"tid": trip_id, "sn": seat_number})

        return TripResponse(id=trip_id, **trip.dict())


# List all buses (Admin only)
@router.get("/buses", response_model=List[BusResponse])
async def list_buses(current_user=Depends(require_admin)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(LIST_BUSES)
        buses = result.fetchall()
        return [
            BusResponse(
                id=row.id,
                plate_number=row.plate_number,
                capacity=row.capacity,
                is_vip=row.is_vip
            )
            for row in buses
        ]



@router.post("/wallet/charge")
async def charge_wallet(
    request: ChargeWalletRequest,
    current_user=Depends(require_admin)
):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            user_result = await db.execute(GET_USER_BY_MOBILE, {"m": request.mobile})
            user = user_result.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="User with this mobile number not found.")

            user_id = user[0]

            await db.execute(CHARGE_WALLET, {
                "amount": request.amount,
                "uid": user_id
            })

            new_balance_result = await db.execute(GET_WALLET_BALANCE, {"uid": user_id})
            new_balance = new_balance_result.scalar_one()

            return {
                "message": f"Wallet for {request.mobile} successfully charged with {request.amount:,} IRR.",
                "new_balance": new_balance
            }