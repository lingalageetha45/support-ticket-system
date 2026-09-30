from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    meta: PaginationMeta
