"""Product and ProductImage Models"""

from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Product(BaseTableModel):
    __tablename__ = "products"

    name = Column(String, nullable=False, index=True)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    stock = Column(Integer, nullable=False, default=0)
    gender = Column(String, nullable=False, default="female")  # 'male', 'female', or 'unisex'
    status = Column(String, nullable=False, default="active")  # 'active' or 'inactive'
    is_best_seller = Column(Boolean, default=False)
    is_new_collection = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    video_position = Column(Integer, nullable=True, default=None)  # Position of video among media (0=first)

    # Relationships
    category = relationship("Category", backref="products", lazy="joined")
    images = relationship("ProductImage", backref="product", cascade="all, delete-orphan", lazy="joined")


class ProductImage(BaseTableModel):
    __tablename__ = "product_images"

    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)
