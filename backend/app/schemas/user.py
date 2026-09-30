from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import UserRole, UserStatus


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.CUSTOMER


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    status: UserStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: int
