from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ConflictException
from app.api.deps import get_admin_user, get_current_user
from app.models.user import User
from app.models.category import TicketCategory
from app.schemas.ticket import CategoryCreate, CategoryUpdate, CategoryOut
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("", response_model=ResponseModel[CategoryOut], status_code=201)
def create_category(data: CategoryCreate, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    exists = db.query(TicketCategory).filter(TicketCategory.name == data.name).first()
    if exists:
        raise ConflictException("Category name already exists")
    cat = TicketCategory(name=data.name, description=data.description, is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return ResponseModel(data=CategoryOut.model_validate(cat), message="Category created")


@router.get("", response_model=ResponseModel[list[CategoryOut]])
def list_categories(active_only: bool = True, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(TicketCategory)
    if active_only:
        q = q.filter(TicketCategory.is_active == True)
    cats = q.order_by(TicketCategory.name).all()
    return ResponseModel(data=[CategoryOut.model_validate(c) for c in cats])


@router.get("/{category_id}", response_model=ResponseModel[CategoryOut])
def get_category(category_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cat = db.query(TicketCategory).filter(TicketCategory.id == category_id).first()
    if not cat:
        raise NotFoundException("Category not found")
    return ResponseModel(data=CategoryOut.model_validate(cat))


@router.patch("/{category_id}", response_model=ResponseModel[CategoryOut])
def update_category(category_id: int, data: CategoryUpdate, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    cat = db.query(TicketCategory).filter(TicketCategory.id == category_id).first()
    if not cat:
        raise NotFoundException("Category not found")
    if data.name is not None:
        cat.name = data.name
    if data.description is not None:
        cat.description = data.description
    if data.is_active is not None:
        cat.is_active = data.is_active
    db.commit()
    db.refresh(cat)
    return ResponseModel(data=CategoryOut.model_validate(cat), message="Category updated")


@router.post("/{category_id}/activate", response_model=ResponseModel[CategoryOut])
def activate_category(category_id: int, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    cat = db.query(TicketCategory).filter(TicketCategory.id == category_id).first()
    if not cat:
        raise NotFoundException("Category not found")
    cat.is_active = True
    db.commit()
    db.refresh(cat)
    return ResponseModel(data=CategoryOut.model_validate(cat), message="Category activated")


@router.post("/{category_id}/deactivate", response_model=ResponseModel[CategoryOut])
def deactivate_category(category_id: int, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    cat = db.query(TicketCategory).filter(TicketCategory.id == category_id).first()
    if not cat:
        raise NotFoundException("Category not found")
    cat.is_active = False
    db.commit()
    db.refresh(cat)
    return ResponseModel(data=CategoryOut.model_validate(cat), message="Category deactivated")
