from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import users
from .core.config import settings
from .core.events import start_user_consumer, consumer
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

# Глобальная переменная для управления consumer
consumer_queue=None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.PROJECT_NAME} starting")

    global consumer_queue
    consumer_task=asyncio.create_task(start_user_consumer())
    consumer_queue=consumer_task #Ссылка

    yield

    if consumer_queue:
        consumer_queue.cancel()
        try:
            await consumer_queue
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")
    await consumer.close()
    logger.info("User Service Consumer stopped")


app=FastAPI(
    title="User Service - Event Management System",
    version="1.0.0",
    description="User microservice",
    lifespan=lifespan
)


app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "user-service",
        "database_url": settings.DATABASE_URL
    }