from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TicketPriority, TicketStatus


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    ticket_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(
            TicketStatus,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
            name="ticketstatus",
        ),
        default=TicketStatus.OPEN,
        nullable=False,
    )

    priority: Mapped[TicketPriority] = mapped_column(
        SAEnum(
            TicketPriority,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
            name="ticketpriority",
        ),
        default=TicketPriority.MEDIUM,
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_categories.id"),
        nullable=False,
        index=True,
    )

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer = relationship(
        "User",
        foreign_keys=[customer_id],
        back_populates="tickets_created",
    )

    assigned_agent = relationship(
        "User",
        foreign_keys=[assigned_agent_id],
        back_populates="assigned_tickets",
    )

    category = relationship(
        "TicketCategory",
        back_populates="tickets",
    )

    comments = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )

    attachments = relationship(
        "TicketAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )

    status_history = relationship(
        "TicketStatusHistory",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketStatusHistory.created_at",
    )

    notifications = relationship(
        "Notification",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_tickets_status_priority",
            "status",
            "priority",
        ),
        Index(
            "ix_tickets_customer_status",
            "customer_id",
            "status",
        ),
        Index(
            "ix_tickets_agent_status",
            "assigned_agent_id",
            "status",
        ),
    )


class TicketStatusHistory(Base):
    __tablename__ = "ticket_status_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    old_status: Mapped[TicketStatus | None] = mapped_column(
        SAEnum(
            TicketStatus,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
            name="ticketstatus",
        ),
        nullable=True,
    )

    new_status: Mapped[TicketStatus] = mapped_column(
        SAEnum(
            TicketStatus,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
            name="ticketstatus",
        ),
        nullable=False,
    )

    changed_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    ticket = relationship(
        "Ticket",
        back_populates="status_history",
    )

    changed_by = relationship(
        "User",
    )