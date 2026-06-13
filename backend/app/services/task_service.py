import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task


async def create_tasks(
    db: AsyncSession,
    user_id: uuid.UUID,
    email_id: uuid.UUID,
    extracted_tasks: list[dict],
) -> list[Task]:
    created = []
    for t in extracted_tasks:
        deadline = None
        if t.get("deadline"):
            try:
                deadline = datetime.fromisoformat(t["deadline"]).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        task = Task(
            user_id=user_id,
            email_id=email_id,
            title=t["title"],
            action_type=t.get("action_type", "other"),
            priority=t.get("priority", "medium"),
            deadline=deadline,
        )
        db.add(task)
        created.append(task)
    await db.commit()
    return created


async def complete_task(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        return None
    task.completed = True
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task


async def get_pending_tasks(db: AsyncSession, user_id: uuid.UUID) -> list[Task]:
    result = await db.execute(
        select(Task)
        .where(Task.user_id == user_id, Task.completed.is_(False))
        .order_by(Task.created_at.desc())
    )
    return list(result.scalars().all())
