from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.api.deps import get_admin_user, get_current_user, get_client_ip
from app.models.user import User
from app.models.enums import UserRole, UserStatus
from app.models.audit import AuditLog
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.schemas.common import ResponseModel, PaginatedResponse, PaginationMeta
from app.repositories.user import UserRepository

router = APIRouter()


def audit(db, user_id, action, entity, entity_id, ip, meta=None):
    db.add(AuditLog(user_id=user_id, action=action, entity=entity, entity_id=entity_id, ip_address=ip, metadata_=meta))
    db.commit()


@router.post("", response_model=ResponseModel[UserOut], status_code=201)
def create_user(
    data: UserCreate,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    if repo.get_by_email(data.email):
        raise ConflictException("Email already exists", code="DUPLICATE_EMAIL")
    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    user = repo.create(user)
    audit(db, admin.id, "USER_CREATED", "user", user.id, get_client_ip(request), {"role": user.role.value})
    return ResponseModel(data=UserOut.model_validate(user), message="User created")


@router.get("", response_model=PaginatedResponse[UserOut])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    skip = (page - 1) * page_size
    users, total = repo.list_users(skip=skip, limit=page_size, role=role, status=status, search=search)
    return PaginatedResponse(
        data=[UserOut.model_validate(u) for u in users],
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=(total + page_size - 1) // page_size),
    )


@router.get("/{user_id}", response_model=ResponseModel[UserOut])
def get_user(user_id: int, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise NotFoundException("User not found")
    return ResponseModel(data=UserOut.model_validate(user))


@router.patch("/{user_id}", response_model=ResponseModel[UserOut])
def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise NotFoundException("User not found")
    if data.email and data.email.lower() != user.email:
        if repo.get_by_email(data.email):
            raise ConflictException("Email already exists")
        user.email = data.email.lower()
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.status is not None:
        user.status = data.status
        user.is_active = data.status == UserStatus.ACTIVE
    repo.update(user)
    audit(db, admin.id, "USER_UPDATED", "user", user.id, get_client_ip(request))
    return ResponseModel(data=UserOut.model_validate(user), message="User updated")


@router.post("/{user_id}/activate", response_model=ResponseModel[UserOut])
def activate_user(user_id: int, request: Request, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise NotFoundException("User not found")
    user.status = UserStatus.ACTIVE
    user.is_active = True
    db.commit()
    db.refresh(user)
    audit(db, admin.id, "USER_ACTIVATED", "user", user.id, get_client_ip(request))
    return ResponseModel(data=UserOut.model_validate(user), message="User activated")


@router.post("/{user_id}/deactivate", response_model=ResponseModel[UserOut])
def deactivate_user(user_id: int, request: Request, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise NotFoundException("User not found")
    if user.id == admin.id:
        raise ForbiddenException("Cannot deactivate yourself")
    user.status = UserStatus.INACTIVE
    user.is_active = False
    db.commit()
    db.refresh(user)
    audit(db, admin.id, "USER_DEACTIVATED", "user", user.id, get_client_ip(request))
    return ResponseModel(data=UserOut.model_validate(user), message="User deactivated")


@router.post("/{user_id}/change-role", response_model=ResponseModel[UserOut])
def change_role(
    user_id: int,
    role: UserRole,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise NotFoundException("User not found")
    user.role = role
    db.commit()
    db.refresh(user)
    audit(db, admin.id, "USER_ROLE_CHANGED", "user", user.id, get_client_ip(request), {"new_role": role.value})
    return ResponseModel(data=UserOut.model_validate(user), message="Role updated")
