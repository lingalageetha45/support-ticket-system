from typing import Generator, Optional
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.user import User
from app.models.enums import UserRole, UserStatus
from app.repositories.user import UserRepository

security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise UnauthorizedException("Authentication required")
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedException("Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(int(user_id))
    if not user:
        raise UnauthorizedException("User not found")
    if not user.is_active or user.status != UserStatus.ACTIVE:
        raise UnauthorizedException("User account is inactive")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def require_roles(*roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(f"Requires one of roles: {[r.value for r in roles]}")
        return current_user
    return role_checker


def get_admin_user(current_user: User = Depends(require_roles(UserRole.ADMIN))) -> User:
    return current_user


def get_agent_or_admin(current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))) -> User:
    return current_user


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
