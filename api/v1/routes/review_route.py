"""Review Routes"""

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.schemas.review import ReviewCreate, ReviewUpdate
from api.v1.services.review import review_service
from api.v1.models.product import Product
from api.v1.models.user import User

reviews = APIRouter(prefix="/reviews", tags=["Reviews"])


def _review_dict(r, db):
    """Build review dict including product image."""
    product_image = None
    if r.product_id:
        product = db.query(Product).filter(Product.id == r.product_id).first()
        if product and product.images:
            product_image = product.images[0].image_url
    return {
        "id": r.id,
        "customer_name": r.customer_name,
        "email": r.email,
        "product_id": r.product_id,
        "product_name": r.product_name,
        "product_image": product_image,
        "rating": r.rating,
        "comment": r.comment,
        "status": r.status,
        "created_at": str(r.created_at) if r.created_at else None,
    }


@reviews.get("", status_code=status.HTTP_200_OK)
def get_all_reviews(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    items = review_service.get_all(db, status_filter=status_filter, search=search, product_id=product_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Reviews retrieved successfully",
        data=[_review_dict(r, db) for r in items],
    )


@reviews.get("/my-review/{product_id}", status_code=status.HTTP_200_OK)
def get_my_review(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's review for a specific product."""
    from api.v1.models.review import Review
    review = db.query(Review).filter(
        Review.product_id == product_id,
        Review.email == current_user.email,
    ).first()
    if review:
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Your review found",
            data=_review_dict(review, db),
        )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="No review found",
        data=None,
    )


@reviews.post("", status_code=status.HTTP_201_CREATED)
def create_review(data: ReviewCreate, db: Session = Depends(get_db)):
    # Check if user already reviewed this product
    from api.v1.models.review import Review
    existing = db.query(Review).filter(
        Review.product_id == data.product_id,
        Review.email == data.email,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product. Use edit instead.",
        )
    r = review_service.create(db, **data.model_dump())
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Review created successfully",
        data=_review_dict(r, db),
    )


@reviews.put("/{review_id}", status_code=status.HTTP_200_OK)
def update_review(
    review_id: str,
    data: ReviewUpdate,
    db: Session = Depends(get_db),
):
    """Update a review's rating and comment."""
    review = review_service.get_by_id(db, review_id)
    if data.rating is not None:
        review.rating = data.rating
    if data.comment is not None:
        review.comment = data.comment
    review.status = "pending"  # Re-submit for approval
    db.commit()
    db.refresh(review)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Review updated successfully",
        data=_review_dict(review, db),
    )


@reviews.patch("/{review_id}/status", status_code=status.HTTP_200_OK)
def update_review_status(review_id: str, new_status: str = Query(...), db: Session = Depends(get_db)):
    r = review_service.update_status(db, review_id, new_status)
    return success_response(status_code=status.HTTP_200_OK, message="Review status updated",
        data={"id": r.id, "status": r.status})


@reviews.delete("/{review_id}", status_code=status.HTTP_200_OK)
def delete_review(review_id: str, db: Session = Depends(get_db)):
    review_service.delete(db, review_id)
    return success_response(status_code=status.HTTP_200_OK, message="Review deleted successfully")
