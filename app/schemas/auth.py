# app/schemas/auth.py
from pydantic import BaseModel, Field
from typing import Literal

class RegisterRequest(BaseModel):
    mobile: str = Field(..., pattern=r"^09\d{9}$", example="09111234567")
    role: Literal["passenger", "operator", "admin"] = "passenger"

class LoginRequest(BaseModel):
    mobile: str = Field(..., pattern=r"^09\d{9}$")
    password: str = "123456"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"