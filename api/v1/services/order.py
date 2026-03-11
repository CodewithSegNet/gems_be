"""Order Service"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.v1.models.order import Order


class OrderService:

    def get_all(self, db: Session, status_filter: Optional[str] = None,
                payment_method: Optional[str] = None, search: Optional[str] = None) -> List[Order]:
        query = db.query(Order)
        if status_filter and status_filter != "all":
            query = query.filter(Order.status == status_filter)
        if payment_method and payment_method != "all":
            query = query.filter(Order.payment_method == payment_method)
        if search:
            query = query.filter(
                (Order.customer_name.ilike(f"%{search}%")) |
                (Order.email.ilike(f"%{search}%")) |
                (Order.id.ilike(f"%{search}%"))
            )
        return query.order_by(Order.created_at.desc()).all()

    def get_by_id(self, db: Session, order_id: str) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order

    def create(self, db: Session, **kwargs) -> Order:
        order = Order(**kwargs)
        db.add(order)
        db.commit()
        db.refresh(order)

        # Send order confirmation email
        try:
            from api.v1.services.email import send_order_confirmation
            email = getattr(order, 'email', None) or kwargs.get('email')
            name = getattr(order, 'customer_name', None) or kwargs.get('customer_name')
            if email:
                send_order_confirmation(email, order.id, order.total or 0, name)
        except Exception:
            pass

        return order

    def update(self, db: Session, order_id: str, **kwargs) -> Order:
        order = self.get_by_id(db, order_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(order, key):
                setattr(order, key, value)
        db.commit()
        db.refresh(order)
        return order

    def update_status(self, db: Session, order_id: str, new_status: str, reason: Optional[str] = None) -> Order:
        order = self.get_by_id(db, order_id)
        order.status = new_status
        if reason:
            order.cancellation_reason = reason
        db.commit()
        db.refresh(order)
        return order

    def approve_payment(self, db: Session, order_id: str) -> Order:
        order = self.get_by_id(db, order_id)
        order.payment_approved = True
        order.status = "processing"
        db.commit()
        db.refresh(order)
        return order

    def get_by_email(self, db: Session, email: str) -> List[Order]:
        """Get all orders for a customer email."""
        return db.query(Order).filter(Order.email == email).order_by(Order.created_at.desc()).all()

    def update_delivery_status(self, db: Session, order_id: str, delivery_status: str) -> Order:
        order = self.get_by_id(db, order_id)
        order.delivery_status = delivery_status
        db.commit()
        db.refresh(order)
        return order

    def delete(self, db: Session, order_id: str):
        order = self.get_by_id(db, order_id)
        db.delete(order)
        db.commit()
        return True


order_service = OrderService()
