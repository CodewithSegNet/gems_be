"""Upload Routes — Cloudinary or local fallback"""

import os
import io
from secrets import token_hex
from fastapi import APIRouter, UploadFile, File, status, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from dotenv import load_dotenv

from api.utils.success_response import success_response

load_dotenv()

upload = APIRouter(prefix="/upload", tags=["Upload"])

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "media")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "avif", "bmp", "tiff", "tif", "heic", "heif", "svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# ---------------------------------------------------------------------------
# Cloudinary setup (optional — falls back to local storage if not configured)
# ---------------------------------------------------------------------------
_cloudinary_ready = False

_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
_api_key = os.getenv("CLOUDINARY_API_KEY", "")
_api_secret = os.getenv("CLOUDINARY_API_SECRET", "")

if _cloud_name and _api_key and _api_secret:
    try:
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(
            cloud_name=_cloud_name,
            api_key=_api_key,
            api_secret=_api_secret,
            secure=True,
        )
        _cloudinary_ready = True
        print(f"☁️  Cloudinary configured (cloud: {_cloud_name})")
    except ImportError:
        print("⚠️  cloudinary package not installed — falling back to local storage")
else:
    print("ℹ️  Cloudinary env vars not set — using local file storage")


def _validate_file(file: UploadFile):
    """Validate file extension."""
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
    return ext


def _upload_to_cloudinary(content: bytes, ext: str) -> str:
    """Upload bytes to Cloudinary and return the secure URL."""
    result = cloudinary.uploader.upload(
        io.BytesIO(content),
        folder="gems-ore",
        resource_type="image",
        format=ext if ext not in ("heic", "heif") else "jpg",
    )
    return result["secure_url"]


def _save_locally(content: bytes, ext: str) -> str:
    """Save file to local media directory and return relative URL."""
    new_filename = f"{token_hex(8)}.{ext}"
    file_path = os.path.join(MEDIA_DIR, new_filename)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
    return f"/media/{new_filename}"


@upload.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)):
    """Upload a single image file."""
    ext = _validate_file(file)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 5MB.")

    if _cloudinary_ready:
        try:
            url = _upload_to_cloudinary(content, ext)
        except Exception as e:
            print(f"⚠️  Cloudinary upload failed ({e}), falling back to local storage")
            url = _save_locally(content, ext)
    else:
        url = _save_locally(content, ext)

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Image uploaded successfully",
        data={"url": url, "filename": url.split("/")[-1]},
    )


@upload.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_multiple_images(files: List[UploadFile] = File(...)):
    """Upload multiple image files (up to 4)."""
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 images allowed")

    urls = []
    for file in files:
        ext = _validate_file(file)
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File {file.filename} too large")

        if _cloudinary_ready:
            try:
                url = _upload_to_cloudinary(content, ext)
            except Exception as e:
                print(f"⚠️  Cloudinary upload failed ({e}), falling back to local storage")
                url = _save_locally(content, ext)
        else:
            url = _save_locally(content, ext)
        urls.append(url)

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Images uploaded successfully",
        data={"urls": urls},
    )


# ---------------------------------------------------------------------------
# Video upload
# ---------------------------------------------------------------------------
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "avi"}
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB


def _validate_video(file: UploadFile):
    """Validate video file extension."""
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid video type. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}")
    return ext


def _upload_video_to_cloudinary(content: bytes, ext: str) -> str:
    """Upload video bytes to Cloudinary and return the secure URL."""
    result = cloudinary.uploader.upload(
        io.BytesIO(content),
        folder="gems-ore/videos",
        resource_type="video",
        format=ext,
    )
    return result["secure_url"]


def _save_video_locally(content: bytes, ext: str) -> str:
    """Save video file to local media directory and return relative URL."""
    new_filename = f"{token_hex(8)}.{ext}"
    video_dir = os.path.join(MEDIA_DIR, "videos")
    os.makedirs(video_dir, exist_ok=True)
    file_path = os.path.join(video_dir, new_filename)
    with open(file_path, "wb") as f:
        f.write(content)
    return f"/media/videos/{new_filename}"


@upload.post("/video", status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...)):
    """Upload a single video file (mp4, webm, mov, avi). Max 50MB."""
    ext = _validate_video(file)
    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(status_code=400, detail="Video too large. Max size is 50MB.")

    if _cloudinary_ready:
        try:
            url = _upload_video_to_cloudinary(content, ext)
        except Exception as e:
            print(f"⚠️  Cloudinary video upload failed ({e}), falling back to local storage")
            url = _save_video_locally(content, ext)
    else:
        url = _save_video_locally(content, ext)

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Video uploaded successfully",
        data={"url": url, "filename": url.split("/")[-1]},
    )
