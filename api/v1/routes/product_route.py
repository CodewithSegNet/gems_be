"""Product Routes"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from api.v1.services.product import product_service

products = APIRouter(prefix="/products", tags=["Products"])


@products.get("", status_code=status.HTTP_200_OK)
def get_all_products(
    gender: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    is_best_seller: Optional[bool] = Query(None),
    is_new_collection: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    items = product_service.get_all(
        db, gender=gender, category_id=category_id,
        status_filter=status_filter, search=search,
        is_best_seller=is_best_seller, is_new_collection=is_new_collection,
    )
    
    result = []
    for p in items:
        images_list = [{"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order} for img in (p.images or [])]
        result.append({
            "id": p.id,
            "name": p.name,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "price": p.price,
            "stock": p.stock,
            "gender": p.gender,
            "status": p.status,
            "is_best_seller": p.is_best_seller,
            "is_new_collection": p.is_new_collection,
            "description": p.description,
            "images": images_list,
            "image": images_list[0]["image_url"] if images_list else None,
            "created_at": str(p.created_at) if p.created_at else None,
            "updated_at": str(p.updated_at) if p.updated_at else None,
        })
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Products retrieved successfully",
        data=result,
    )


@products.get("/{product_id}", status_code=status.HTTP_200_OK)
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = product_service.get_by_id(db, product_id)
    images_list = [{"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order} for img in (p.images or [])]
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Product retrieved successfully",
        data={
            "id": p.id,
            "name": p.name,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "price": p.price,
            "stock": p.stock,
            "gender": p.gender,
            "status": p.status,
            "is_best_seller": p.is_best_seller,
            "is_new_collection": p.is_new_collection,
            "description": p.description,
            "images": images_list,
            "image": images_list[0]["image_url"] if images_list else None,
            "created_at": str(p.created_at) if p.created_at else None,
            "updated_at": str(p.updated_at) if p.updated_at else None,
        },
    )


@products.post("", status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    p = product_service.create(
        db,
        name=data.name,
        price=data.price,
        stock=data.stock,
        gender=data.gender,
        status_val=data.status,
        category_id=data.category_id,
        is_best_seller=data.is_best_seller,
        is_new_collection=data.is_new_collection,
        description=data.description,
        image_urls=data.image_urls,
    )
    images_list = [{"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order} for img in (p.images or [])]
    
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Product created successfully",
        data={
            "id": p.id,
            "name": p.name,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "price": p.price,
            "stock": p.stock,
            "gender": p.gender,
            "status": p.status,
            "is_best_seller": p.is_best_seller,
            "is_new_collection": p.is_new_collection,
            "description": p.description,
            "images": images_list,
            "image": images_list[0]["image_url"] if images_list else None,
            "created_at": str(p.created_at) if p.created_at else None,
        },
    )


@products.put("/{product_id}", status_code=status.HTTP_200_OK)
def update_product(product_id: str, data: ProductUpdate, db: Session = Depends(get_db)):
    update_data = data.model_dump(exclude_unset=True)
    # Rename 'status' to 'status' (already matching column name)
    p = product_service.update(db, product_id, **update_data)
    images_list = [{"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order} for img in (p.images or [])]
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Product updated successfully",
        data={
            "id": p.id,
            "name": p.name,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "price": p.price,
            "stock": p.stock,
            "gender": p.gender,
            "status": p.status,
            "is_best_seller": p.is_best_seller,
            "is_new_collection": p.is_new_collection,
            "images": images_list,
            "image": images_list[0]["image_url"] if images_list else None,
        },
    )


@products.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product_service.delete(db, product_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Product deleted successfully",
    )
