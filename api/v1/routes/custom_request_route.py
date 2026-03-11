"""Custom Request Routes"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.schemas.custom_request import CustomRequestCreate, CustomRequestUpdate
from api.v1.services.custom_request import custom_request_service

custom_requests = APIRouter(prefix="/custom-requests", tags=["Custom Requests"])


@custom_requests.get("", status_code=status.HTTP_200_OK)
def get_all_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    items = custom_request_service.get_all(db, status_filter=status_filter, search=search)
    result = [
        {
            "id": cr.id, "full_name": cr.full_name, "email": cr.email,
            "phone_number": cr.phone_number, "description": cr.description,
            "status": cr.status, "created_at": str(cr.created_at) if cr.created_at else None,
        }
        for cr in items
    ]
    return success_response(status_code=status.HTTP_200_OK, message="Custom requests retrieved successfully", data=result)


@custom_requests.post("", status_code=status.HTTP_201_CREATED)
def create_request(data: CustomRequestCreate, db: Session = Depends(get_db)):
    cr = custom_request_service.create(db, **data.model_dump())
    return success_response(status_code=status.HTTP_201_CREATED, message="Custom request created successfully",
        data={"id": cr.id, "full_name": cr.full_name, "status": cr.status})


@custom_requests.patch("/{request_id}/status", status_code=status.HTTP_200_OK)
def update_request_status(request_id: str, new_status: str = Query(...), db: Session = Depends(get_db)):
    cr = custom_request_service.update_status(db, request_id, new_status)
    return success_response(status_code=status.HTTP_200_OK, message="Request status updated",
        data={"id": cr.id, "status": cr.status})


@custom_requests.delete("/{request_id}", status_code=status.HTTP_200_OK)
def delete_request(request_id: str, db: Session = Depends(get_db)):
    custom_request_service.delete(db, request_id)
    return success_response(status_code=status.HTTP_200_OK, message="Custom request deleted successfully")
