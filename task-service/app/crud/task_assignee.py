from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.task import Task
from ..models.task_assignee import TaskAssignee, TaskAssigneeStatus


class TaskAssigneeCRUD:
    async def list_for_task(self, db: AsyncSession, task_id: int) -> list[TaskAssignee]:
        q = (
            select(TaskAssignee)
            .where(TaskAssignee.task_id == task_id)
            .order_by(TaskAssignee.created_at.asc(), TaskAssignee.id.asc())
        )
        r = await db.execute(q)
        return list(r.scalars().all())

    async def get_row(
        self, db: AsyncSession, task_id: int, user_id: int
    ) -> TaskAssignee | None:
        q = select(TaskAssignee).where(
            TaskAssignee.task_id == task_id,
            TaskAssignee.user_id == user_id,
        )
        r = await db.execute(q)
        return r.scalar_one_or_none()

    async def is_accepted(self, db: AsyncSession, task_id: int, user_id: int) -> bool:
        row = await self.get_row(db, task_id, user_id)
        return row is not None and row.status == TaskAssigneeStatus.ACCEPTED

    async def invite(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        user_id: int,
        invited_by: int,
    ) -> TaskAssignee:
        row = TaskAssignee(
            task_id=task_id,
            user_id=user_id,
            status=TaskAssigneeStatus.PENDING,
            invited_by=invited_by,
        )
        db.add(row)
        await db.flush()
        await db.refresh(row)
        return row

    async def accept(
        self, db: AsyncSession, task_id: int, user_id: int
    ) -> TaskAssignee | None:
        row = await self.get_row(db, task_id, user_id)
        if not row or row.status != TaskAssigneeStatus.PENDING:
            return None
        now = datetime.now(timezone.utc)
        row.status = TaskAssigneeStatus.ACCEPTED
        row.responded_at = now
        await db.flush()
        await db.refresh(row)
        return row

    async def decline(
        self, db: AsyncSession, task_id: int, user_id: int
    ) -> TaskAssignee | None:
        row = await self.get_row(db, task_id, user_id)
        if not row or row.status != TaskAssigneeStatus.PENDING:
            return None
        now = datetime.now(timezone.utc)
        row.status = TaskAssigneeStatus.DECLINED
        row.responded_at = now
        await db.flush()
        await db.refresh(row)
        return row

    async def delete_row(self, db: AsyncSession, task_id: int, user_id: int) -> bool:
        res = await db.execute(
            delete(TaskAssignee).where(
                TaskAssignee.task_id == task_id,
                TaskAssignee.user_id == user_id,
            )
        )
        if not res.rowcount:
            return False
        await db.flush()
        return True

    async def list_pending_invitations_for_user(
        self, db: AsyncSession, user_id: int
    ) -> list[tuple[TaskAssignee, Task]]:
        q = (
            select(TaskAssignee, Task)
            .join(Task, Task.id == TaskAssignee.task_id)
            .where(
                TaskAssignee.user_id == user_id,
                TaskAssignee.status == TaskAssigneeStatus.PENDING,
            )
            .order_by(TaskAssignee.created_at.desc())
        )
        r = await db.execute(q)
        return list(r.all())

    async def list_sent_pending_invitations_for_user(
        self, db: AsyncSession, invited_by: int
    ) -> list[tuple[TaskAssignee, Task]]:
        q = (
            select(TaskAssignee, Task)
            .join(Task, Task.id == TaskAssignee.task_id)
            .where(
                TaskAssignee.invited_by == invited_by,
                TaskAssignee.status == TaskAssigneeStatus.PENDING,
            )
            .order_by(TaskAssignee.created_at.desc())
        )
        r = await db.execute(q)
        return list(r.all())


task_assignee_crud = TaskAssigneeCRUD()
