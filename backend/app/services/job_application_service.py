import uuid
from datetime import datetime, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email
from app.models.job_application import JobApplication

# Only forward progression through the pipeline updates `status` — a stray later
# email that only re-confirms receipt shouldn't downgrade an "interviewing" row
# back to "applied".
STAGE_RANK = {
    "applied": 0,
    "interviewing": 1,
    "offer": 2,
    "rejected": 2,
    "withdrawn": 2,
    "other": 0,
}

# Statuses that mean the loop is closed — never "awaiting a response".
TERMINAL_STATUSES = {"offer", "rejected", "withdrawn"}

DEFAULT_STALE_DAYS = 14


def _normalize_domain(sender_email: str | None) -> str | None:
    if not sender_email or "@" not in sender_email:
        return None
    domain = sender_email.split("@", 1)[1].strip().lower()
    # Ignore generic ATS/mail-relay domains that don't identify the company.
    generic = {"greenhouse.io", "lever.co", "myworkday.com", "icims.com", "smartrecruiters.com"}
    if domain in generic:
        return None
    return domain or None


def to_out_dict(app: JobApplication, stale_days: int = DEFAULT_STALE_DAYS) -> dict:
    now = datetime.now(timezone.utc)
    last_contact = app.last_contact_at
    days_since_contact = None
    if last_contact is not None:
        if last_contact.tzinfo is None:
            last_contact = last_contact.replace(tzinfo=timezone.utc)
        days_since_contact = (now - last_contact).days

    awaiting_response = (
        app.status not in TERMINAL_STATUSES
        and days_since_contact is not None
        and days_since_contact >= stale_days
    )

    return {
        "id": app.id,
        "email_id": app.email_id,
        "company_name": app.company_name,
        "company_domain": app.company_domain,
        "role_title": app.role_title,
        "status": app.status,
        "source": app.source,
        "applied_at": app.applied_at,
        "last_contact_at": app.last_contact_at,
        "notes": app.notes,
        "awaiting_response": awaiting_response,
        "days_since_contact": days_since_contact,
        "created_at": app.created_at,
    }


async def _find_existing(db: AsyncSession, user_id: uuid.UUID, company_domain: str | None, company_name: str) -> JobApplication | None:
    query = select(JobApplication).where(JobApplication.user_id == user_id)
    if company_domain:
        query = query.where(
            or_(
                JobApplication.company_domain == company_domain,
                JobApplication.company_name.ilike(company_name),
            )
        )
    else:
        query = query.where(JobApplication.company_name.ilike(company_name))
    query = query.order_by(JobApplication.created_at.desc())
    result = await db.execute(query)
    return result.scalars().first()


async def upsert_from_email(
    db: AsyncSession,
    user_id: uuid.UUID,
    email: Email,
    details: dict,
) -> JobApplication | None:
    """Create or update a JobApplication row from AI-extracted job details for one email."""
    if not details.get("is_job_related"):
        return None
    company_name = (details.get("company_name") or "").strip()
    if not company_name:
        return None

    stage = details.get("stage") or "other"
    if stage not in STAGE_RANK:
        stage = "other"

    domain = _normalize_domain(email.sender_email)
    received_at = email.received_at or datetime.now(timezone.utc)

    app = await _find_existing(db, user_id, domain, company_name)
    if app is None:
        app = JobApplication(
            user_id=user_id,
            email_id=email.id,
            company_name=company_name,
            company_domain=domain,
            role_title=details.get("role_title"),
            status=stage,
            source="ai",
            applied_at=received_at,
            last_contact_at=received_at,
        )
        db.add(app)
    else:
        # Only move the tracked stage forward; always refresh "last contact".
        if STAGE_RANK.get(stage, 0) >= STAGE_RANK.get(app.status, 0):
            app.status = stage
        if not app.role_title and details.get("role_title"):
            app.role_title = details["role_title"]
        if app.applied_at is None or received_at < app.applied_at:
            app.applied_at = received_at
        if app.last_contact_at is None or received_at > app.last_contact_at:
            app.last_contact_at = received_at
            app.email_id = email.id
        if not app.company_domain and domain:
            app.company_domain = domain

    await db.flush()
    return app


async def list_for_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: str | None = None,
    waiting_only: bool = False,
    search: str | None = None,
    stale_days: int = DEFAULT_STALE_DAYS,
) -> list[dict]:
    query = select(JobApplication).where(JobApplication.user_id == user_id)
    if status:
        query = query.where(JobApplication.status == status)
    if search:
        like = f"%{search}%"
        query = query.where(
            or_(JobApplication.company_name.ilike(like), JobApplication.role_title.ilike(like))
        )
    query = query.order_by(JobApplication.last_contact_at.desc().nulls_last())
    result = await db.execute(query)
    apps = list(result.scalars().all())

    out = [to_out_dict(a, stale_days) for a in apps]
    if waiting_only:
        out = [o for o in out if o["awaiting_response"]]
    return out


async def get_for_user(db: AsyncSession, user_id: uuid.UUID, app_id: uuid.UUID) -> JobApplication | None:
    result = await db.execute(
        select(JobApplication).where(JobApplication.id == app_id, JobApplication.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_manual(db: AsyncSession, user_id: uuid.UUID, data: dict) -> JobApplication:
    app = JobApplication(
        user_id=user_id,
        source="manual",
        applied_at=data.get("applied_at") or datetime.now(timezone.utc),
        last_contact_at=data.get("applied_at") or datetime.now(timezone.utc),
        **{k: v for k, v in data.items() if k != "applied_at"},
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


async def update(db: AsyncSession, user_id: uuid.UUID, app_id: uuid.UUID, data: dict) -> JobApplication | None:
    app = await get_for_user(db, user_id, app_id)
    if app is None:
        return None
    for field, value in data.items():
        setattr(app, field, value)
    if "status" in data:
        app.last_contact_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(app)
    return app


async def delete(db: AsyncSession, user_id: uuid.UUID, app_id: uuid.UUID) -> bool:
    app = await get_for_user(db, user_id, app_id)
    if app is None:
        return False
    await db.delete(app)
    await db.commit()
    return True


async def backfill_from_processed_emails(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """
    Re-scans emails already classified as `job_application` (e.g. synced before this
    module existed) and links/creates tracker rows for them. Idempotent.
    """
    from app.services import ai_service  # local import to avoid a circular import at module load

    result = await db.execute(
        select(Email)
        .where(Email.user_id == user_id, Email.category == "job_application")
        .order_by(Email.received_at.asc())
    )
    candidates = list(result.scalars().all())

    linked = 0
    for email in candidates:
        details = await ai_service.extract_job_details(
            subject=email.subject or "",
            body=email.body or "",
            sender=f"{email.sender_name} <{email.sender_email}>",
        )
        app = await upsert_from_email(db, user_id, email, details)
        if app is not None:
            linked += 1

    await db.commit()
    return {"scanned": len(candidates), "linked": linked}
