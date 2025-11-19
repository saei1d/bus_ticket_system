# app/api/v1/endpoints/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "فاز ۱ با موفقیت راه‌اندازی شد!",
        "architecture": "Clean + Async Ready"
    }