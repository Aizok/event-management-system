from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import auth
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.PROJECT_NAME} starting")
    yield
    print("Service stopped")


app=FastAPI(
    title="Auth Service - Event Management System",
    version="1.0.0",
    description="Authorization microservice",
    lifespan=lifespan
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth-service",
        "database_url": settings.DATABASE_URL
    }