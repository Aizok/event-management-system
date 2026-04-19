import asyncio
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from .config import settings


client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    timeout=15.0
)


async def generate_completion(prompt: str) -> str:
    try:
        system_message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": "You are an expert event planner assistant.",
        }

        user_message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": prompt,
        }

        messages = [system_message, user_message]

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=settings.AI_MODEL,
            messages=messages,
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        raise RuntimeError("AI generation failed") from e