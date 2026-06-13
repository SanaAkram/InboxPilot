import uuid
from datetime import datetime
from pydantic import BaseModel


class BriefingOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    briefing: str
    generated_at: datetime

    model_config = {"from_attributes": True}
