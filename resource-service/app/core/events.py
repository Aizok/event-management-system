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

    if start_time is None or end_time is None:
        logger.error(
            "TaskRescheduled received with null start/end "
            f"(task_id={task_id}, start_time={start_time}, end_time={end_time}, data={data})"
        )
        return

    logger.info(f"TaskRescheduled received (task_id={task_id})")
    logger.info(f"TaskRescheduled window (task_id={task_id}): {start_time} — {end_time}")
    print(
        f"[TaskRescheduled] handler start task_id={task_id} window={start_time} — {end_time}",
        flush=True,
    )

    async with AsyncSessionLocal() as db:
        allocations=await resource_crud.get_allocations_by_task(db, task_id)
        logger.info(f"Allocations to shift for task_id={task_id}: {len(allocations)}")
        print(f"[TaskRescheduled] allocations to shift: {len(allocations)}", flush=True)
        allocations=sorted(allocations, key=lambda a: a.date_start)
        processed = 0
        for alloc in allocations:
            try:
                before = (alloc.id, alloc.date_start, alloc.date_end, alloc.status)
                await resource_crud.shift_allocation_to_fit_task(
                    db,
                    alloc,
                    start_time,
                    end_time
                )
                after = (alloc.id, alloc.date_start, alloc.date_end, alloc.status)
                logger.info(f"Allocation shift (task_id={task_id}) before={before} after={after}")
                print(
                    f"[TaskRescheduled] allocation {alloc.id} before={before} after={after}",
                    flush=True,
                )
                processed += 1
            except Exception as e:
                logger.error(f"Allocation shift error: {e}", exc_info=True)
                print(f"[TaskRescheduled] allocation {alloc.id} error: {e}", flush=True)

        await db.commit()
        print(f"[TaskRescheduled] commit done, processed={processed}", flush=True)


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