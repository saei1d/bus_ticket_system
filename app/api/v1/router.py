# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.booking import router as booking_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.report import router as report_router
from app.api.v1.endpoints.trip import router as trip_router



router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(booking_router)
router.include_router(admin_router)
router.include_router(report_router)
router.include_router(trip_router)