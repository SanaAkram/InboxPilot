import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.job_application import JobApplicationCreate, JobApplicationOut, JobApplicationUpdate
from app.services import job_application_service

router = APIRouter()


@router.get("", response_model=list[JobApplicationOut])
async def list_job_applications(
    status: str | None = Query(None),
    waiting_only: bool = Query(False),
    search: str | None = Query(None),
    stale_days: int = Query(14, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await job_application_service.list_for_user(
        db, current_user.id, status=status, waiting_only=waiting_only, search=search, stale_days=stale_days
    )


@router.post("", response_model=JobApplicationOut, status_code=201)
async def create_job_application(
    body: JobApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = await job_application_service.create_manual(db, current_user.id, body.model_dump())
    return job_application_service.to_out_dict(app)


@router.patch("/{app_id}", response_model=JobApplicationOut)
async def update_job_application(
    app_id: uuid.UUID,
    body: JobApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = await job_application_service.update(db, current_user.id, app_id, body.model_dump(exclude_none=True))
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return job_application_service.to_out_dict(app)


@router.delete("/{app_id}", status_code=204)
async def delete_job_application(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = await job_application_service.delete(db, current_user.id, app_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Application not found")


@router.post("/scan", response_model=dict)
async def scan_for_job_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Classify unprocessed emails (batched) and link any job-application ones into the tracker."""
    return await job_application_service.backfill_from_processed_emails(db, current_user.id)
