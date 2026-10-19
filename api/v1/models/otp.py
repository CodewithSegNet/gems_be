"""OTP Code Model for Multi-Worker and Multi-Process Safety"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from api.v1.models.base_model import BaseTableModel


class OtpCode(BaseTableModel):
    __tablename__ = "otp_codes"

    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
