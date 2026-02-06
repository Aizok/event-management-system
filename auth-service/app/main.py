from fastapi import FastAPI
from app.api.v1.endpoints import auth
from app.core.config import settings
from app.core.database import engine
from app.models.user import Base


app=FastAPI(
    title="Auth Service - Event Management System",
    version="1.0.0",
    description="Authorization microservice"
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Auth Service works!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth-service",
        "database_urk": settings.DATABASE_URL
    }