from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from app.core.exceptions import (
    UnauthorizedException,
    ConflictException,
    ValidationException,
)
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.enums import UserRole, UserStatus
from app.models.audit import AuditLog
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserOut,
    Token,
    TokenRefresh,
    UserChangePassword,
)
from app.schemas.common import ResponseModel
from app.repositories.user import UserRepository


router = APIRouter()


def create_audit(
    db: Session,
    user_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None,
    ip: str,
    metadata: dict | None = None,
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        ip_address=ip,
        metadata_=metadata,
    )
    db.add(log)
    db.commit()


@router.post(
    "/register",
    response_model=ResponseModel[UserOut],
    status_code=201,
)
def register(
    data: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)

    if repo.get_by_email(data.email):
        raise ConflictException(
            "Email already registered",
            code="DUPLICATE_EMAIL",
        )

    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=UserRole.CUSTOMER,
        status=UserStatus.ACTIVE,
        is_active=True,
    )

    user = repo.create(user)

    create_audit(
        db,
        user.id,
        "USER_REGISTERED",
        "user",
        user.id,
        get_client_ip(request),
    )

    return ResponseModel(
        data=UserOut.model_validate(user),
        message="Registration successful",
    )


@router.post(
    "/login",
    response_model=ResponseModel[Token],
)
def login(
    data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    user = repo.get_by_email(data.email)
    ip = get_client_ip(request)

    if not user or not verify_password(
        data.password,
        user.hashed_password,
    ):
        create_audit(
            db,
            None,
            "LOGIN_FAILED",
            "user",
            None,
            ip,
            {"email": data.email},
        )

        raise UnauthorizedException(
            "Invalid email or password",
            code="INVALID_CREDENTIALS",
        )

    if not user.is_active or user.status != UserStatus.ACTIVE:
        create_audit(
            db,
            user.id,
            "LOGIN_FAILED_INACTIVE",
            "user",
            user.id,
            ip,
        )

        raise UnauthorizedException(
            "Account is inactive",
            code="INACTIVE_USER",
        )

    access = create_access_token(
        user.id,
        extra_claims={"role": user.role.value},
    )

    refresh = create_refresh_token(user.id)

    expires = (
        datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh,
        expires_at=expires,
    )

    db.add(refresh_token)
    db.commit()

    create_audit(
        db,
        user.id,
        "LOGIN_SUCCESS",
        "user",
        user.id,
        ip,
    )

    return ResponseModel(
        data=Token(
            access_token=access,
            refresh_token=refresh,
        ),
        message="Login successful",
    )


@router.post(
    "/refresh",
    response_model=ResponseModel[Token],
)
def refresh_token(
    data: TokenRefresh,
    db: Session = Depends(get_db),
):
    payload = decode_token(data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid refresh token")

    user_id = int(payload["sub"])

    refresh_token_record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == data.refresh_token,
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,
        )
        .first()
    )

    if (
        not refresh_token_record
        or refresh_token_record.expires_at
        < datetime.now(timezone.utc)
    ):
        raise UnauthorizedException(
            "Refresh token expired or revoked"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if (
        not user
        or not user.is_active
        or user.status != UserStatus.ACTIVE
    ):
        raise UnauthorizedException("User inactive")

    access = create_access_token(
        user.id,
        extra_claims={"role": user.role.value},
    )

    new_refresh = create_refresh_token(user.id)

    refresh_token_record.is_revoked = True

    new_refresh_token = RefreshToken(
        user_id=user.id,
        token=new_refresh,
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        ),
    )

    db.add(new_refresh_token)
    db.commit()

    return ResponseModel(
        data=Token(
            access_token=access,
            refresh_token=new_refresh,
        )
    )


@router.post(
    "/logout",
    response_model=ResponseModel,
)
def logout(
    data: TokenRefresh,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    refresh_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == data.refresh_token,
            RefreshToken.user_id == current_user.id,
        )
        .first()
    )

    if refresh_token:
        refresh_token.is_revoked = True
        db.commit()

    return ResponseModel(
        message="Logged out successfully"
    )


@router.get(
    "/me",
    response_model=ResponseModel[UserOut],
)
def me(
    current_user: User = Depends(get_current_user),
):
    return ResponseModel(
        data=UserOut.model_validate(current_user)
    )


@router.post(
    "/change-password",
    response_model=ResponseModel,
)
def change_password(
    data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(
        data.current_password,
        current_user.hashed_password,
    ):
        raise ValidationException(
            "Current password is incorrect"
        )

    current_user.hashed_password = get_password_hash(
        data.new_password
    )

    # Revoke all existing refresh tokens after a password change.
    # This prevents previously issued refresh tokens from being
    # used to create new access tokens.
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False,
    ).update(
        {
            RefreshToken.is_revoked: True
        },
        synchronize_session=False,
    )

    db.commit()

    return ResponseModel(
        message="Password changed successfully"
    )