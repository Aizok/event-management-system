from pydantic import BaseModel, ConfigDict

class TaskDependencyResponse(BaseModel):
    id: int
    task_id: int
    depends_on_task_id: int

    model_config = ConfigDict(from_attributes=True)

class TaskDependencyListResponse(BaseModel):
    task_id: int
    depends_on: list[int]