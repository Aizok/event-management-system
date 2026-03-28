from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...crud.event import event_crud
from ...models.event import Event

async def get_event_or_404(
        event_id: int,
        db: AsyncSession=Depends(get_db)
) -> Event:
    event=await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event
