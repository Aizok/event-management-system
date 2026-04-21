from fastapi import APIRouter, HTTPException, status, Depends
from ....schemas.ai import GenerateRequest, GenerateResponse
from ....services.ai_service import generate_event_plan
from ....core.security import get_current_user_id

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_plan(request: GenerateRequest, user_id: int = Depends(get_current_user_id)):
    try:
        result = await generate_event_plan(
            description=request.description,
            event_id=request.event_id,
            user_id=user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI generation failed"
        )
