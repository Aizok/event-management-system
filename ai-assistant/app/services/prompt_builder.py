def sanitize_input(text: str) -> str:
    forbidden_patterns = [
        "ignore previous instructions",
        "system:",
        "assistant:",
        "you are chatgpt",
        "act as",
    ]

    lowered = text.lower()

    for pattern in forbidden_patterns:
        if pattern in lowered:
            raise ValueError("Potential prompt injection detected")

    return text

def build_event_prompt(description: str) -> str:
    description=sanitize_input(description)
    return f"""
You are an event planning assistant.

Analyze the following event description and generate structured JSON.

Requirements:
- Extract event name
- Generate a list of tasks
- Each task must have:
  - title
  - description
  - estimated_hours

Return ONLY JSON in this format:
{{
  "event_name": "...",
  "tasks": [
    {{
      "title": "...",
      "description": "...",
      "estimated_hours": 5
    }}
  ]
}}

Do not include explanations, comments, or text outside JSON.

Event description:
{description}
"""
