import uuid
from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    action_type: str = "other"
    priority: str = "medium"
    deadline: datetime | None = None
    email_id: uuid.UUID | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    action_type: str | None = None
    priority: str | None = None
    deadline: datetime | None = None
    completed: bool | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    email_id: uuid.UUID | None
    user_id: uuid.UUID
    title: str
    description: str | None
    action_type: str
    priority: str
    deadline: datetime | None
    completed: bool
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskFilter(BaseModel):
    completed: bool | None = None
    priority: str | None = None
    action_type: str | None = None
