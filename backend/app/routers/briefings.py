from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.daily_briefing import DailyBriefing
from app.models.email import Email
from app.models.task import Task
from app.models.user import User
from app.schemas.briefing import BriefingOut
from app.services import ai_service

router = APIRouter()


@router.post("/generate", response_model=BriefingOut, status_code=201)
async def generate_briefing(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Gather latest 30 emails
    emails_result = await db.execute(
        select(Email)
        .where(Email.user_id == current_user.id)
        .order_by(Email.received_at.desc())
        .limit(30)
    )
    emails = list(emails_result.scalars().all())

    # Gather pending tasks
    tasks_result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id, Task.completed.is_(False))
        .order_by(Task.created_at.desc())
        .limit(15)
    )
    tasks = list(tasks_result.scalars().all())

    emails_summary = [
        {
            "sender": e.sender_email or e.sender_name or "Unknown",
            "subject": e.subject or "(no subject)",
            "category": e.category,
            "priority": e.priority,
        }
        for e in emails
    ]
    tasks_summary = [
        {
            "title": t.title,
            "priority": t.priority,
            "deadline": t.deadline.date().isoformat() if t.deadline else None,
        }
        for t in tasks
    ]

    briefing_text = await ai_service.generate_briefing(emails_summary, tasks_summary)

    briefing = DailyBriefing(user_id=current_user.id, briefing=briefing_text)
    db.add(briefing)
    await db.commit()
    await db.refresh(briefing)
    return briefing


@router.get("/latest", response_model=BriefingOut)
async def get_latest_briefing(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DailyBriefing)
        .where(DailyBriefing.user_id == current_user.id)
        .order_by(DailyBriefing.generated_at.desc())
        .limit(1)
    )
    briefing = result.scalar_one_or_none()
    if briefing is None:
        raise HTTPException(status_code=404, detail="No briefing generated yet")
    return briefing
