"""Review Model"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from api.v1.models.base_model import BaseTableModel


class Review(BaseTableModel):
    __tablename__ = "reviews"

    customer_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    product_name = Column(String, nullable=True)  # Denormalized for easy display
    rating = Column(Integer, nullable=False, default=5)
    comment = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")
    # 'pending', 'approved', 'rejected'
