"""Discount Model"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from api.v1.models.base_model import BaseTableModel


class Discount(BaseTableModel):
    __tablename__ = "discounts"

    name = Column(String, nullable=False)
    discount_type = Column(String, nullable=False, default="general")
    # 'new_customer', 'order_amount', 'general', 'product'
    code = Column(String, nullable=True, unique=True, index=True)
    type = Column(String, nullable=False, default="percentage")
    # 'percentage' or 'fixed'
    value = Column(Float, nullable=False, default=0.0)
    min_purchase = Column(Float, nullable=True)
    order_min_amount = Column(Float, nullable=True)
    product_id = Column(String, nullable=True)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default="active")
    auto_apply = Column(Boolean, default=False)
