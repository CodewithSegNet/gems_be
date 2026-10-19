"""The database module"""

from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy import create_engine
from api.utils.settings import settings, BASE_DIR


DB_HOST = settings.DB_HOST
DB_PORT = settings.DB_PORT
DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD
DB_NAME = settings.DB_NAME
DB_TYPE = settings.DB_TYPE


def get_db_engine(test_mode: bool = False):
    if DB_TYPE == "sqlite" or test_mode:
        db_name = "test.db" if test_mode else f"{DB_NAME}.db"
        DATABASE_URL = f"sqlite:///{BASE_DIR}/{db_name}"
        return create_engine(
            DATABASE_URL, connect_args={"check_same_thread": False}
        )
    elif DB_TYPE == "postgresql":
        if settings.DB_URL:
            DATABASE_URL = settings.DB_URL
        elif DB_PASSWORD:
            DATABASE_URL = (
                f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )
        else:
            DATABASE_URL = (
                f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )
    else:
        DATABASE_URL = settings.DB_URL or f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    return create_engine(
        DATABASE_URL,
        pool_size=3,          # keep 3 persistent connections (Render free tier)
        max_overflow=5,       # allow 5 burst connections above pool_size
        pool_pre_ping=True,   # validate conn before use — avoids stale conn errors
        pool_recycle=300,     # recycle every 5 min (idle timeout guard)
        connect_args={
            "connect_timeout": 10,
            "application_name": "gemsore-api",
        },
    )


engine = get_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db_session = scoped_session(SessionLocal)

Base = declarative_base()


def create_database():
    try:
        return Base.metadata.create_all(bind=engine)
    except Exception as e:
        err = str(e).lower()
        if "already exists" in err or "uniqueviolation" in err or "duplicate key" in err:
            return None
        raise e


def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()
