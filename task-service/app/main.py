from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import tasks
from .core.config import settings
import logging
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.PROJECT_NAME} starting")
    yield
    print("Service stopped")


app=FastAPI(
    title="Task Service - Event Management System",
    version="1.0.0",
    description="Task microservice",
    lifespan=lifespan
)

app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "task-service"
    }