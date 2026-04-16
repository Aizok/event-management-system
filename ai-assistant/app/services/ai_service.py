import json
from ..core.openai_client import generate_completion
from ..services.prompt_builder import build_event_prompt


async def generate_event_plan(description: str) -> dict:
    prompt = build_event_prompt(description)

    raw_response = await generate_completion(prompt)

    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        raise ValueError("Invalid AI response format")
