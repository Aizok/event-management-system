import json
import asyncio
from pydantic import ValidationError

from ..core.openai_client import generate_completion
from .prompt_builder import build_event_prompt
from ..core.task_client import create_task
from ..schemas.ai import TaskItem, CreatedTask
from ..core.auth_client import get_service_token
import logging

logger=logging.getLogger(__name__)
MAX_TASKS = 30
MAX_DESCRIPTION = 2100
MAX_AI_RESPONSE = 20000
semaphore=asyncio.Semaphore(5)

def extract_json(text: str) -> str:
    brace_stack = 0
    start = None

    for i, ch in enumerate(text):
        if ch == "{":
            if brace_stack == 0:
                start = i
            brace_stack += 1
        elif ch == "}":
            if brace_stack > 0:
                brace_stack -= 1
            if brace_stack == 0 and start is not None:
                return text[start:i + 1]

    raise ValueError("No valid JSON object found")


async def create_task_limited(task_payload: dict, token: str):
    async with semaphore:
        return await create_task(task_payload, token)


async def generate_event_plan(description: str, event_id: int):
    description = description[:MAX_DESCRIPTION]
    prompt = build_event_prompt(description)

    raw_response = await generate_completion(prompt)
    raw_response = raw_response[:MAX_AI_RESPONSE]

    try:
        clean_json = extract_json(raw_response)
        data = json.loads(clean_json)
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
    token = await get_service_token()

    tasks_to_create = [
        create_task_limited({
            "title": t.title,
            "description": t.description,
            "estimated_hours": t.estimated_hours,
            "event_id": event_id
        }, token)
        for t in validated_tasks
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
        "errors": errors if errors else None
    }
