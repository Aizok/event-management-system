import json
import asyncio
import re
from pydantic import ValidationError

from ..core.openai_client import generate_completion
from .prompt_builder import build_event_prompt
from ..core.task_client import create_task
from ..schemas.ai import TaskItem, CreatedTask


def extract_json(text: str) -> str:
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in AI response")
    return match.group(0)


async def generate_event_plan(description: str, event_id: int):
    prompt = build_event_prompt(description)

    raw_response = await generate_completion(prompt)

    try:
        clean_json = extract_json(raw_response)
        data = json.loads(clean_json)
    except Exception:
        raise ValueError("Invalid AI response format")

    raw_tasks = data.get("tasks", [])

    validated_tasks: list[TaskItem] = []

    for t in raw_tasks:
        try:
            validated_tasks.append(TaskItem(**t))
        except ValidationError:
            continue

    if not validated_tasks:
        raise ValueError("AI returned no valid tasks")

    tasks_to_create = [
        create_task({
            "title": t.title,
            "description": t.description,
            "estimated_hours": t.estimated_hours,
            "event_id": event_id
        })
        for t in validated_tasks
    ]

    results = await asyncio.gather(*tasks_to_create, return_exceptions=True)

    created_tasks = []
    for r in results:
        if isinstance(r, Exception):
            continue
        try:
            created_tasks.append(CreatedTask(**r))
        except ValidationError:
            continue

    event_name = data.get("event_name") or "Generated Event"

    return {
        "event_name": event_name,
        "tasks": created_tasks
    }