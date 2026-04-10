from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class TaskHistoryResponse(BaseModel):
    id: int
    task_id: int
    changed_by: int
    field: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)