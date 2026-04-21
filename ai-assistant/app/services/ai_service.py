import json
import asyncio
from pydantic import ValidationError
from datetime import datetime, timedelta, timezone

from ..core.openai_client import generate_completion
from .prompt_builder import build_event_prompt
from ..schemas.ai import TaskItem, CreatedTask, TaskTiming
from ..core.task_client import create_task
from ..core.event_client import get_event
from ..core.auth_client import get_service_token
import logging

logger=logging.getLogger(__name__)
MAX_TASKS = 30
MAX_DESCRIPTION = 2100
MAX_AI_RESPONSE = 20000
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


def build_task_payload_with_timing(
        tasks: list[TaskItem],
        event_start: datetime,
        event_end: datetime,
        event_id: int,
        user_id: int
):
    now=datetime.now(timezone.utc)

    before_tasks=[t for t in tasks if t.timing == TaskTiming.BEFORE]
    during_tasks=[t for t in tasks if t.timing == TaskTiming.DURING]
    after_tasks=[t for t in tasks if t.timing == TaskTiming.AFTER]

    result=[]

    def distribute(task_list, window_start, window_end):
        if not task_list:
            return []
        if window_end<=window_start:
            window_start=window_end - timedelta(hours=len(task_list) or 1)
            if window_start<now:
                window_start=now

        window=(window_end-window_start).total_seconds()
        step=window/max(len(task_list), 1)

        items=[]
        for i, t in enumerate(task_list):
            start=window_start+timedelta(seconds=step*i)
            duration=timedelta(hours=t.estimated_hours or 1)
            end=start+duration

            if end>window_end:
                end=window_end

            items.append((t, start, end))
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
            "deadline": (end + timedelta(hours=2)).isoformat(),
            "priority": "medium",
            "owner_id": user_id,
            "assignee_id": None
        }
        for (t, start, end) in result
    ]


async def create_task_limited(task_payload: dict, token: str):
    async with semaphore:
        return await create_task(task_payload, token)


async def generate_event_plan(description: str, event_id: int, user_id: int):
    description = description[:MAX_DESCRIPTION]
    prompt = build_event_prompt(description)

    raw_response = await generate_completion(prompt)
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
    raw_tasks = raw_tasks[:MAX_TASKS*2]

    validated_tasks: list[TaskItem] = []

    for t in raw_tasks:
        try:
            validated_tasks.append(TaskItem(**t))
        except ValidationError:
            continue

    if not validated_tasks:
        raise ValueError("AI returned no valid tasks")

    original_count=len(validated_tasks)

    if original_count > MAX_TASKS:
        logger.warning(f"AI returned too many tasks, truncated to {MAX_TASKS}")

    validated_tasks = validated_tasks[:MAX_TASKS]

    event=await get_event(event_id)
    event_start=datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))
    event_end=datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))

    payloads=build_task_payload_with_timing(
        validated_tasks,
        event_start,
        event_end,
        event_id,
        user_id
    )

    token = await get_service_token()
    tasks_to_create=[
        create_task_limited(payload, token)
        for payload in payloads
    ]

    results = await asyncio.gather(*tasks_to_create, return_exceptions=True)

    created_tasks = []
    errors = []
    for r in results:
        if isinstance(r, Exception):
            logger.exception("Task creation failed")
            errors.append(f"Task creation failed: {type(r).__name__}")
            continue
        try:
            created_tasks.append(CreatedTask(**r))
        except ValidationError:
            continue

    event_name = data.get("event_name")
    if not isinstance(event_name, str) or not event_name.strip():
        event_name = "Generated Event"

    return {
        "event_name": event_name,
        "tasks": created_tasks,
        "errors": errors
    }
