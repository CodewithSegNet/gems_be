"""Setting Routes"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.setting import Setting

setting_router = APIRouter(prefix="/settings", tags=["Settings"])

# Keys that are exposed publicly (no auth needed)
PUBLIC_KEYS = [
    "btc_address",
    "usdt_erc20",
    "usdt_bep20",
    "usdt_trc20",
    "ngn_to_usd_rate",
    "vat_enabled",
    "vat_rate",
]


def _get_or_create(db: Session, key: str, default: str = "") -> Setting:
    s = db.query(Setting).filter(Setting.key == key).first()
    if not s:
        s = Setting(key=key, value=default)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@setting_router.get("/public", status_code=status.HTTP_200_OK)
def get_public_settings(db: Session = Depends(get_db)):
    """Get public settings (wallet addresses) — no auth required."""
    result = {}
    for key in PUBLIC_KEYS:
        s = db.query(Setting).filter(Setting.key == key).first()
        result[key] = s.value if s else ""
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Public settings retrieved",
        data=result,
    )


@setting_router.get("", status_code=status.HTTP_200_OK)
def get_all_settings(db: Session = Depends(get_db)):
    """Get all settings (admin)."""
    items = db.query(Setting).all()
    result = {s.key: s.value for s in items}
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Settings retrieved",
        data=result,
    )


@setting_router.put("", status_code=status.HTTP_200_OK)
def update_settings(data: Dict[str, str], db: Session = Depends(get_db)):
    """Update multiple settings at once (admin)."""
    for key, value in data.items():
        s = db.query(Setting).filter(Setting.key == key).first()
        if s:
            s.value = value
        else:
            s = Setting(key=key, value=value)
            db.add(s)
    db.commit()
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Settings updated successfully",
        data=data,
    )
