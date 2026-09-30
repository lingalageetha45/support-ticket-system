from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.audit import AuditLog
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter()


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int]
    action: str
    entity: str
    entity_id: Optional[int]
    ip_address: Optional[str]
    created_at: datetime


@router.get("", response_model=PaginatedResponse[AuditOut])
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    entity: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    total = q.count()
    items = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        data=[AuditOut.model_validate(a) for a in items],
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=(total + page_size - 1) // page_size or 1),
    )
