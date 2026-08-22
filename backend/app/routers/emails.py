import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.ai_extraction import AIExtraction
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.models.user import User
from app.schemas.email import EmailListOut, EmailOut, EmailStatusUpdate
from app.services import ai_service, gmail_service, job_application_service, task_service

router = APIRouter()


@router.get("", response_model=dict)
async def list_emails(
    category: str | None = Query(None),
    priority: str | None = Query(None),
    status: str | None = Query(None),
    direction: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Email).where(Email.user_id == current_user.id)
    if category:
        query = query.where(Email.category == category)
    if priority:
        query = query.where(Email.priority == priority)
    if status:
        query = query.where(Email.status == status)
    if direction:
        query = query.where(Email.direction == direction)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    query = query.order_by(Email.received_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    emails = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [EmailListOut.model_validate(e) for e in emails],
    }


@router.get("/{email_id}", response_model=EmailOut)
async def get_email(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.user_id == current_user.id)
    )
    email = result.scalar_one_or_none()
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("/sync")
async def sync_emails(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch latest emails from Gmail and store them in the database."""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.user_id == current_user.id,
            EmailAccount.provider == "gmail",
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=400, detail="No Gmail account connected")

    messages = await gmail_service.sync_emails(
        access_token=account.access_token,
        refresh_token=account.refresh_token,
        token_expiry=account.token_expiry,
    )

    new_count = 0
    seen_in_batch: set[str] = set()
    for msg in messages:
        # A message CC'd/sent to the user's own address carries both INBOX and SENT
        # labels, so it can appear in both the inbound and outbound fetches within the
        # same sync call - dedupe against this batch too, not just already-committed
        # rows, since nothing here is committed (and thus visible to the query below)
        # until the loop finishes. Without this, a duplicate gmail_message_id (a unique
        # column) throws an IntegrityError on commit and fails the whole sync.
        if msg["gmail_message_id"] in seen_in_batch:
            continue
        seen_in_batch.add(msg["gmail_message_id"])

        existing = await db.execute(
            select(Email).where(Email.gmail_message_id == msg["gmail_message_id"])
        )
        if existing.scalar_one_or_none() is not None:
            continue
        email_row = Email(user_id=current_user.id, **msg)
        db.add(email_row)
        new_count += 1

    await db.commit()
    return {"synced": new_count, "total_fetched": len(messages)}


@router.post("/process/{email_id}")
async def process_email(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run AI classification and task extraction on a single email."""
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.user_id == current_user.id)
    )
    email = result.scalar_one_or_none()
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")

    classification = await ai_service.classify_email(
        subject=email.subject or "",
        body=email.body or "",
        sender=f"{email.sender_name} <{email.sender_email}>",
        direction=email.direction,
    )

    email.category = classification.get("category", "other")
    email.priority = classification.get("priority", "medium")
    email.processed = True

    extraction = AIExtraction(
        email_id=email.id,
        raw_response=classification,
        category=classification.get("category"),
        priority=classification.get("priority"),
        confidence=classification.get("confidence"),
    )
    db.add(extraction)

    tasks_result = await ai_service.extract_tasks(
        subject=email.subject or "",
        body=email.body or "",
        sender=f"{email.sender_name} <{email.sender_email}>",
    )
    extracted = tasks_result.get("tasks", [])
    created_tasks = await task_service.create_tasks(
        db, current_user.id, email.id, extracted
    )

    job_application = None
    if email.category == "job_application":
        job_details = await ai_service.extract_job_details(
            subject=email.subject or "",
            body=email.body or "",
            sender=f"{email.sender_name} <{email.sender_email}>",
            direction=email.direction,
        )
        job_application = await job_application_service.upsert_from_email(
            db, current_user.id, email, job_details
        )

    await db.commit()
    return {
        "classification": classification,
        "tasks_created": len(created_tasks),
        "job_application_id": str(job_application.id) if job_application else None,
    }


@router.patch("/{email_id}/status")
async def update_email_status(
    email_id: uuid.UUID,
    body: EmailStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.user_id == current_user.id)
    )
    email = result.scalar_one_or_none()
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    email.status = body.status
    await db.commit()
    return {"id": str(email_id), "status": body.status}
