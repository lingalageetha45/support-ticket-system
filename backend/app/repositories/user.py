from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.models.enums import UserRole, UserStatus


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None,
    ) -> tuple[List[User], int]:
        q = self.db.query(User)
        if role:
            q = q.filter(User.role == role)
        if status:
            q = q.filter(User.status == status)
        if search:
            like = f"%{search}%"
            q = q.filter(or_(User.email.ilike(like), User.full_name.ilike(like)))
        total = q.count()
        users = q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        return users, total

    def count_by_role(self, role: UserRole, active_only: bool = False) -> int:
        q = self.db.query(User).filter(User.role == role)
        if active_only:
            q = q.filter(User.is_active == True, User.status == UserStatus.ACTIVE)
        return q.count()
