"""Category Routes"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.schemas.category import CategoryCreate, CategoryUpdate
from api.v1.services.category import category_service

categories = APIRouter(prefix="/categories", tags=["Categories"])


@categories.get("", status_code=status.HTTP_200_OK)
def get_all_categories(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    items = category_service.get_all(db, search=search)
    result = []
    for c in items:
        result.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "product_count": category_service.get_product_count(db, c.id),
            "created_at": str(c.created_at) if c.created_at else None,
        })
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Categories retrieved successfully",
        data=result,
    )


@categories.get("/{category_id}", status_code=status.HTTP_200_OK)
def get_category(category_id: str, db: Session = Depends(get_db)):
    c = category_service.get_by_id(db, category_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Category retrieved successfully",
        data={
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "product_count": category_service.get_product_count(db, c.id),
            "created_at": str(c.created_at) if c.created_at else None,
        },
    )


@categories.post("", status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    c = category_service.create(db, name=data.name, description=data.description)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Category created successfully",
        data={
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "product_count": 0,
            "created_at": str(c.created_at) if c.created_at else None,
        },
    )


@categories.put("/{category_id}", status_code=status.HTTP_200_OK)
def update_category(category_id: str, data: CategoryUpdate, db: Session = Depends(get_db)):
    update_data = data.model_dump(exclude_unset=True)
    c = category_service.update(db, category_id, **update_data)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Category updated successfully",
        data={
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "product_count": category_service.get_product_count(db, c.id),
            "created_at": str(c.created_at) if c.created_at else None,
        },
    )


@categories.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(category_id: str, db: Session = Depends(get_db)):
    category_service.delete(db, category_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Category deleted successfully",
    )
