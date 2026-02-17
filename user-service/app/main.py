from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.endpoints import users
from .core.config import settings
from .core.database import engine
from .models.user import Base

Base.metadata.create_all(bind=engine)

app=FastAPI(
    title="User Service - Event Management System",
    version="1.0.0",
    description="User microservice"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "user-service",
        "database_url": settings.DATABASE_URL
    }