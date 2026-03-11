"""Setting Model — key-value store for app configuration"""

from sqlalchemy import Column, String, Text
from api.v1.models.base_model import BaseTableModel


class Setting(BaseTableModel):
    __tablename__ = "settings"

    key = Column(String, nullable=False, unique=True, index=True)
    value = Column(Text, nullable=True)
