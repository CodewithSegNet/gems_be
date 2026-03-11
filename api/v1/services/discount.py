"""Discount Service"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.v1.models.discount import Discount


class DiscountService:

    def get_all(self, db: Session, status_filter: Optional[str] = None,
                discount_type: Optional[str] = None, search: Optional[str] = None) -> List[Discount]:
        query = db.query(Discount)
        if status_filter and status_filter != "all":
            query = query.filter(Discount.status == status_filter)
        if discount_type and discount_type != "all":
            query = query.filter(Discount.discount_type == discount_type)
        if search:
            query = query.filter(
                (Discount.name.ilike(f"%{search}%")) |
                (Discount.code.ilike(f"%{search}%"))
            )
        return query.order_by(Discount.created_at.desc()).all()

    def get_by_id(self, db: Session, discount_id: str) -> Discount:
        discount = db.query(Discount).filter(Discount.id == discount_id).first()
        if not discount:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")
        return discount

    def create(self, db: Session, **kwargs) -> Discount:
        # Check for duplicate code
        code = kwargs.get("code")
        if code:
            existing = db.query(Discount).filter(Discount.code == code).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Discount code already exists")
        
        discount = Discount(**kwargs)
        db.add(discount)
        db.commit()
        db.refresh(discount)
        return discount

    def update(self, db: Session, discount_id: str, **kwargs) -> Discount:
        discount = self.get_by_id(db, discount_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(discount, key):
                setattr(discount, key, value)
        db.commit()
        db.refresh(discount)
        return discount

    def delete(self, db: Session, discount_id: str):
        discount = self.get_by_id(db, discount_id)
        db.delete(discount)
        db.commit()
        return True


discount_service = DiscountService()
