from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
            name="userrole",
        ),
        default=UserRole.CUSTOMER,
        nullable=False,
    )

    status: Mapped[UserStatus] = mapped_column(
        SAEnum(
            UserStatus,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
            name="userstatus",
        ),
        default=UserStatus.ACTIVE,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tickets_created = relationship(
        "Ticket",
        foreign_keys="Ticket.customer_id",
        back_populates="customer",
    )

    assigned_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_agent_id",
        back_populates="assigned_agent",
    )

    comments = relationship(
        "TicketComment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    attachments = relationship(
        "TicketAttachment",
        back_populates="uploaded_by_user",
        cascade="all, delete-orphan",
    )

    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )