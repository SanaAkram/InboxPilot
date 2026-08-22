import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class JobApplication(Base):
    """
    A tracked job application, grouped by company. Created/updated automatically
    when an email is classified as `job_application` (see ai_service.extract_job_details
    and job_application_service.upsert_from_email), or added manually by the user.
    """

    __tablename__ = "inb_pilot_job_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inb_pilot_users.id", ondelete="CASCADE"))
    email_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inb_pilot_emails.id", ondelete="SET NULL"), nullable=True)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    company_domain: Mapped[str | None] = mapped_column(String)
    role_title: Mapped[str | None] = mapped_column(String)
    # applied | interviewing | offer | rejected | withdrawn
    status: Mapped[str] = mapped_column(String, default="applied")
    # ai | manual
    source: Mapped[str] = mapped_column(String, default="manual")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="job_applications")
    email: Mapped["Email | None"] = relationship()
