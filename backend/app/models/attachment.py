
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    uploaded_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    original_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    ticket = relationship(
        "Ticket",
        back_populates="attachments",
    )

    uploaded_by_user = relationship(
        "User",
        back_populates="attachments",
    )
