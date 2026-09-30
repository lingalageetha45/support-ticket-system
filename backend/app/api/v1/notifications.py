from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.ticket import NotificationOut
from app.schemas.common import ResponseModel, PaginatedResponse, PaginationMeta

router = APIRouter()


@router.get("", response_model=PaginatedResponse[NotificationOut])
def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        q = q.filter(Notification.is_read == False)
    total = q.count()
    items = q.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        data=[NotificationOut.model_validate(n) for n in items],
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=(total + page_size - 1) // page_size or 1),
    )


@router.post("/{notification_id}/read", response_model=ResponseModel)
def mark_as_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if n:
        n.is_read = True
        db.commit()
    return ResponseModel(message="Marked as read")


@router.post("/read-all", response_model=ResponseModel)
def mark_all_as_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == current_user.id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return ResponseModel(message="All notifications marked as read")
