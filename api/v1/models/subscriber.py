"""Subscriber Model"""

from sqlalchemy import Column, String, Boolean
from api.v1.models.base_model import BaseTableModel


class Subscriber(BaseTableModel):
    __tablename__ = "subscribers"

    email = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
