# app/schemas/booking.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReserveRequest(BaseModel):
    trip_id: int
    seat_number: int

class BookingResponse(BaseModel):
    id: int
    trip_id: int
    seat_number: int
    price_paid: int
    status: str
    created_at: datetime

class CancelResponse(BaseModel):
    message: str
    refunded_amount: int