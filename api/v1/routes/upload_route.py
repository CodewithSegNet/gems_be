"""Upload Routes"""

import os
import shutil
from secrets import token_hex
from fastapi import APIRouter, UploadFile, File, status, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from api.utils.success_response import success_response

upload = APIRouter(prefix="/upload", tags=["Upload"])

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "media")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "avif", "bmp", "tiff", "tif", "heic", "heif", "svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@upload.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)):
    """Upload a single image file."""
    
    # Validate extension
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
    
    # Read content and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 5MB.")
    
    # Save file
    new_filename = f"{token_hex(8)}.{ext}"
    file_path = os.path.join(MEDIA_DIR, new_filename)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Return URL relative to server
    image_url = f"/media/{new_filename}"
    
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Image uploaded successfully",
        data={"url": image_url, "filename": new_filename},
    )


@upload.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_multiple_images(files: List[UploadFile] = File(...)):
    """Upload multiple image files (up to 4)."""
    
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 images allowed")
    
    urls = []
    for file in files:
        ext = file.filename.split(".")[-1].lower() if file.filename else ""
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid file type for {file.filename}")
        
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File {file.filename} too large")
        
        new_filename = f"{token_hex(8)}.{ext}"
        file_path = os.path.join(MEDIA_DIR, new_filename)
        os.makedirs(MEDIA_DIR, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        urls.append(f"/media/{new_filename}")
    
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Images uploaded successfully",
        data={"urls": urls},
    )
