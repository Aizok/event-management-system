from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import ai
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.PROJECT_NAME} starting")
    yield
    print("Service stopped")


app = FastAPI(
    title="AI Assistant Service - Event Management System",
    version=settings.VERSION,
    description="AI assistant microservice",
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