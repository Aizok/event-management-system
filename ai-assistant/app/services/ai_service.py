import json
import asyncio
from ..core.openai_client import generate_completion
from .prompt_builder import build_event_prompt
from ..core.task_client import create_task


async def generate_event_plan(description: str, event_id: int):
    prompt = build_event_prompt(description)

    raw_response = await generate_completion(prompt)

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        raise ValueError("Invalid AI response format")

    tasks = data.get("tasks", [])

    tasks_to_create = [
        create_task({
            "title": t["title"],
            "description": t.get("description"),
            "estimated_hours": t.get("estimated_hours"),
            "event_id": event_id
        })
        for t in tasks
    ]

    created_tasks = await asyncio.gather(*tasks_to_create)

    return {
        "event_name": data.get("event_name"),
        "tasks_created": created_tasks
    }