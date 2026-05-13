import asyncio
from openai import OpenAI, OpenAIError
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from .config import settings
from ..services.prompt_builder import SYSTEM_GUARD

client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    timeout=60.0
)


async def generate_completion(prompt: str) -> str:
    try:
        system_message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": SYSTEM_GUARD,
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

        content = response.choices[0].message.content
        if content is None or not str(content).strip():
            raise RuntimeError("AI_ERROR empty model response")
        return str(content)

    except Exception as e:
        error_str=str(e)
        if "429" in error_str or "rate" in error_str.lower():
            raise RuntimeError("AI_RATE_LIMIT")
        raise RuntimeError(f"AI_ERROR {e}")