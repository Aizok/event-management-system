import logging
from ..crud.resource import resource_crud
from .database import AsyncSessionLocal
from shared.events.consumer import EventConsumer
from shared.events.schemas.events import BaseEvent, TaskRescheduled


logger=logging.getLogger(__name__)

consumer=EventConsumer()

async def handle_task_rescheduled(event: TaskRescheduled):
    """Обработка сдвига задачи по времени, нужно пересчитать allocations"""
    task_id=event.source_entity_id
    data=event.data

    start_time=data.get("start_time")
    end_time=data.get("end_time")

    logger.info(f"TaskRescheduled received (task_id={task_id})")

    async with AsyncSessionLocal() as db:
        allocations=await resource_crud.get_allocations_by_task(db, task_id)

        for alloc in allocations:
            try:
                await resource_crud.shift_allocation_to_fit_task(
                    db,
                    alloc,
                    start_time,
                    end_time
                )
            except Exception as e:
                logger.error(f"Allocation shift error: {e}")

        await db.commit()


async def start_resource_consumer():
    logger.info("Starting consumer in resource-service")

    queue=await consumer.consume(
        queue_name="resource-service",
        routing_keys=[
            "TaskRescheduled.task-service"
        ],
        callback=handle_task_rescheduled
    )
    logger.info(f"Resource_events consumer started")
    return queue