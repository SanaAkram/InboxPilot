import uuid
from datetime import datetime
from pydantic import BaseModel


class JobApplicationCreate(BaseModel):
    company_name: str
    role_title: str | None = None
    status: str = "applied"
    applied_at: datetime | None = None
    notes: str | None = None


class JobApplicationUpdate(BaseModel):
    company_name: str | None = None
    role_title: str | None = None
    status: str | None = None
    notes: str | None = None


class JobApplicationOut(BaseModel):
    id: uuid.UUID
    email_id: uuid.UUID | None
    company_name: str
    company_domain: str | None
    role_title: str | None
    status: str
    source: str
    applied_at: datetime | None
    last_contact_at: datetime | None
    notes: str | None
    awaiting_response: bool
    days_since_contact: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobApplicationFilter(BaseModel):
    status: str | None = None
    waiting_only: bool = False
    search: str | None = None
    stale_days: int = 14
