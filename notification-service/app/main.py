from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import notifications
from .core.config import settings
from .core.events import start_notification_consumer, consumer
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

# Глобальная переменная для управления consumer
consumer_background_task=None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.PROJECT_NAME} starting")

    global consumer_background_task
    consumer_task=asyncio.create_task(start_notification_consumer())
    consumer_background_task=consumer_task #Ссылка

    yield

    if consumer_background_task:
        consumer_background_task.cancel()
        try:
            await consumer_background_task
        except asyncio.CancelledError:
            logger.info("Notification Consumer task cancelled")
    await consumer.close()
    logger.info("Notification Service Consumer stopped")


app=FastAPI(
    title="Notification Service - Event Management System",
    version="1.0.0",
    description="Notification microservice",
    lifespan=lifespan
)


app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "notification-service",
        "database_url": settings.DATABASE_URL
    }