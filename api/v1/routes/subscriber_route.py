"""Subscriber Routes"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.subscriber import Subscriber
from api.v1.services.email import send_subscription_confirmation

subscribers = APIRouter(prefix="/subscribers", tags=["Subscribers"])


class SubscribeRequest(BaseModel):
    email: EmailStr


@subscribers.post("", status_code=status.HTTP_201_CREATED)
def subscribe(data: SubscribeRequest, db: Session = Depends(get_db)):
    """Subscribe to the newsletter."""
    existing = db.query(Subscriber).filter(Subscriber.email == data.email.lower().strip()).first()
    if existing:
        if existing.is_active:
            return success_response(
                status_code=status.HTTP_200_OK,
                message="You're already subscribed!",
                data={"email": existing.email}
            )
        # Reactivate
        existing.is_active = True
        db.commit()
        send_subscription_confirmation(existing.email)
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Welcome back! You've been resubscribed.",
            data={"email": existing.email}
        )

    subscriber = Subscriber(email=data.email.lower().strip(), is_active=True)
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)

    send_subscription_confirmation(subscriber.email)

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Successfully subscribed to our newsletter!",
        data={"email": subscriber.email}
    )


@subscribers.get("", status_code=status.HTTP_200_OK)
def list_subscribers(db: Session = Depends(get_db)):
    """List all subscribers (admin)."""
    items = db.query(Subscriber).filter(Subscriber.is_active == True).order_by(Subscriber.created_at.desc()).all()
    result = [
        {"id": s.id, "email": s.email, "created_at": str(s.created_at) if s.created_at else None}
        for s in items
    ]
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Subscribers retrieved successfully",
        data=result
    )
