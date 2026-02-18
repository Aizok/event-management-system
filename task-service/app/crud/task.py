from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.task import Task
from ..schemas.task import TaskCreate, TaskUpdate

class TaskCRUD:
    def create(self, db: Session, obj_in: TaskCreate, owner_id: int) -> Task:
        db_obj=Task(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, task_id: int) -> Optional[Task]:
        return db.query(Task).filter(Task.id==task_id).first()

    def get_multi(self, db: Session, skip: int=0, limit: int=100, owner_id: int = None) -> List[Task]:
        query=db.query(Task)
        if owner_id:
            query=query.filter(Task.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()

    def get_by_event(self, db: Session, event_id: int, owner_id: int = None) -> List[Task]:
        query=db.query(Task).filter(Task.event_id==event_id)
        if owner_id:
            query=query.filter(Task.owner_id==owner_id)
        return query.all()

    def update(self, db: Session, task_id: int, obj_in: TaskUpdate, owner_id: int) -> Task:
        db_obj=self.get(db, task_id)
        if not db_obj:
            raise ValueError("Task not found")

        #TODO Проверка по роли

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj


    def delete(self, db: Session, task_id: int) -> bool:
        obj=self.get(db, task_id)
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False

task_crud=TaskCRUD()