from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import TicketStatus, TicketPriority
from app.schemas.user import UserOut


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    category_id: int
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    category_id: Optional[int] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None


class TicketAssign(BaseModel):
    agent_id: int


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    note: Optional[str] = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    customer_id: int
    assigned_agent_id: Optional[int]
    category_id: int
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    customer: Optional[UserOut] = None
    assigned_agent: Optional[UserOut] = None
    category: Optional[CategoryOut] = None


class TicketListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: str
    title: str
    status: TicketStatus
    priority: TicketPriority
    customer_id: int
    assigned_agent_id: Optional[int]
    category_id: int
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    is_internal: bool = False


class CommentUpdate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    user_id: int
    message: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime
    user: Optional[UserOut] = None


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    uploaded_by_id: int
    file_name: str
    original_name: str
    file_type: str
    mime_type: str
    file_size: int
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    ticket_id: Optional[int]
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime


class DashboardStats(BaseModel):
    total_tickets: int = 0
    open_tickets: int = 0
    in_progress_tickets: int = 0
    resolved_tickets: int = 0
    closed_tickets: int = 0
    overdue_tickets: int = 0
    critical_tickets: int = 0
    # Admin extras
    total_customers: Optional[int] = None
    total_agents: Optional[int] = None
    active_agents: Optional[int] = None
    # Agent extras
    my_open_tickets: Optional[int] = None
    my_overdue_tickets: Optional[int] = None
    my_resolved_tickets: Optional[int] = None
