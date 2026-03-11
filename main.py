import sys
import uvicorn, os, time
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from collections import defaultdict

from api.db.database import get_db, create_database
from api.v1.models import *  # noqa: F401, F403 — import all models to register them
from api.utils.success_response import success_response
from api.v1.routes import api_version_one
from api.utils.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all database tables on startup
    create_database()
    
    # Seed initial data
    db = next(get_db())
    try:
        seed_database(db)
    except Exception as e:
        print(f"Seeding info: {e}")
    finally:
        db.close()

    yield


app = FastAPI(lifespan=lifespan, title="Gems Ore API", version="1.0.0")


MEDIA_DIR = "./media"
os.makedirs(MEDIA_DIR, exist_ok=True)

TEMP_DIR = "./tmp/media"
os.makedirs(TEMP_DIR, exist_ok=True)

# Load up media static files
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
app.mount("/tmp/media", StaticFiles(directory=TEMP_DIR), name="tmp-media")

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://www.gemsore.com",
    "https://www.gemsore.com/",
    "https://gemsore.com"
]


# Middleware to track request counts
request_counter = defaultdict(lambda: defaultdict(int))


class RequestCountMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        endpoint = request.url.path
        ip_address = request.client.host
        request_counter[endpoint][ip_address] += 1
        response = await call_next(request)
        return response


app.add_middleware(RequestCountMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    formatted_process_time = f"{process_time:.3f}s"
    client_ip = request.client.host
    method = request.method
    url = request.url.path
    status_code = response.status_code
    log_string = f'{client_ip} - "{method} {url} HTTP/1.1" {status_code} - {formatted_process_time}'
    print(log_string)
    return response


app.include_router(api_version_one)


@app.get("/", tags=["Home"])
async def get_root(request: Request) -> dict:
    return success_response(message="Welcome to Gems Ore API", status_code=status.HTTP_200_OK)


# REGISTER EXCEPTION HANDLERS
@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": False, "status_code": exc.status_code, "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    errors = [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]} for error in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"status": False, "status_code": 422, "message": "Invalid input", "errors": errors},
    )


@app.exception_handler(IntegrityError)
async def integrity_exception(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=500,
        content={"status": False, "status_code": 500, "message": f"Database integrity error: {exc}"},
    )


@app.exception_handler(Exception)
async def exception(request: Request, exc: Exception):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    print(f"[ERROR] {exc}, {exc_type} line {exc_tb.tb_lineno if exc_tb else '?'}")
    return JSONResponse(
        status_code=500,
        content={"status": False, "status_code": 500, "message": f"An unexpected error occurred: {exc}"},
    )


def seed_database(db):
    """Seed the database with initial categories and an admin user."""
    from api.v1.models.category import Category
    from api.v1.models.user import User
    from api.v1.services.auth import auth_service

    # Seed admin user
    existing_admin = db.query(User).filter(User.email == "admin@gemsore.com").first()
    if not existing_admin:
        auth_service.register(
            db=db,
            email="admin@gemsore.com",
            password="admin123",
            first_name="Admin",
            last_name="Gems Ore",
            is_admin=True,
        )
        print("✅ Admin user seeded: admin@gemsore.com / admin123")

    # Seed default categories
    default_categories = [
        {"name": "Rings", "description": "Beautiful diamond and gemstone rings"},
        {"name": "Necklaces", "description": "Elegant necklaces for all occasions"},
        {"name": "Earrings", "description": "Stunning earrings collection"},
        {"name": "Bracelets", "description": "Luxury bracelets and bangles"},
        {"name": "Pendants", "description": "Decorative pendants and charms"},
    ]

    for cat_data in default_categories:
        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not existing:
            cat = Category(**cat_data)
            db.add(cat)
    
    db.commit()
    print("✅ Default categories seeded")

    # Seed default settings (wallet addresses)
    from api.v1.models.setting import Setting
    default_settings = {
        "btc_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "usdt_erc20": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
        "usdt_bep20": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
        "usdt_trc20": "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE",
    }
    for key, value in default_settings.items():
        existing = db.query(Setting).filter(Setting.key == key).first()
        if not existing:
            db.add(Setting(key=key, value=value))
    db.commit()
    print("✅ Default settings seeded")


if __name__ == "__main__":
    uvicorn.run("main:app", port=7001, reload=True, workers=1, reload_excludes=["logs"])
