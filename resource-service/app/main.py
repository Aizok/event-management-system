import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import resources
from .core.config import settings
from .core.database import AsyncSessionLocal
from .crud.resource import resource_crud
from .core.events import start_resource_consumer, consumer
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


# Глобальная переменная для управления consumer
consumer_background_task=None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.PROJECT_NAME} starting")

    worker_task=asyncio.create_task(allocation_status_worker())

    global consumer_background_task
    consumer_task=asyncio.create_task(start_resource_consumer())
    consumer_background_task=consumer_task

    yield

    worker_task.cancel()

    if consumer_background_task:
        consumer_background_task.cancel()
        try:
            await consumer_background_task
        except asyncio.CancelledError:
            logger.info("Resource consumer task cancelled")

    await consumer.close()
    logger.info("Resource Service Consumer stopped")


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