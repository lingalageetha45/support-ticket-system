from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import NotificationType


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="SET NULL"),
        nullable=True,
    )

    type: Mapped[NotificationType] = mapped_column(
        SAEnum(
            NotificationType,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
            name="notificationtype",
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="notifications",
    )

    ticket = relationship(
        "Ticket",
        back_populates="notifications",
    )