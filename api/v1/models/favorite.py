"""Favorite Model"""

from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from api.v1.models.base_model import BaseTableModel


class Favorite(BaseTableModel):
    __tablename__ = "favorites"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_favorite"),
    )
