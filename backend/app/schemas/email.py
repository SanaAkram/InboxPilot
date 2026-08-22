import uuid
from datetime import datetime
from pydantic import BaseModel


class EmailOut(BaseModel):
    id: uuid.UUID
    gmail_message_id: str
    thread_id: str | None
    direction: str
    sender_name: str | None
    sender_email: str | None
    subject: str | None
    body: str | None
    snippet: str | None
    received_at: datetime | None
    category: str
    priority: str
    status: str
    processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailListOut(BaseModel):
    id: uuid.UUID
    gmail_message_id: str
    direction: str
    sender_name: str | None
    sender_email: str | None
    subject: str | None
    snippet: str | None
    received_at: datetime | None
    category: str
    priority: str
    status: str
    processed: bool

    model_config = {"from_attributes": True}


class EmailFilter(BaseModel):
    category: str | None = None
    priority: str | None = None
    status: str | None = None
    page: int = 1
    limit: int = 20


class EmailStatusUpdate(BaseModel):
    status: str
