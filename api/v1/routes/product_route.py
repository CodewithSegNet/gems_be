"""Product Routes"""

import time
import hashlib
import json

from fastapi import APIRouter, Depends, status, Query, Response, Request
from sqlalchemy.orm import Session
from typing import Optional

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from api.v1.services.product import product_service
from api.utils.cloudinary_optimizer import optimize_product

products = APIRouter(prefix="/products", tags=["Products"])

# ── In-memory TTL cache ────────────────────────────────────────────────────
# Safe for Render free tier (single instance). Cleared on every write so data
# is never stale after a product is created / updated / deleted.
_cache: dict = {}
CACHE_TTL = 120  # seconds (2 minutes)


def _cache_key(**kwargs) -> str:
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    return "products:" + hashlib.md5(raw.encode()).hexdigest()


def invalidate_product_cache() -> None:
    """Bust all cached product-list entries. Call on any create/update/delete."""
    for k in list(_cache.keys()):
        if k.startswith("products:"):
            _cache.pop(k, None)
# ──────────────────────────────────────────────────────────────────────────


@products.get("", status_code=status.HTTP_200_OK)
def get_all_products(
    request: Request,
    gender: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    is_best_seller: Optional[bool] = Query(None),
    is_new_collection: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    response: Response = None,
    db: Session = Depends(get_db),
):
    ck = _cache_key(
        gender=gender, category_id=category_id, status=status_filter,
        search=search, is_best_seller=is_best_seller,
        is_new_collection=is_new_collection, page=page, limit=limit,
    )

    # Serve from cache if still fresh
    if ck in _cache:
        ts, cached_payload, etag = _cache[ck]
        if time.time() - ts < CACHE_TTL:
            if request and request.headers.get("if-none-match") in (f'"{etag}"', etag):
                return Response(
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    headers={
                        "ETag": f'"{etag}"',
                        "Cache-Control": "public, max-age=60, stale-while-revalidate=30",
                    },
                )
            return success_response(
                status_code=status.HTTP_200_OK,
                message="Products retrieved successfully",
                data=cached_payload,
                headers={
                    "ETag": f'"{etag}"',
                    "Cache-Control": "public, max-age=60, stale-while-revalidate=30",
                    "Vary": "Accept-Encoding",
                    "X-Cache": "HIT",
                },
            )

    items, total = product_service.get_all(
        db,
        gender=gender,
        category_id=category_id,
        status_filter=status_filter,
        search=search,
        is_best_seller=is_best_seller,
        is_new_collection=is_new_collection,
        page=page,
        limit=limit,
    )

    result = []
    for p in items:
        images_list = [
            {"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order}
            for img in (p.images or [])
        ]
        raw = {
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
            "video_url": p.video_url,
            "video_position": p.video_position,
            "images": images_list,
            "image": images_list[0]["image_url"] if images_list else None,
            "created_at": str(p.created_at) if p.created_at else None,
            "updated_at": str(p.updated_at) if p.updated_at else None,
        }
        result.append(optimize_product(raw))

    payload = {"items": result, "total": total, "page": page, "limit": limit}
    etag = hashlib.md5(json.dumps(payload, default=str).encode()).hexdigest()[:16]

    # Store in cache
    _cache[ck] = (time.time(), payload, etag)

    if request and request.headers.get("if-none-match") in (f'"{etag}"', etag):
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={
                "ETag": f'"{etag}"',
                "Cache-Control": "public, max-age=60, stale-while-revalidate=30",
            },
        )

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Products retrieved successfully",
        data=payload,
        headers={
            "ETag": f'"{etag}"',
            "Cache-Control": "public, max-age=60, stale-while-revalidate=30",
            "Vary": "Accept-Encoding",
            "X-Cache": "MISS",
        },
    )


@products.get("/{product_id}", status_code=status.HTTP_200_OK)
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = product_service.get_by_id(db, product_id)
    images_list = [
        {"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order}
        for img in (p.images or [])
    ]
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Product retrieved successfully",
        data=optimize_product({
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
            "video_url": p.video_url,
            "video_position": p.video_position,
            "images": images_list,
            "image": images_list[0]["image_url"] if images_list else None,
            "created_at": str(p.created_at) if p.created_at else None,
            "updated_at": str(p.updated_at) if p.updated_at else None,
        }),
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
        video_url=data.video_url,
        video_position=data.video_position,
    )
    invalidate_product_cache()  # bust stale cache
    images_list = [
        {"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order}
        for img in (p.images or [])
    ]

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Product created successfully",
        data=optimize_product({
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
            "video_url": p.video_url,
            "video_position": p.video_position,
            "images": images_list,
            "image": images_list[0]["image_url"] if images_list else None,
            "created_at": str(p.created_at) if p.created_at else None,
        }),
    )


@products.put("/{product_id}", status_code=status.HTTP_200_OK)
def update_product(product_id: str, data: ProductUpdate, db: Session = Depends(get_db)):
    update_data = data.model_dump(exclude_unset=True)
    p = product_service.update(db, product_id, **update_data)
    invalidate_product_cache()  # bust stale cache
    images_list = [
        {"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order}
        for img in (p.images or [])
    ]

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
            "description": p.description,
            "video_url": p.video_url,
            "video_position": p.video_position,
            "images": images_list,
            "image": images_list[0]["image_url"] if images_list else None,
        },
    )


@products.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product_service.delete(db, product_id)
    invalidate_product_cache()  # bust stale cache
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Product deleted successfully",
    )
