import json
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

    created_tasks = []

    for task in tasks:
        task_payload = {
            "title": task["title"],
            "description": task.get("description"),
            "estimated_hours": task.get("estimated_hours"),
            "event_id": event_id
        }

        created = await create_task(task_payload)
        created_tasks.append(created)

    return {
        "event_name": data.get("event_name"),
        "tasks_created": created_tasks
    }