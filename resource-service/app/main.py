import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import resources
from .core.config import settings
from .core.database import AsyncSessionLocal
from .crud.resource import resource_crud
import logging

logger=logging.getLogger(__name__)


async def allocation_status_worker():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await resource_crud.update_allocation_statuses(db)
        except Exception as e:
            logger.error(f"Allocation worker error: {e}")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.PROJECT_NAME} starting")
    worker_task=asyncio.create_task(allocation_status_worker())

    yield
    worker_task.cancel()
    print("Service stopped")


app=FastAPI(
    title="Resource Service - Event Management System",
    version="1.0.0",
    description="Resource microservice",
    lifespan=lifespan
)

app.include_router(resources.router, prefix="/api/resources", tags=["resources"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "resource-service",
        "database_url": settings.DATABASE_URL
    }