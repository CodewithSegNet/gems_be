"""Discount Routes"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.schemas.discount import DiscountCreate, DiscountUpdate
from api.v1.services.discount import discount_service

discounts = APIRouter(prefix="/discounts", tags=["Discounts"])


@discounts.get("", status_code=status.HTTP_200_OK)
def get_all_discounts(
    status_filter: Optional[str] = Query(None, alias="status"),
    discount_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    items = discount_service.get_all(db, status_filter=status_filter, discount_type=discount_type, search=search)
    result = [
        {
            "id": d.id, "name": d.name, "discount_type": d.discount_type,
            "code": d.code, "type": d.type, "value": d.value,
            "min_purchase": d.min_purchase, "order_min_amount": d.order_min_amount,
            "product_id": d.product_id, "max_uses": d.max_uses, "used_count": d.used_count,
            "expires_at": str(d.expires_at) if d.expires_at else None,
            "status": d.status, "auto_apply": d.auto_apply,
            "created_at": str(d.created_at) if d.created_at else None,
        }
        for d in items
    ]
    return success_response(status_code=status.HTTP_200_OK, message="Discounts retrieved successfully", data=result)


@discounts.post("", status_code=status.HTTP_201_CREATED)
def create_discount(data: DiscountCreate, db: Session = Depends(get_db)):
    d = discount_service.create(db, **data.model_dump())
    return success_response(status_code=status.HTTP_201_CREATED, message="Discount created successfully",
        data={"id": d.id, "name": d.name, "code": d.code, "status": d.status})


@discounts.put("/{discount_id}", status_code=status.HTTP_200_OK)
def update_discount(discount_id: str, data: DiscountUpdate, db: Session = Depends(get_db)):
    update_data = data.model_dump(exclude_unset=True)
    d = discount_service.update(db, discount_id, **update_data)
    return success_response(status_code=status.HTTP_200_OK, message="Discount updated successfully",
        data={"id": d.id, "name": d.name, "status": d.status})


@discounts.delete("/{discount_id}", status_code=status.HTTP_200_OK)
def delete_discount(discount_id: str, db: Session = Depends(get_db)):
    discount_service.delete(db, discount_id)
    return success_response(status_code=status.HTTP_200_OK, message="Discount deleted successfully")


from pydantic import BaseModel as PydanticBase
from datetime import datetime, timezone
from typing import List


class CouponValidate(PydanticBase):
    code: str
    subtotal: float = 0.0


@discounts.post("/validate", status_code=status.HTTP_200_OK)
def validate_coupon(data: CouponValidate, db: Session = Depends(get_db)):
    """Validate a coupon code for the storefront cart (general promo codes only)."""
    from api.v1.models.discount import Discount

    d = db.query(Discount).filter(Discount.code == data.code).first()
    if not d:
        return success_response(status_code=status.HTTP_200_OK, message="Invalid coupon code", data={"valid": False})

    if d.status != "active":
        return success_response(status_code=status.HTTP_200_OK, message="Coupon is not active", data={"valid": False})

    if d.expires_at and d.expires_at < datetime.now(timezone.utc):
        return success_response(status_code=status.HTTP_200_OK, message="Coupon has expired", data={"valid": False})

    if d.max_uses and d.used_count >= d.max_uses:
        return success_response(status_code=status.HTTP_200_OK, message="Coupon max uses reached", data={"valid": False})

    min_amt = d.min_purchase or d.order_min_amount or 0
    if data.subtotal < min_amt:
        return success_response(
            status_code=status.HTTP_200_OK,
            message=f"Minimum purchase of {min_amt:,.0f} required",
            data={"valid": False},
        )

    # Calculate discount
    if d.type == "percentage":
        discount_value = data.subtotal * (d.value / 100)
    else:
        discount_value = d.value

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Coupon applied successfully",
        data={
            "valid": True,
            "name": d.name,
            "code": d.code,
            "type": d.type,
            "value": d.value,
            "discount_type": d.discount_type,
            "discount_amount": round(discount_value, 2),
        },
    )


# --- Auto-applied discounts ---

class AutoDiscountRequest(PydanticBase):
    subtotal: float = 0.0
    email: Optional[str] = None
    product_ids: List[str] = []
    product_prices: List[float] = []  # parallel to product_ids


def _calc_discount(d, subtotal: float, product_price: float = 0) -> float:
    """Calculate discount amount for a given discount rule."""
    base = product_price if d.discount_type == "product" else subtotal
    if d.type == "percentage":
        return base * (d.value / 100)
    return min(d.value, base)  # fixed can't exceed the base


@discounts.post("/apply-auto", status_code=status.HTTP_200_OK)
def apply_auto_discounts(data: AutoDiscountRequest, db: Session = Depends(get_db)):
    """Find the best auto-applied discount for the current cart."""
    from api.v1.models.discount import Discount
    from api.v1.models.order import Order

    now = datetime.now(timezone.utc)

    # Fetch all active auto-applicable discounts (not general promo codes)
    candidates = (
        db.query(Discount)
        .filter(
            Discount.status == "active",
            Discount.discount_type.in_(["new_customer", "order_amount", "product"]),
        )
        .all()
    )

    best = None
    best_amount = 0

    for d in candidates:
        # Check expiry
        if d.expires_at and d.expires_at < now:
            continue
        # Check max uses
        if d.max_uses and d.used_count >= d.max_uses:
            continue

        if d.discount_type == "new_customer":
            # Only if we know the email and user has ZERO previous orders
            if not data.email:
                continue
            order_count = db.query(Order).filter(Order.email == data.email.lower().strip()).count()
            if order_count > 0:
                continue
            # Check min purchase
            min_amt = d.min_purchase or 0
            if data.subtotal < min_amt:
                continue
            amount = _calc_discount(d, data.subtotal)

        elif d.discount_type == "order_amount":
            min_amt = d.order_min_amount or 0
            if data.subtotal < min_amt:
                continue
            amount = _calc_discount(d, data.subtotal)

        elif d.discount_type == "product":
            if not d.product_id or d.product_id not in data.product_ids:
                continue
            # Find the price of the matching product
            idx = data.product_ids.index(d.product_id)
            pprice = data.product_prices[idx] if idx < len(data.product_prices) else 0
            amount = _calc_discount(d, data.subtotal, pprice)

        else:
            continue

        amount = round(amount, 2)
        if amount > best_amount:
            best_amount = amount
            best = d

    if not best:
        return success_response(
            status_code=status.HTTP_200_OK,
            message="No auto-discounts applicable",
            data={"applied": False},
        )

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Auto-discount applied",
        data={
            "applied": True,
            "id": best.id,
            "name": best.name,
            "discount_type": best.discount_type,
            "type": best.type,
            "value": best.value,
            "discount_amount": best_amount,
            "product_id": best.product_id,
        },
    )


# --- Increment used_count after order is placed ---

class DiscountUseRequest(PydanticBase):
    discount_id: Optional[str] = None
    code: Optional[str] = None


@discounts.post("/use", status_code=status.HTTP_200_OK)
def use_discount(data: DiscountUseRequest, db: Session = Depends(get_db)):
    """Increment used_count for a discount after an order is placed."""
    from api.v1.models.discount import Discount

    d = None
    if data.discount_id:
        d = db.query(Discount).filter(Discount.id == data.discount_id).first()
    elif data.code:
        d = db.query(Discount).filter(Discount.code == data.code).first()

    if d:
        d.used_count = (d.used_count or 0) + 1
        db.commit()
        return success_response(status_code=status.HTTP_200_OK, message="Discount usage recorded")

    return success_response(status_code=status.HTTP_200_OK, message="Discount not found (skipped)")
