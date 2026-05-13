from fastapi import APIRouter, HTTPException, status, Depends
from ....schemas.ai import GenerateRequest, GenerateResponse, CommitGeneratedTasksRequest, CommitGeneratedTasksResponse
from ....services.ai_service import generate_event_plan, commit_generated_tasks
from ....core.security import get_current_profile_id

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_plan(request: GenerateRequest, _profile_id: int = Depends(get_current_profile_id)):
    try:
        result = await generate_event_plan(
            description=request.description,
            event_id=request.event_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:

        if "AI_RATE_LIMIT" in str(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service is rate limited. Try again later."
            )
    
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed {e}"
        )


@router.post("/commit", response_model=CommitGeneratedTasksResponse)
async def commit_plan(request: CommitGeneratedTasksRequest, user_id: int = Depends(get_current_profile_id)):
    try:
        return await commit_generated_tasks(request, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        if "AI_RATE_LIMIT" in str(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service is rate limited. Try again later.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Commit failed: {e}",
        )
