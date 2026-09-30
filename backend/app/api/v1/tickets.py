from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import (
    get_admin_user,
    get_agent_or_admin,
    get_client_ip,
    get_current_user,
)
from app.core.database import get_db
from app.core.exceptions import (
    ForbiddenException,
    InvalidStatusTransition,
    NotFoundException,
    ValidationException,
)
from app.models.audit import AuditLog
from app.models.category import TicketCategory
from app.models.enums import (
    SLA_HOURS,
    STATUS_TRANSITIONS,
    TicketPriority,
    TicketStatus,
    UserRole,
    UserStatus,
)
from app.models.notification import Notification, NotificationType
from app.models.ticket import Ticket, TicketStatusHistory
from app.models.user import User
from app.schemas.common import PaginationMeta, PaginatedResponse, ResponseModel
from app.schemas.ticket import (
    TicketAssign,
    TicketCreate,
    TicketListOut,
    TicketOut,
    TicketStatusUpdate,
    TicketUpdate,
)


router = APIRouter()


def generate_ticket_number(db: Session) -> str:
    last = db.query(Ticket).order_by(Ticket.id.desc()).first()
    next_id = (last.id + 1) if last else 1

    return (
        f"TKT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-"
        f"{next_id:05d}"
    )


def calculate_due_date(priority: TicketPriority) -> datetime:
    hours = SLA_HOURS.get(priority, 48)
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def create_notification(
    db: Session,
    user_id: int,
    ticket_id: int,
    ntype: NotificationType,
    title: str,
    message: str,
):
    notification = Notification(
        user_id=user_id,
        ticket_id=ticket_id,
        type=ntype,
        title=title,
        message=message,
    )

    db.add(notification)


def audit(
    db: Session,
    user_id: int,
    action: str,
    entity: str,
    entity_id: int,
    ip: str | None,
    meta=None,
):
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            ip_address=ip,
            metadata_=meta,
        )
    )


def can_access_ticket(user: User, ticket: Ticket) -> bool:
    if user.role == UserRole.ADMIN:
        return True

    if user.role == UserRole.AGENT:
        return (
            ticket.assigned_agent_id == user.id
            or ticket.assigned_agent_id is None
        )

    if user.role == UserRole.CUSTOMER:
        return ticket.customer_id == user.id

    return False


@router.post(
    "",
    response_model=ResponseModel[TicketOut],
    status_code=201,
)
def create_ticket(
    data: TicketCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = (
        db.query(TicketCategory)
        .filter(
            TicketCategory.id == data.category_id,
            TicketCategory.is_active == True,
        )
        .first()
    )

    if not category:
        raise ValidationException("Invalid or inactive category")

    ticket = Ticket(
        ticket_number=generate_ticket_number(db),
        title=data.title,
        description=data.description,
        status=TicketStatus.OPEN,
        priority=data.priority,
        customer_id=current_user.id,
        category_id=data.category_id,
        due_date=calculate_due_date(data.priority),
    )

    db.add(ticket)
    db.flush()

    history = TicketStatusHistory(
        ticket_id=ticket.id,
        old_status=None,
        new_status=TicketStatus.OPEN,
        changed_by_id=current_user.id,
        note="Ticket created",
    )

    db.add(history)

    create_notification(
        db,
        current_user.id,
        ticket.id,
        NotificationType.TICKET_CREATED,
        "Ticket Created",
        f"Your ticket {ticket.ticket_number} has been created.",
    )

    audit(
        db,
        current_user.id,
        "TICKET_CREATED",
        "ticket",
        ticket.id,
        get_client_ip(request),
    )

    db.commit()
    db.refresh(ticket)

    return ResponseModel(
        data=TicketOut.model_validate(ticket),
        message="Ticket created",
    )


@router.get(
    "",
    response_model=PaginatedResponse[TicketListOut],
)
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    category_id: Optional[int] = None,
    assigned_agent_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|updated_at|due_date|priority|status)$",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)

    # Authorization scope
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(
            Ticket.customer_id == current_user.id
        )

    elif current_user.role == UserRole.AGENT:
        query = query.filter(
            or_(
                Ticket.assigned_agent_id == current_user.id,
                Ticket.assigned_agent_id.is_(None),
            )
        )

    # Filters
    if status:
        query = query.filter(Ticket.status == status)

    if priority:
        query = query.filter(Ticket.priority == priority)

    if category_id:
        query = query.filter(
            Ticket.category_id == category_id
        )

    if assigned_agent_id:
        query = query.filter(
            Ticket.assigned_agent_id == assigned_agent_id
        )

    if customer_id and current_user.role == UserRole.ADMIN:
        query = query.filter(
            Ticket.customer_id == customer_id
        )

    if search:
        like = f"%{search}%"

        query = query.filter(
            or_(
                Ticket.title.ilike(like),
                Ticket.description.ilike(like),
                Ticket.ticket_number.ilike(like),
            )
        )

    if date_from:
        query = query.filter(
            Ticket.created_at >= date_from
        )

    if date_to:
        query = query.filter(
            Ticket.created_at <= date_to
        )

    total = query.count()

    sort_column = getattr(
        Ticket,
        sort_by,
        Ticket.created_at,
    )

    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    tickets = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        data=[
            TicketListOut.model_validate(ticket)
            for ticket in tickets
        ],
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=(
                (total + page_size - 1) // page_size
                if total
                else 1
            ),
        ),
    )


@router.get(
    "/{ticket_id}",
    response_model=ResponseModel[TicketOut],
)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.customer),
            joinedload(Ticket.assigned_agent),
            joinedload(Ticket.category),
        )
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise NotFoundException("Ticket not found")

    if not can_access_ticket(current_user, ticket):
        raise ForbiddenException(
            "You do not have access to this ticket"
        )

    return ResponseModel(
        data=TicketOut.model_validate(ticket)
    )


@router.patch(
    "/{ticket_id}",
    response_model=ResponseModel[TicketOut],
)
def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise NotFoundException("Ticket not found")

    if not can_access_ticket(current_user, ticket):
        raise ForbiddenException("Access denied")

    if (
        ticket.status == TicketStatus.CLOSED
        and current_user.role != UserRole.ADMIN
    ):
        raise ForbiddenException(
            "Closed tickets cannot be modified"
        )

    if data.title is not None:
        ticket.title = data.title

    if data.description is not None:
        ticket.description = data.description

    if data.category_id is not None:
        category = (
            db.query(TicketCategory)
            .filter(
                TicketCategory.id == data.category_id,
                TicketCategory.is_active == True,
            )
            .first()
        )

        if not category:
            raise ValidationException(
                "Invalid or inactive category"
            )

        ticket.category_id = data.category_id

    if (
        data.priority is not None
        and data.priority != ticket.priority
    ):
        ticket.priority = data.priority
        ticket.due_date = calculate_due_date(
            data.priority
        )

    if (
        data.status is not None
        and data.status != ticket.status
    ):
        allowed = STATUS_TRANSITIONS.get(
            ticket.status,
            [],
        )

        if data.status not in allowed:
            raise InvalidStatusTransition(
                f"Cannot transition from "
                f"{ticket.status.value} to "
                f"{data.status.value}"
            )

        old_status = ticket.status
        ticket.status = data.status

        if data.status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.now(
                timezone.utc
            )

        if data.status == TicketStatus.CLOSED:
            ticket.closed_at = datetime.now(
                timezone.utc
            )

        db.add(
            TicketStatusHistory(
                ticket_id=ticket.id,
                old_status=old_status,
                new_status=data.status,
                changed_by_id=current_user.id,
                note="Status updated via ticket update",
            )
        )

        create_notification(
            db,
            ticket.customer_id,
            ticket.id,
            NotificationType.TICKET_STATUS_CHANGED,
            "Status Updated",
            f"Ticket {ticket.ticket_number} is now "
            f"{data.status.value}",
        )

        if ticket.assigned_agent_id:
            create_notification(
                db,
                ticket.assigned_agent_id,
                ticket.id,
                NotificationType.TICKET_STATUS_CHANGED,
                "Status Updated",
                f"Ticket {ticket.ticket_number} is now "
                f"{data.status.value}",
            )

    db.commit()
    db.refresh(ticket)

    audit(
        db,
        current_user.id,
        "TICKET_UPDATED",
        "ticket",
        ticket.id,
        get_client_ip(request),
    )

    return ResponseModel(
        data=TicketOut.model_validate(ticket),
        message="Ticket updated",
    )


@router.post(
    "/{ticket_id}/assign",
    response_model=ResponseModel[TicketOut],
)
def assign_ticket(
    ticket_id: int,
    data: TicketAssign,
    request: Request,
    current_user: User = Depends(get_agent_or_admin),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise NotFoundException("Ticket not found")

    agent = (
        db.query(User)
        .filter(
            User.id == data.agent_id,
            User.role == UserRole.AGENT,
        )
        .first()
    )

    if not agent:
        raise ValidationException("Invalid agent")

    if (
        not agent.is_active
        or agent.status != UserStatus.ACTIVE
    ):
        raise ValidationException(
            "Cannot assign to inactive agent",
            code="INACTIVE_AGENT",
        )

    old_agent = ticket.assigned_agent_id

    ticket.assigned_agent_id = agent.id

    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS

        db.add(
            TicketStatusHistory(
                ticket_id=ticket.id,
                old_status=TicketStatus.OPEN,
                new_status=TicketStatus.IN_PROGRESS,
                changed_by_id=current_user.id,
                note=f"Assigned to {agent.full_name}",
            )
        )

    if old_agent:
        notification_type = (
            NotificationType.TICKET_REASSIGNED
        )
    else:
        notification_type = (
            NotificationType.TICKET_ASSIGNED
        )

    create_notification(
        db,
        agent.id,
        ticket.id,
        notification_type,
        "Ticket Assigned",
        f"You have been assigned ticket "
        f"{ticket.ticket_number}",
    )

    create_notification(
        db,
        ticket.customer_id,
        ticket.id,
        notification_type,
        "Ticket Assigned",
        f"Your ticket {ticket.ticket_number} "
        f"has been assigned to an agent",
    )

    audit(
        db,
        current_user.id,
        "TICKET_ASSIGNED",
        "ticket",
        ticket.id,
        get_client_ip(request),
        {"agent_id": agent.id},
    )

    db.commit()
    db.refresh(ticket)

    return ResponseModel(
        data=TicketOut.model_validate(ticket),
        message="Ticket assigned",
    )


@router.post(
    "/{ticket_id}/status",
    response_model=ResponseModel[TicketOut],
)
def change_status(
    ticket_id: int,
    data: TicketStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise NotFoundException("Ticket not found")

    if not can_access_ticket(current_user, ticket):
        raise ForbiddenException("Access denied")

    # Customers should not change ticket workflow status.
    if current_user.role == UserRole.CUSTOMER:
        raise ForbiddenException(
            "Customers cannot change ticket status"
        )

    allowed = STATUS_TRANSITIONS.get(
        ticket.status,
        [],
    )

    if data.status not in allowed:
        raise InvalidStatusTransition(
            f"Cannot transition from "
            f"{ticket.status.value} to "
            f"{data.status.value}"
        )

    old_status = ticket.status
    ticket.status = data.status

    if data.status == TicketStatus.RESOLVED:
        ticket.resolved_at = datetime.now(
            timezone.utc
        )

        create_notification(
            db,
            ticket.customer_id,
            ticket.id,
            NotificationType.TICKET_RESOLVED,
            "Ticket Resolved",
            f"Ticket {ticket.ticket_number} "
            f"has been resolved",
        )

    if data.status == TicketStatus.CLOSED:
        ticket.closed_at = datetime.now(
            timezone.utc
        )

        create_notification(
            db,
            ticket.customer_id,
            ticket.id,
            NotificationType.TICKET_CLOSED,
            "Ticket Closed",
            f"Ticket {ticket.ticket_number} "
            f"has been closed",
        )

    db.add(
        TicketStatusHistory(
            ticket_id=ticket.id,
            old_status=old_status,
            new_status=data.status,
            changed_by_id=current_user.id,
            note=data.note,
        )
    )

    create_notification(
        db,
        ticket.customer_id,
        ticket.id,
        NotificationType.TICKET_STATUS_CHANGED,
        "Status Changed",
        f"Ticket {ticket.ticket_number} is now "
        f"{data.status.value}",
    )

    if (
        ticket.assigned_agent_id
        and ticket.assigned_agent_id != current_user.id
    ):
        create_notification(
            db,
            ticket.assigned_agent_id,
            ticket.id,
            NotificationType.TICKET_STATUS_CHANGED,
            "Status Changed",
            f"Ticket {ticket.ticket_number} is now "
            f"{data.status.value}",
        )

    audit(
        db,
        current_user.id,
        "STATUS_CHANGED",
        "ticket",
        ticket.id,
        get_client_ip(request),
        {
            "from": old_status.value,
            "to": data.status.value,
        },
    )

    db.commit()
    db.refresh(ticket)

    return ResponseModel(
        data=TicketOut.model_validate(ticket),
        message="Status updated",
    )


@router.delete(
    "/{ticket_id}",
    response_model=ResponseModel,
)
def delete_ticket(
    ticket_id: int,
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise NotFoundException("Ticket not found")

    db.delete(ticket)

    audit(
        db,
        current_user.id,
        "TICKET_DELETED",
        "ticket",
        ticket_id,
        get_client_ip(request),
    )

    db.commit()

    return ResponseModel(
        message="Ticket deleted"
    )