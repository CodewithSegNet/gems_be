"""Shipping Location Routes"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.schemas.shipping import ShippingLocationCreate, ShippingLocationUpdate
from api.v1.services.shipping import shipping_service

shipping = APIRouter(prefix="/shipping", tags=["Shipping"])


def _shipping_dict(s):
    return {
        "id": s.id,
        "country": s.country,
        "state": s.state,
        "shipping_price": s.shipping_price,
        "is_free_shipping": s.is_free_shipping,
        "delivery_days": s.delivery_days,
        "created_at": str(s.created_at) if s.created_at else None,
        "updated_at": str(s.updated_at) if s.updated_at else None,
    }


@shipping.get("", status_code=status.HTTP_200_OK)
def get_all_shipping(db: Session = Depends(get_db)):
    items = shipping_service.get_all(db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Shipping locations retrieved",
        data=[_shipping_dict(s) for s in items],
    )


@shipping.get("/calculate", status_code=status.HTTP_200_OK)
def calculate_shipping(
    country: str = Query("Nigeria"),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Public endpoint: fetch shipping cost for a location."""
    location = shipping_service.get_by_location(db, country, state)
    if not location:
        return success_response(
            status_code=status.HTTP_200_OK,
            message="No shipping rule found for this location",
            data={"shipping_price": 0, "is_free_shipping": False, "found": False},
        )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Shipping cost retrieved",
        data={
            "shipping_price": 0 if location.is_free_shipping else location.shipping_price,
            "is_free_shipping": location.is_free_shipping,
            "delivery_days": location.delivery_days,
            "found": True,
        },
    )


@shipping.post("", status_code=status.HTTP_201_CREATED)
def create_shipping(data: ShippingLocationCreate, db: Session = Depends(get_db)):
    item = shipping_service.create(db, **data.model_dump())
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Shipping location created",
        data=_shipping_dict(item),
    )


@shipping.put("/{shipping_id}", status_code=status.HTTP_200_OK)
def update_shipping(
    shipping_id: str, data: ShippingLocationUpdate, db: Session = Depends(get_db)
):
    update_data = data.model_dump(exclude_unset=True)
    item = shipping_service.update(db, shipping_id, **update_data)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Shipping location updated",
        data=_shipping_dict(item),
    )


@shipping.delete("/{shipping_id}", status_code=status.HTTP_200_OK)
def delete_shipping(shipping_id: str, db: Session = Depends(get_db)):
    shipping_service.delete(db, shipping_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Shipping location deleted",
    )
