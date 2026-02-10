from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.endpoints.events import router as events_router
from .core.config import settings
from .core.database import engine
from .models.event import Base

Base.metadata.create_all(bind=engine)

app=FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001", "http://localhost:8002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(events_router, prefix="/api/v1/events", tags=["events"])

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "event-service"
    }