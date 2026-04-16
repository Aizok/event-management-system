from contextlib import asynccontextmanager
from fastapi import FastAPI
from .core.config import settings
from .api.v1.endpoints import ai


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.PROJECT_NAME} starting")
    yield
    print("Service stopped")


app = FastAPI(
    title="AI Assistant Service - Event Management System",
    version="1.0.0",
    description="AI microservice",
    lifespan=lifespan
)

app.include_router(ai.router, prefix="/api/ai", tags=["ai"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-assistant",
        "database_url": settings.DATABASE_URL
    }