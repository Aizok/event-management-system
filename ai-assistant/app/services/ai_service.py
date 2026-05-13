import json
import asyncio
from pydantic import ValidationError
from datetime import datetime, timedelta, timezone

from ..core.openai_client import generate_completion
from .prompt_builder import build_event_prompt
from ..schemas.ai import (
    TaskItem,
    CreatedTask,
    TaskTiming,
    TaskPriority,
    ProposedTask,
    GenerateResponse,
    CommitGeneratedTasksRequest,
    CommitGeneratedTasksResponse,
)
from ..core.task_client import create_task
from ..core.event_client import get_event
from ..core.auth_client import get_service_token
import logging

logger=logging.getLogger(__name__)
MAX_TASKS = 30
MAX_DESCRIPTION = 2100
MAX_AI_RESPONSE = 20000
MIN_GAP=0
MAX_GAP=1800
semaphore=asyncio.Semaphore(5)


def extract_json(text: str) -> dict:
    decoder = json.JSONDecoder()

    for i, ch in enumerate(text):
        if ch in "{[":
            try:
                obj, _ = decoder.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue

    raise ValueError("No valid JSON found in AI response")


def get_deadline(end, priority):
    if priority == "high":
        return end + timedelta(hours=1)
    if priority == "medium":
        return end + timedelta(hours=2)
    return end + timedelta(hours=3)


def build_task_payload_with_timing(
        tasks: list[TaskItem],
        event_start: datetime,
        event_end: datetime,
        event_id: int
):
    now=datetime.now(timezone.utc)

    before_tasks=[t for t in tasks if t.timing == TaskTiming.BEFORE]
    during_tasks=[t for t in tasks if t.timing == TaskTiming.DURING]
    after_tasks=[t for t in tasks if t.timing == TaskTiming.AFTER]

    result=[]

    def distribute(task_list, window_start, window_end):
        if not task_list:
            return []

        priority_order = {
            TaskPriority.HIGH: 0,
            TaskPriority.MEDIUM: 1,
            TaskPriority.LOW: 2
        }

        sorted_tasks = sorted(
            task_list,
            key=lambda task: priority_order.get(task.priority, 1)
        )
        if window_start < now:
            window_start = now

        if window_end <= window_start:
            window_start = now
            window_end = now + timedelta(hours=len(task_list) or 1)
            logger.warning("Invalid time window, fallback applied")

        window_seconds = (window_end - window_start).total_seconds()

        total_duration_seconds = sum(
            (t.estimated_hours or 1) * 3600 for t in sorted_tasks
        )

        if total_duration_seconds > window_seconds:
            scale = window_seconds / total_duration_seconds

            sorted_tasks = [
                TaskItem(
                    **t.model_dump(exclude={"estimated_hours"}),
                    estimated_hours=max(round((t.estimated_hours or 1) * scale), 1)
                )
                for t in sorted_tasks
            ]

            total_duration_seconds = window_seconds

        free_time = max(window_seconds - total_duration_seconds, 0)
        gap = free_time / max(len(sorted_tasks) - 1, 1)
        gap = max(MIN_GAP, min(gap, MAX_GAP))
        # минимум 0, максимум 30 минут

        current_time=window_start

        items = []
        for i, t in enumerate(sorted_tasks):
            duration=timedelta(hours=t.estimated_hours or 1)
            start=current_time

            if start + duration > window_end:
                start = window_end - duration
                start = max(start, window_start)
            end=start+duration

            items.append((t, start, end))
            if i<len(sorted_tasks)-1:
                current_time=end+timedelta(seconds=gap)
        return items

    result+=distribute(before_tasks, now, event_start)
    result+=distribute(during_tasks, event_start, event_end)

    after_end=event_end+timedelta(days=1)
    result+=distribute(after_tasks, event_end, after_end)

    return [
        {
            "title": t.title,
            "description": t.description,
            "event_id": event_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "deadline": get_deadline(end, t.priority.value).isoformat(),
            "priority": t.priority.value,
            "assignee_id": None
        }
        for (t, start, end) in result
    ]


async def create_task_limited(task_payload: dict, token: str, owner_id: int):
    async with semaphore:
        return await create_task(task_payload, token, owner_id)


async def build_event_plan_drafts(description: str, event_id: int) -> tuple[str, list[dict]]:
    description = description[:MAX_DESCRIPTION]
    prompt = build_event_prompt(description)

    raw_response = await generate_completion(prompt)
    if not isinstance(raw_response, str) or not raw_response.strip():
        raise ValueError("Пустой ответ модели, повторите запрос")
    raw_response = raw_response[:MAX_AI_RESPONSE]

    try:
        data = extract_json(raw_response)
        if not isinstance(data, dict):
            raise ValueError("AI returned invalid structure")
    except Exception:
        logger.error(f"AI response parsing failed: {raw_response[:500]}")
        raise ValueError("Invalid AI response format")

    raw_tasks = data.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raise ValueError("AI returned invalid tasks format")
    raw_tasks = raw_tasks[: MAX_TASKS * 2]

    validated_tasks: list[TaskItem] = []

    for t in raw_tasks:
        try:
            validated_tasks.append(TaskItem(**t))
        except ValidationError:
            continue

    if not validated_tasks:
        raise ValueError("AI returned no valid tasks")

    original_count = len(validated_tasks)

    if original_count > MAX_TASKS:
        logger.warning(f"AI returned too many tasks, truncated to {MAX_TASKS}")

    validated_tasks = validated_tasks[:MAX_TASKS]

    event = await get_event(event_id)
    event_start = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))
    event_end = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))

    payloads = build_task_payload_with_timing(
        validated_tasks,
        event_start,
        event_end,
        event_id,
    )

    event_name = data.get("event_name")
    if not isinstance(event_name, str) or not event_name.strip():
        event_name = "Сгенерированный план"

    return event_name, payloads


async def generate_event_plan(description: str, event_id: int) -> dict:
    event_name, payloads = await build_event_plan_drafts(description, event_id)
    tasks = [ProposedTask(**p) for p in payloads]
    return GenerateResponse(event_name=event_name, tasks=tasks, errors=[]).model_dump(mode="json")


async def commit_generated_tasks(request: CommitGeneratedTasksRequest, user_id: int) -> dict:
    token = await get_service_token()
    tasks_to_create = [
        create_task_limited(task.model_dump(mode="json"), token, user_id)
        for task in request.tasks
    ]

    results = await asyncio.gather(*tasks_to_create, return_exceptions=True)

    created_tasks: list[CreatedTask] = []
    errors: list[str] = []
    for r in results:
        if isinstance(r, Exception):
            logger.exception("Task creation failed")
            errors.append(f"Не удалось создать задачу: {type(r).__name__}")
            continue
        try:
            created_tasks.append(CreatedTask(**r))
        except ValidationError as e:
            logger.error(f"Invalid task response: {r}, error: {e}")
            errors.append("Некорректный ответ task-service при создании задачи")
            continue

    return CommitGeneratedTasksResponse(tasks=created_tasks, errors=errors).model_dump(mode="json")