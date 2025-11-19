# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=dict)
async def register(request: RegisterRequest):
    return await register_user(request.mobile, request.role)

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    return await login_user(request.mobile, request.password)