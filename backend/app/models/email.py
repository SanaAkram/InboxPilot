import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Email(Base):
    __tablename__ = "inb_pilot_emails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inb_pilot_users.id", ondelete="CASCADE"))
    gmail_message_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    thread_id: Mapped[str | None] = mapped_column(String)
    # inbound | outbound. For outbound (sent) mail, sender_name/sender_email hold the
    # *recipient* (the counterparty) instead of the user's own address - see
    # gmail_service._parse_message. This keeps job-application matching (which keys off
    # sender_email's domain) working unmodified regardless of direction.
    direction: Mapped[str] = mapped_column(String, default="inbound")
    sender_name: Mapped[str | None] = mapped_column(String)
    sender_email: Mapped[str | None] = mapped_column(String)
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    category: Mapped[str] = mapped_column(String, default="other")
    priority: Mapped[str] = mapped_column(String, default="medium")
    status: Mapped[str] = mapped_column(String, default="new")
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="emails")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="email", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="email", cascade="all, delete-orphan")
    ai_extractions: Mapped[list["AIExtraction"]] = relationship(back_populates="email", cascade="all, delete-orphan")
