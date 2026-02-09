from fastapi import FastAPI
from .api.v1.endpoints import events
from .core.config import settings
from .core.database import engine
from .models.event import Base

Base.metadata.create_all(bind=engine)

app=FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

app.include_router(events.router, prefix="/api/v1/events", tags=["events"])

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "event-service"
    }