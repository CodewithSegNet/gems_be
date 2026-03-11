"""Category Model"""

from sqlalchemy import Column, String, Text
from api.v1.models.base_model import BaseTableModel


class Category(BaseTableModel):
    __tablename__ = "categories"

    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
