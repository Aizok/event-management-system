from sqlalchemy import select, func, update, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple
from ..models.task import Task, TaskStatus, TaskPriority
from ..models.task_history import TaskHistory
from ..schemas.task import TaskCreate, TaskUpdate
from ..crud.task_dependency import task_dependency_crud
from datetime import datetime, timezone, timedelta

START_GRACE_PERIOD = timedelta(minutes=5)

def is_late_start(task: Task):
    if not task.actual_start_time:
        return False

    return task.actual_start_time > task.start_time + START_GRACE_PERIOD


def serialize(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return str(value) if value is not None else None


def calculate_delay(task: Task) -> timedelta | None:
    if not task.actual_end_time:
        return None

    return task.actual_end_time - task.end_time


class TaskCRUD:
    async def create(self, db: AsyncSession, obj_in: TaskCreate, owner_id: int) -> Task:
        db_obj=Task(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        await db.flush()

        history = TaskHistory(
            task_id=db_obj.id,
            changed_by=owner_id,
            field="created",
            old_value=None,
            new_value="task created"
        )
        db.add(history)

        await self.sync_blocked_status(db, db_obj)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get(self, db: AsyncSession, task_id: int) -> Optional[Task]:
        query = select(Task).where(Task.id == task_id)
        result=await db.execute(query)
        task=result.scalar_one_or_none()

        if task:
            task.is_late_start=is_late_start(task)
        return task


    async def get_multi(self, db: AsyncSession, skip: int=0, limit: int=100) -> List[Task]:
        query = (
            select(Task)
            .order_by(Task.start_time.asc(), Task.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        tasks = result.scalars().all()
        for task in tasks:
            task.is_late_start=is_late_start(task)
        return tasks


    async def get_by_event(self, db: AsyncSession, event_id: int) -> List[Task]:
        query=select(Task).where(Task.event_id==event_id).order_by(Task.start_time.asc(), Task.id.asc())
        result=await db.execute(query)
        tasks = result.scalars().all()
        for task in tasks:
            task.is_late_start=is_late_start(task)
        return tasks


    async def get_by_assignee(self, db: AsyncSession, user_id: int):
        query=select(Task).where(Task.assignee_id == user_id).order_by(Task.start_time.asc(), Task.id.asc())
        result=await db.execute(query)
        tasks=result.scalars().all()

        for task in tasks:
            task.is_late_start=is_late_start(task)

        return tasks


    async def get_by_event_and_assignee(self, db, event_id: int, user_id: int):
        query = select(Task).where(
            Task.event_id == event_id,
            Task.assignee_id == user_id
        ).order_by(Task.start_time.asc(), Task.id.asc())

        result = await db.execute(query)
        tasks = result.scalars().all()

        for task in tasks:
            task.is_late_start = is_late_start(task)

        return tasks


    async def get_by_event_ids(self, db: AsyncSession, event_ids: List[int] ,skip: int=0, limit: int=100):
        query = (
            select(Task)
            .where(Task.event_id.in_(event_ids))
            .order_by(Task.start_time.asc(), Task.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result=await db.execute(query)
        tasks = result.scalars().all()
        for task in tasks:
            task.is_late_start = is_late_start(task)
        return tasks


    async def update(self, db: AsyncSession, task_id: int, obj_in: TaskUpdate, user_id: int) -> Optional[Task]:
        db_obj=await self.get(db, task_id)
        if not db_obj:
            return None

        update_data=obj_in.model_dump(exclude_unset=True)
        if not update_data:
            return db_obj

        is_executor=db_obj.assignee_id == user_id
        if is_executor:
            allowed_fields={"status"}
            forbidden = set(update_data.keys()) - allowed_fields
            if forbidden:
                raise ValueError("Executors can only change status")
            status_value = getattr(update_data.get("status"), "value", update_data.get("status"))
            if status_value not in {"in_progress", "done"}:
                raise ValueError("Executors can only set status to in_progress or done")

        new_status = update_data.get("status", db_obj.status)

        if "status" in update_data and new_status in [TaskStatus.IN_PROGRESS, TaskStatus.DONE]:
            has_blockers = await self.has_unfinished_parents(db, task_id)
            if has_blockers:
                raise ValueError("Task is blocked by unfinished dependencies")

        now=datetime.now(timezone.utc)
        if "status" in update_data:
            if new_status==TaskStatus.IN_PROGRESS:
                if db_obj.actual_start_time is None:
                    db_obj.actual_start_time=now

            if new_status==TaskStatus.DONE:
                if db_obj.actual_end_time is None:
                    db_obj.actual_end_time=now

        new_start = update_data.get("start_time", db_obj.start_time)
        new_end = update_data.get("end_time", db_obj.end_time)
        new_deadline = update_data.get("deadline", db_obj.deadline)

        if new_start >= new_end:
            raise ValueError("start_time must be < end_time")

        if new_end > new_deadline:
            raise ValueError("end_time must be <= deadline")

        for field, value in update_data.items():
            old_value=getattr(db_obj, field)

            if old_value != value:
                history=TaskHistory(
                    task_id=db_obj.id,
                    changed_by=user_id,
                    field=field,
                    old_value=serialize(old_value),
                    new_value=serialize(value)
                )
                db.add(history)
                setattr(db_obj, field, value)

        await db.flush()
        await self.sync_blocked_status(db, db_obj)

        if "start_time" in update_data or "end_time" in update_data:
            await self.recalculate_schedule(db, db_obj.id)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete(self, db: AsyncSession, task_id: int) -> bool:
        async with db.begin():
            parent_ids=await task_dependency_crud.get_parent_ids(db, task_id)
            child_ids=await task_dependency_crud.get_child_ids(db, task_id)

            if parent_ids and child_ids:
                for child_id in child_ids:
                    for parent_id in parent_ids:
                        if child_id==parent_id:
                            continue

                        try:
                            async with db.begin_nested():
                                await task_dependency_crud.create(
                                    db,
                                    task_id=child_id,
                                    depends_on_task_id=parent_id,
                                    commit=False
                                )
                        except ValueError:
                            continue
                for child_id in child_ids:
                    await self.recalculate_schedule(db, child_id)

            query=delete(Task).where(Task.id==task_id)
            result=await db.execute(query)

        return result.rowcount > 0


    async def update_overdue_tasks(self, db: AsyncSession):
        now=datetime.now(timezone.utc)

        query=(
            update(Task)
            .where(
                Task.deadline < now,
                Task.actual_end_time.is_(None),
                Task.status.notin_([TaskStatus.DONE, TaskStatus.OVERDUE])
            )
            .values(status=TaskStatus.OVERDUE)
        )

        await db.execute(query)
        await db.commit()


    async def recalculate_schedule(self, db: AsyncSession, task_id: int, visited=None):
        from ..core.events import publish_task_rescheduled

        task=await self.get(db, task_id)
        if not task:
            return

        if visited is None:
            visited=set()
        if task_id in visited:
            return
        visited.add(task_id)

        children_ids=await task_dependency_crud.get_child_ids(db, task_id)

        for child_id in children_ids:
            child=await self.get(db, child_id)
            if not child:
                continue

            parent_ids=await task_dependency_crud.get_parent_ids(db, child_id)

            parents=[]
            for pid in parent_ids:
                parent = await self.get(db, pid)
                if parent:
                    parents.append(parent)

            if not parents:
                continue

            max_end=max(p.actual_end_time or p.end_time for p in parents)

            if child.start_time < max_end:
                delta=max_end - child.start_time

                child.start_time+=delta
                child.end_time+=delta

                await db.flush()
                await self.sync_blocked_status(db, child)
                await publish_task_rescheduled(db, child.id)
                # Рекурсивно вниз
                await self.recalculate_schedule(db, child_id)


    async def has_unfinished_parents(self, db: AsyncSession, task_id: int) -> bool:
        parent_ids=await task_dependency_crud.get_parent_ids(db, task_id)

        if not parent_ids:
            return False

        query=select(Task.status).where(Task.id.in_(parent_ids))
        result=await db.execute(query)
        statuses=result.scalars().all()

        return any(status != TaskStatus.DONE for status in statuses)


    async def sync_blocked_status(self, db: AsyncSession, task: Task):
        # Не меняем статус завершенных и просроченных задач
        if task.status in [TaskStatus.DONE, TaskStatus.OVERDUE]:
            return

        has_blockers=await self.has_unfinished_parents(db, task.id)
        if has_blockers:
            # Меняем статус, если задача ещё на завершена
            if task.status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS]:
                task.status=TaskStatus.BLOCKED
        else:
            # Разблокировать, если была blocked
            if task.status == TaskStatus.BLOCKED:
                task.status=TaskStatus.TODO


    async def get_critical_tasks(self, db: AsyncSession):
        query=select(Task).where(
            Task.actual_end_time.is_not(None),
            Task.actual_end_time>Task.end_time
        )
        result=await db.execute(query)
        return result.scalars().all()

    def _accessible_task_conditions(
        self,
        *,
        is_admin: bool,
        profile_id: int,
        allowed_event_ids: List[int],
        event_id: Optional[int],
        status: Optional[TaskStatus],
        priority: Optional[TaskPriority],
        q: Optional[str],
    ) -> List:
        cond: List = []
        if not is_admin:
            if allowed_event_ids:
                cond.append(
                    or_(Task.event_id.in_(allowed_event_ids), Task.assignee_id == profile_id)
                )
            else:
                cond.append(Task.assignee_id == profile_id)
        if event_id is not None:
            cond.append(Task.event_id == event_id)
        if status is not None:
            cond.append(Task.status == status)
        if priority is not None:
            cond.append(Task.priority == priority)
        if q and str(q).strip():
            cond.append(Task.title.ilike(f"%{str(q).strip()}%"))
        return cond

    async def count_accessible_tasks(
        self,
        db: AsyncSession,
        *,
        is_admin: bool,
        profile_id: int,
        allowed_event_ids: List[int],
        event_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        q: Optional[str] = None,
    ) -> int:
        conditions = self._accessible_task_conditions(
            is_admin=is_admin,
            profile_id=profile_id,
            allowed_event_ids=allowed_event_ids,
            event_id=event_id,
            status=status,
            priority=priority,
            q=q,
        )
        stmt = select(func.count()).select_from(Task)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def list_accessible_tasks(
        self,
        db: AsyncSession,
        *,
        is_admin: bool,
        profile_id: int,
        allowed_event_ids: List[int],
        skip: int = 0,
        limit: int = 25,
        event_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        q: Optional[str] = None,
    ) -> List[Task]:
        conditions = self._accessible_task_conditions(
            is_admin=is_admin,
            profile_id=profile_id,
            allowed_event_ids=allowed_event_ids,
            event_id=event_id,
            status=status,
            priority=priority,
            q=q,
        )
        stmt = select(Task)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Task.start_time.asc(), Task.id.asc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        for task in tasks:
            task.is_late_start = is_late_start(task)
        return tasks

    async def metrics_accessible_tasks(
        self,
        db: AsyncSession,
        *,
        is_admin: bool,
        profile_id: int,
        allowed_event_ids: List[int],
    ) -> Tuple[int, int]:
        base = self._accessible_task_conditions(
            is_admin=is_admin,
            profile_id=profile_id,
            allowed_event_ids=allowed_event_ids,
            event_id=None,
            status=None,
            priority=None,
            q=None,
        )
        total_stmt = select(func.count()).select_from(Task)
        overdue_stmt = select(func.count()).select_from(Task).where(Task.status == TaskStatus.OVERDUE)
        if base:
            total_stmt = total_stmt.where(and_(*base))
            overdue_stmt = overdue_stmt.where(and_(*base))
        total_r = await db.execute(total_stmt)
        overdue_r = await db.execute(overdue_stmt)
        return int(total_r.scalar_one() or 0), int(overdue_r.scalar_one() or 0)

task_crud=TaskCRUD()
