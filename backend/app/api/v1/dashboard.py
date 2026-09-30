from datetime import datetime, timezone

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.ticket import Ticket
from app.models.enums import (
    UserRole,
    UserStatus,
    TicketStatus,
    TicketPriority,
)
from app.models.notification import Notification, NotificationType
from app.models.audit import AuditLog
from app.schemas.ticket import DashboardStats
from app.schemas.common import ResponseModel


router = APIRouter()


def create_sla_breach_notifications(db: Session):
    """
    Find active tickets whose SLA deadline has passed and create
    SLA breach notifications.

    A notification is created only once per ticket/user combination.
    """

    now = datetime.now(timezone.utc)

    overdue_tickets = (
        db.query(Ticket)
        .filter(
            Ticket.due_date.isnot(None),
            Ticket.due_date < now,
            Ticket.status.in_(
                [
                    TicketStatus.OPEN,
                    TicketStatus.IN_PROGRESS,
                ]
            ),
        )
        .all()
    )

    for ticket in overdue_tickets:
        recipients = set()

        # Customer should know that the ticket has breached SLA.
        recipients.add(ticket.customer_id)

        # Assigned agent should also be notified.
        if ticket.assigned_agent_id:
            recipients.add(ticket.assigned_agent_id)

        for user_id in recipients:
            existing = (
                db.query(Notification)
                .filter(
                    Notification.ticket_id == ticket.id,
                    Notification.user_id == user_id,
                    Notification.type == NotificationType.SLA_BREACHED,
                )
                .first()
            )

            if existing:
                continue

            notification = Notification(
                user_id=user_id,
                ticket_id=ticket.id,
                type=NotificationType.SLA_BREACHED,
                title="SLA Breached",
                message=(
                    f"Ticket {ticket.ticket_number} has exceeded "
                    f"its SLA deadline."
                ),
            )

            db.add(notification)

            audit_log = AuditLog(
                user_id=None,
                action="SLA_BREACHED",
                entity="ticket",
                entity_id=ticket.id,
                ip_address="system",
                metadata_={
                    "ticket_number": ticket.ticket_number,
                    "due_date": (
                        ticket.due_date.isoformat()
                        if ticket.due_date
                        else None
                    ),
                },
            )

            db.add(audit_log)

    db.commit()


@router.get(
    "/stats",
    response_model=ResponseModel[DashboardStats],
)
def get_dashboard_stats(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    # Check SLA breaches in the background so the dashboard
    # response does not have to wait for the notification work.
    background_tasks.add_task(
        create_sla_breach_notifications,
        db,
    )

    base = db.query(Ticket)

    if current_user.role == UserRole.CUSTOMER:
        base = base.filter(
            Ticket.customer_id == current_user.id
        )

    elif current_user.role == UserRole.AGENT:
        base = base.filter(
            Ticket.assigned_agent_id == current_user.id
        )

    total = base.count()

    open_c = base.filter(
        Ticket.status == TicketStatus.OPEN
    ).count()

    in_prog = base.filter(
        Ticket.status == TicketStatus.IN_PROGRESS
    ).count()

    resolved = base.filter(
        Ticket.status == TicketStatus.RESOLVED
    ).count()

    closed = base.filter(
        Ticket.status == TicketStatus.CLOSED
    ).count()

    overdue = base.filter(
        Ticket.due_date < now,
        Ticket.status.in_(
            [
                TicketStatus.OPEN,
                TicketStatus.IN_PROGRESS,
            ]
        ),
    ).count()

    critical = base.filter(
        Ticket.priority == TicketPriority.CRITICAL
    ).count()

    stats = DashboardStats(
        total_tickets=total,
        open_tickets=open_c,
        in_progress_tickets=in_prog,
        resolved_tickets=resolved,
        closed_tickets=closed,
        overdue_tickets=overdue,
        critical_tickets=critical,
    )

    # Admin-specific statistics
    if current_user.role == UserRole.ADMIN:
        stats.total_customers = (
            db.query(User)
            .filter(User.role == UserRole.CUSTOMER)
            .count()
        )

        stats.total_agents = (
            db.query(User)
            .filter(User.role == UserRole.AGENT)
            .count()
        )

        stats.active_agents = (
            db.query(User)
            .filter(
                User.role == UserRole.AGENT,
                User.is_active == True,
                User.status == UserStatus.ACTIVE,
            )
            .count()
        )

    # Agent-specific statistics
    elif current_user.role == UserRole.AGENT:
        my_base = db.query(Ticket).filter(
            Ticket.assigned_agent_id == current_user.id
        )

        stats.my_open_tickets = (
            my_base
            .filter(
                Ticket.status.in_(
                    [
                        TicketStatus.OPEN,
                        TicketStatus.IN_PROGRESS,
                    ]
                )
            )
            .count()
        )

        stats.my_overdue_tickets = (
            my_base
            .filter(
                Ticket.due_date < now,
                Ticket.status.in_(
                    [
                        TicketStatus.OPEN,
                        TicketStatus.IN_PROGRESS,
                    ]
                ),
            )
            .count()
        )

        stats.my_resolved_tickets = (
            my_base
            .filter(
                Ticket.status == TicketStatus.RESOLVED
            )
            .count()
        )

    return ResponseModel(data=stats)