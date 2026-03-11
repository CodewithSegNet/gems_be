import os
from pydantic_settings import BaseSettings
from pathlib import Path


# Use this to build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application config - simplified for Gems Ore jewelry store."""

    PYTHON_ENV: str = os.getenv("PYTHON_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "gems-ore-secret-key-change-in-prod")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days
    JWT_REFRESH_EXPIRY: int = int(os.getenv("JWT_REFRESH_EXPIRY", "30"))

    APP_URL: str = os.getenv("APP_URL", "http://127.0.0.1:7001")
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "pk_test_xxxxxxxxxxxx")
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "sk_test_xxxxxxxxxxxx")
    
    # Database configurations
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_NAME: str = os.getenv("DB_NAME", "gemsore")
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")
    DB_URL: str = os.getenv("DB_URL", "")
    SITE_URL: str = os.getenv("SITE_URL", "https://www.gemsore.com")

    TEMP_DIR: str = os.path.join(BASE_DIR, "tmp", "media")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
