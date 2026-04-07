from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.endpoints import tasks
from .api.v1.endpoints import task_dependencies
from .core.config import settings
from .core.events import producer
import asyncio
from .core.database import AsyncSessionLocal
from .crud.task import task_crud
import logging

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)


async def overdue_worker():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await task_crud.update_overdue_tasks(db)
        except Exception as e:
            logger.error(f"Overdue worker error: {e}")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.PROJECT_NAME} starting")
    await producer.connect()
    worker_task=asyncio.create_task(overdue_worker())

    yield

    worker_task.cancel()
    print("Service stopped")
    await producer.close()

app=FastAPI(
    title="Task Service - Event Management System",
    version="1.0.0",
    description="Task microservice",
    lifespan=lifespan
)

app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(task_dependencies.router, prefix="/api/tasks", tags=["task-dependencies"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "task-service",
        "database_url": settings.DATABASE_URL
    }