from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import users
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.PROJECT_NAME} starting")
    yield
    print("Service stopped")


app=FastAPI(
    title="User Service - Event Management System",
    version="1.0.0",
    description="User microservice",
    lifespan=lifespan
)


app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "user-service",
        "database_url": settings.DATABASE_URL
    }