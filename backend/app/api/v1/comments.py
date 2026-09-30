
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
)
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User
from app.models.ticket import Ticket
from app.models.comment import TicketComment
from app.models.enums import UserRole, TicketStatus
from app.models.notification import Notification, NotificationType
from app.models.audit import AuditLog
from app.schemas.ticket import CommentCreate, CommentUpdate, CommentOut
from app.schemas.common import ResponseModel


router = APIRouter()


def can_access_ticket_comments(user: User, ticket: Ticket) -> bool:
    """
    Check whether the current user can access comments
    for the given ticket.
    """
    if user.role == UserRole.ADMIN:
        return True

    if user.role == UserRole.AGENT:
        # Agents can access comments on tickets assigned to them
        # and on tickets that are not assigned yet.
        return (
            ticket.assigned_agent_id == user.id
            or ticket.assigned_agent_id is None
        )

    if user.role == UserRole.CUSTOMER:
        return ticket.customer_id == user.id

    return False


@router.post(
    "/{ticket_id}/comments",
    response_model=ResponseModel[CommentOut],
    status_code=201,
)
def add_comment(
    ticket_id: int,
    data: CommentCreate,
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

    if not can_access_ticket_comments(current_user, ticket):
        raise ForbiddenException("Access denied")

    if ticket.status == TicketStatus.CLOSED:
        raise ValidationException(
            "Cannot comment on closed tickets. Please reopen first."
        )

    if data.is_internal and current_user.role == UserRole.CUSTOMER:
        raise ForbiddenException(
            "Customers cannot create internal comments"
        )

    comment = TicketComment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        message=data.message,
        is_internal=data.is_internal,
    )

    db.add(comment)

    # Flush so the database generates the comment ID
    # before creating the audit record.
    db.flush()

    # Notify the customer and assigned agent.
    recipients = set()

    if ticket.customer_id != current_user.id:
        recipients.add(ticket.customer_id)

    if (
        ticket.assigned_agent_id
        and ticket.assigned_agent_id != current_user.id
    ):
        recipients.add(ticket.assigned_agent_id)

    for user_id in recipients:
        # Internal comments must not notify the customer.
        if (
            data.is_internal
            and user_id == ticket.customer_id
        ):
            continue

        notification = Notification(
            user_id=user_id,
            ticket_id=ticket_id,
            type=NotificationType.NEW_COMMENT,
            title="New Comment",
            message=f"New comment on ticket {ticket.ticket_number}",
        )

        db.add(notification)

    audit_log = AuditLog(
        user_id=current_user.id,
        action="COMMENT_ADDED",
        entity="comment",
        entity_id=comment.id,
        ip_address=get_client_ip(request),
    )

    db.add(audit_log)

    db.commit()
    db.refresh(comment)

    return ResponseModel(
        data=CommentOut.model_validate(comment),
        message="Comment added",
    )


@router.get(
    "/{ticket_id}/comments",
    response_model=ResponseModel[list[CommentOut]],
)
def list_comments(
    ticket_id: int,
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

    if not can_access_ticket_comments(current_user, ticket):
        raise ForbiddenException("Access denied")

    query = (
        db.query(TicketComment)
        .options(joinedload(TicketComment.user))
        .filter(TicketComment.ticket_id == ticket_id)
    )

    # Customers cannot see internal comments.
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(
            TicketComment.is_internal == False
        )

    comments = (
        query
        .order_by(TicketComment.created_at.asc())
        .all()
    )

    return ResponseModel(
        data=[
            CommentOut.model_validate(comment)
            for comment in comments
        ]
    )


@router.patch(
    "/{ticket_id}/comments/{comment_id}",
    response_model=ResponseModel[CommentOut],
)
def update_comment(
    ticket_id: int,
    comment_id: int,
    data: CommentUpdate,
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

    if not can_access_ticket_comments(current_user, ticket):
        raise ForbiddenException("Access denied")

    comment = (
        db.query(TicketComment)
        .filter(
            TicketComment.id == comment_id,
            TicketComment.ticket_id == ticket_id,
        )
        .first()
    )

    if not comment:
        raise NotFoundException("Comment not found")

    # Admins can moderate comments.
    # Customers and agents can only edit their own comments.
    if current_user.role != UserRole.ADMIN:
        if comment.user_id != current_user.id:
            raise ForbiddenException(
                "You can only edit your own comments"
            )

    comment.message = data.message

    db.commit()
    db.refresh(comment)

    return ResponseModel(
        data=CommentOut.model_validate(comment),
        message="Comment updated",
    )


@router.delete(
    "/{ticket_id}/comments/{comment_id}",
    response_model=ResponseModel,
)
def delete_comment(
    ticket_id: int,
    comment_id: int,
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

    if not can_access_ticket_comments(current_user, ticket):
        raise ForbiddenException("Access denied")

    comment = (
        db.query(TicketComment)
        .filter(
            TicketComment.id == comment_id,
            TicketComment.ticket_id == ticket_id,
        )
        .first()
    )

    if not comment:
        raise NotFoundException("Comment not found")

    # Admins can moderate comments.
    # Customers and agents can only delete their own comments.
    if current_user.role != UserRole.ADMIN:
        if comment.user_id != current_user.id:
            raise ForbiddenException(
                "You can only delete your own comments"
            )

    db.delete(comment)
    db.commit()

    return ResponseModel(message="Comment deleted")
