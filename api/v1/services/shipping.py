"""Shipping Location Service"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.shipping import ShippingLocation


class ShippingService:
    """Service class for shipping location CRUD."""

    def get_all(self, db: Session):
        return db.query(ShippingLocation).order_by(
            ShippingLocation.country, ShippingLocation.state
        ).all()

    def get_by_id(self, db: Session, shipping_id: str):
        item = db.query(ShippingLocation).filter(ShippingLocation.id == shipping_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping location not found",
            )
        return item

    def get_by_location(self, db: Session, country: str, state: str = None):
        """Look up shipping cost for a specific location."""
        query = db.query(ShippingLocation).filter(
            ShippingLocation.country.ilike(country)
        )
        if state:
            query = query.filter(ShippingLocation.state.ilike(state))
        else:
            query = query.filter(ShippingLocation.state.is_(None))
        return query.first()

    def create(self, db: Session, **kwargs):
        item = ShippingLocation(**kwargs)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def update(self, db: Session, shipping_id: str, **kwargs):
        item = self.get_by_id(db, shipping_id)
        for key, value in kwargs.items():
            if value is not None:
                setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item

    def delete(self, db: Session, shipping_id: str):
        item = self.get_by_id(db, shipping_id)
        db.delete(item)
        db.commit()


shipping_service = ShippingService()
