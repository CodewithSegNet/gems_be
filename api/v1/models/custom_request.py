"""Custom Request Model"""

from sqlalchemy import Column, String, Text
from api.v1.models.base_model import BaseTableModel


class CustomRequest(BaseTableModel):
    __tablename__ = "custom_requests"

    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")
    # 'pending', 'contacted', 'completed'
