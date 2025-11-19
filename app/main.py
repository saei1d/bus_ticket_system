# app/main.py
from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine
from app.api.v1.router import router as v1_router
from app.models import *


app = FastAPI(
    title="Bus Ticket System API",
    version="1.0.0",
    description="bus ticketing platform.",
    contact={
        "name": "Me",
    },
    license_info={
        "name": "MIT",
    },
)


@app.on_event("startup")
async def startup_event():
    print("Bus Ticket System API started and ready to accept requests.")
    print("Use Alembic for database migrations if schema changes are needed.")


# Include all v1 API routes
app.include_router(v1_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to the Bus Ticket System API",
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "version": "1.0.0"
    }