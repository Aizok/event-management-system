from fastapi import FastAPI
from .api.v1.endpoints import auth
from .core.config import settings
from .core.database import engine
from .models.user import Base

Base.metadata.create_all(bind=engine)

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
        "database_url": settings.DATABASE_URL
    }