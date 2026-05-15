from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import events
from .core.config import settings
from .api.v1.endpoints import event_participants

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.PROJECT_NAME} starting")
    yield
    print("Service stopped")


app=FastAPI(
    title="Event Service - Event Management System",
    version="1.0.0",
    description="Event microservice",
    lifespan=lifespan
)

app.include_router(
    event_participants.router,
    prefix="/api/events",
    tags=["participants"]
)
app.include_router(events.router, prefix="/api/events", tags=["events"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "event-service",
        "database_url": settings.DATABASE_URL
    }