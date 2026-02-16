from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ....core.database import get_db
from ....core.security import get_current_user_id
from ....crud.task import task_crud
from ....schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    return task_crud.create(db=db, obj_in=task_in)

@router.get("/", response_model=List[TaskResponse])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return task_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/{task_id}", response_model=TaskResponse)
def read_task(task_id: int, db: Session = Depends(get_db)):
    Task = task_crud.get(db, task_id)
    if not Task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Task

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return task_crud.update(db=db, task_id=task_id, obj_in=task_in, owner_id=user_id)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)  
def delete_task(task_id: int, db: Session = Depends(get_db)):
    success = task_crud.delete(db, task_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
