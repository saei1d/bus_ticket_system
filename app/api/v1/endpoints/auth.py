# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, Request
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth_service import register_user, login_user
from app.services.rate_limit import check_rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest, req: Request):
    # Rate limit: 10 requests per minute per IP and phone
    ip = get_client_ip(req)
    await check_rate_limit(f"register_ip:{ip}", limit=10, window_seconds=60)
    await check_rate_limit(f"register_phone:{request.mobile}", limit=10, window_seconds=60)
    
    return await register_user(request.mobile, request.role)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request):
    # Rate limit: 10 requests per minute per IP and phone
    ip = get_client_ip(req)
    await check_rate_limit(f"login_ip:{ip}", limit=10, window_seconds=60)
    await check_rate_limit(f"login_phone:{request.mobile}", limit=10, window_seconds=60)
    
    return await login_user(request.mobile, request.password)