"""Shipping Location Model"""

from sqlalchemy import Column, String, Float, Boolean
from api.v1.models.base_model import BaseTableModel


class ShippingLocation(BaseTableModel):
    __tablename__ = "shipping_locations"

    country = Column(String, nullable=False, default="Nigeria")
    state = Column(String, nullable=True)  # e.g. "Lagos", "Abuja" for Nigerian states
    shipping_price = Column(Float, nullable=False, default=0.0)
    is_free_shipping = Column(Boolean, nullable=False, default=False)
    delivery_days = Column(String, nullable=True)  # e.g. "3-5 days", "7-14 days"
