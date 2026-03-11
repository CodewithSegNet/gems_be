"""Custom Request Service"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.v1.models.custom_request import CustomRequest


class CustomRequestService:

    def get_all(self, db: Session, status_filter: Optional[str] = None,
                search: Optional[str] = None) -> List[CustomRequest]:
        query = db.query(CustomRequest)
        if status_filter and status_filter != "all":
            query = query.filter(CustomRequest.status == status_filter)
        if search:
            query = query.filter(
                (CustomRequest.full_name.ilike(f"%{search}%")) |
                (CustomRequest.email.ilike(f"%{search}%"))
            )
        return query.order_by(CustomRequest.created_at.desc()).all()

    def get_by_id(self, db: Session, request_id: str) -> CustomRequest:
        req = db.query(CustomRequest).filter(CustomRequest.id == request_id).first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom request not found")
        return req

    def create(self, db: Session, **kwargs) -> CustomRequest:
        req = CustomRequest(**kwargs)
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    def update_status(self, db: Session, request_id: str, new_status: str) -> CustomRequest:
        req = self.get_by_id(db, request_id)
        req.status = new_status
        db.commit()
        db.refresh(req)
        return req

    def delete(self, db: Session, request_id: str):
        req = self.get_by_id(db, request_id)
        db.delete(req)
        db.commit()
        return True


custom_request_service = CustomRequestService()
