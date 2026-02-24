from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import resources
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.PROJECT_NAME} starting")
    yield
    print("Service stopped")


app=FastAPI(
    title="Resource Service - Event Management System",
    version="1.0.0",
    description="Resource microservice",
    lifespan=lifespan
)

app.include_router(resources.router, prefix="/api/v1/resources", tags=["resources"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "resource-service"
    }