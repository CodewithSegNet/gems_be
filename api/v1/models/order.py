"""Order Model"""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text
from api.v1.models.base_model import BaseTableModel


class Order(BaseTableModel):
    __tablename__ = "orders"

    customer_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    total = Column(Float, nullable=False, default=0.0)
    crypto_amount = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="pending")
    # 'awaiting_payment', 'pending', 'processing', 'completed', 'cancelled'
    delivery_status = Column(String, nullable=False, default="not_shipped")
    # 'not_shipped', 'shipped', 'in_transit', 'delivered'
    payment_method = Column(String, nullable=False, default="Paystack")
    # 'BTC', 'USDT', 'Paystack'
    payment_proof = Column(String, nullable=True)
    payment_approved = Column(Boolean, default=False)
    cancellation_reason = Column(Text, nullable=True)
    items_count = Column(Integer, nullable=False, default=0)
    items_json = Column(Text, nullable=True)
    # JSON string: [{"id":"..","name":"..","image":"..","price":..,"quantity":..}]
    discount_code = Column(String, nullable=True)
    discount_amount = Column(Float, nullable=False, default=0.0)
    shipping_country = Column(String, nullable=True)
    shipping_state = Column(String, nullable=True)
    shipping_cost = Column(Float, nullable=False, default=0.0)
    estimated_delivery = Column(String, nullable=True)  # e.g. "3-5 days"
