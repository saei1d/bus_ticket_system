from pydantic import BaseModel, Field
from datetime import datetime

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


class ChargeWalletRequest(BaseModel):
    mobile: str = Field(..., pattern=r"^09\d{9}$", description="Iranian mobile number starting with 09")
    amount: int = Field(..., gt=0, description="Amount in IRR to add")
