from fastapi import APIRouter, HTTPException, status
from ....schemas.ai import GenerateRequest, GenerateResponse
from ....services.ai_service import generate_event_plan

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_plan(request: GenerateRequest):
    try:
        result = await generate_event_plan(request.description)
        return result
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI generation failed")
