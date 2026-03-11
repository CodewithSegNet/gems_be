"""Review Service"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.v1.models.review import Review


class ReviewService:

    def get_all(self, db: Session, status_filter: Optional[str] = None,
                search: Optional[str] = None, product_id: Optional[str] = None) -> List[Review]:
        query = db.query(Review)
        if product_id:
            query = query.filter(Review.product_id == product_id)
        if status_filter and status_filter != "all":
            query = query.filter(Review.status == status_filter)
        if search:
            query = query.filter(
                (Review.customer_name.ilike(f"%{search}%")) |
                (Review.product_name.ilike(f"%{search}%"))
            )
        return query.order_by(Review.created_at.desc()).all()

    def get_by_id(self, db: Session, review_id: str) -> Review:
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        return review

    def create(self, db: Session, **kwargs) -> Review:
        review = Review(**kwargs)
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    def update_status(self, db: Session, review_id: str, new_status: str) -> Review:
        review = self.get_by_id(db, review_id)
        review.status = new_status
        db.commit()
        db.refresh(review)
        return review

    def delete(self, db: Session, review_id: str):
        review = self.get_by_id(db, review_id)
        db.delete(review)
        db.commit()
        return True


review_service = ReviewService()
