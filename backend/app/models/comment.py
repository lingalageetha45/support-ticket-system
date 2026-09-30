from datetime import datetime, timezone
from sqlalchemy import Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # internal notes for agents
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    ticket = relationship("Ticket", back_populates="comments")
    user = relationship("User", back_populates="comments")
