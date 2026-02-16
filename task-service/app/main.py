from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.endpoints.tasks import router as tasks_router
from .core.config import settings
from .core.database import engine
from .models.base import Base

Base.metadata.create_all(bind=engine)

app=FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001", "http://localhost:8002", "http://localhost:8003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "task-service"
    }