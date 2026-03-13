"""Order Routes"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.schemas.order import OrderCreate, OrderUpdate
from api.v1.services.order import order_service
from api.v1.models.user import User
from api.v1.services.email import send_order_confirmation, send_order_status_update, send_admin_payment_notification, send_delivery_status_update

orders = APIRouter(prefix="/orders", tags=["Orders"])


def _order_dict(o):
    """Serialize an order to a dict with all fields."""
    return {
        "id": o.id,
        "customer_name": o.customer_name,
        "email": o.email,
        "phone": getattr(o, "phone", None),
        "address": getattr(o, "address", None),
        "city": getattr(o, "city", None),
        "notes": getattr(o, "notes", None),
        "total": o.total,
        "crypto_amount": o.crypto_amount,
        "status": o.status,
        "delivery_status": getattr(o, "delivery_status", "not_shipped"),
        "payment_method": o.payment_method,
        "payment_proof": o.payment_proof,
        "payment_approved": o.payment_approved,
        "cancellation_reason": o.cancellation_reason,
        "items_count": o.items_count,
        "items_json": getattr(o, "items_json", None),
        "discount_code": getattr(o, "discount_code", None),
        "discount_amount": getattr(o, "discount_amount", 0),
        "shipping_country": getattr(o, "shipping_country", None),
        "shipping_state": getattr(o, "shipping_state", None),
        "shipping_cost": getattr(o, "shipping_cost", 0),
        "estimated_delivery": getattr(o, "estimated_delivery", None),
        "created_at": str(o.created_at) if o.created_at else None,
    }


@orders.get("", status_code=status.HTTP_200_OK)
def get_all_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    payment_method: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    items = order_service.get_all(db, status_filter=status_filter, payment_method=payment_method, search=search)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Orders retrieved successfully",
        data=[_order_dict(o) for o in items],
    )


@orders.get("/my-orders", status_code=status.HTTP_200_OK)
def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get orders for the currently authenticated customer (by email)."""
    items = order_service.get_by_email(db, current_user.email)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Your orders retrieved successfully",
        data=[_order_dict(o) for o in items],
    )


@orders.get("/has-purchased/{product_id}", status_code=status.HTTP_200_OK)
def has_purchased_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if the current user has purchased a specific product."""
    import json as _json
    user_orders = order_service.get_by_email(db, current_user.email)
    for o in user_orders:
        if o.status in ("completed", "processing", "pending", "delivered") and o.items_json:
            try:
                items = _json.loads(o.items_json)
                if any(item.get("id") == product_id for item in items):
                    return success_response(
                        status_code=status.HTTP_200_OK,
                        message="Purchase check",
                        data={"purchased": True, "delivered": o.status == "delivered"},
                    )
            except (ValueError, TypeError):
                pass
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Purchase check",
        data={"purchased": False, "delivered": False},
    )


@orders.get("/{order_id}", status_code=status.HTTP_200_OK)
def get_order(order_id: str, db: Session = Depends(get_db)):
    o = order_service.get_by_id(db, order_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Order retrieved successfully",
        data=_order_dict(o),
    )


@orders.post("", status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    o = order_service.create(db, **data.model_dump())
    # Send order confirmation to customer
    try:
        send_order_confirmation(o.email, o.id, o.total, o.customer_name, getattr(o, 'estimated_delivery', None))
        # Only notify admin immediately for Paystack (instant payment); crypto orders notify on proof upload
        if o.payment_method == "Paystack":
            send_admin_payment_notification(o.id, o.email, o.total, o.payment_method, o.customer_name)
    except Exception:
        pass
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Order created successfully",
        data=_order_dict(o),
    )


@orders.put("/{order_id}", status_code=status.HTTP_200_OK)
def update_order(order_id: str, data: OrderUpdate, db: Session = Depends(get_db)):
    update_data = data.model_dump(exclude_unset=True)
    o = order_service.update(db, order_id, **update_data)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Order updated successfully",
        data=_order_dict(o),
    )


@orders.patch("/{order_id}/status", status_code=status.HTTP_200_OK)
def update_order_status(order_id: str, new_status: str = Query(...), reason: Optional[str] = Query(None), db: Session = Depends(get_db)):
    o = order_service.update_status(db, order_id, new_status, reason)
    # Send status update email to customer
    try:
        send_order_status_update(o.email, o.id, new_status, o.customer_name)
    except Exception:
        pass
    return success_response(status_code=status.HTTP_200_OK, message="Order status updated", data={"id": o.id, "status": o.status})


@orders.patch("/{order_id}/delivery-status", status_code=status.HTTP_200_OK)
def update_delivery_status(order_id: str, delivery_status: str = Query(...), db: Session = Depends(get_db)):
    o = order_service.update_delivery_status(db, order_id, delivery_status)
    # Send delivery status email to customer
    try:
        send_delivery_status_update(o.email, o.id, delivery_status, o.customer_name)
    except Exception:
        pass
    return success_response(status_code=status.HTTP_200_OK, message="Delivery status updated", data={"id": o.id, "delivery_status": o.delivery_status})


@orders.patch("/{order_id}/payment-proof", status_code=status.HTTP_200_OK)
def upload_payment_proof(order_id: str, proof_url: str = Query(...), db: Session = Depends(get_db)):
    o = order_service.update(db, order_id, payment_proof=proof_url)
    # Notify admin of payment proof upload
    try:
        send_admin_payment_notification(o.id, o.email, o.total, o.payment_method, o.customer_name)
    except Exception:
        pass
    return success_response(status_code=status.HTTP_200_OK, message="Payment proof uploaded", data={"id": o.id, "payment_proof": o.payment_proof})


@orders.patch("/{order_id}/approve-payment", status_code=status.HTTP_200_OK)
def approve_payment(order_id: str, db: Session = Depends(get_db)):
    o = order_service.approve_payment(db, order_id)
    return success_response(status_code=status.HTTP_200_OK, message="Payment approved", data={"id": o.id, "payment_approved": o.payment_approved, "status": o.status})


@orders.delete("/{order_id}", status_code=status.HTTP_200_OK)
def delete_order(order_id: str, db: Session = Depends(get_db)):
    order_service.delete(db, order_id)
    return success_response(status_code=status.HTTP_200_OK, message="Order deleted successfully")
