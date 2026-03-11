"""Authentication Service"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext

from api.utils.jwt_handler import create_access_token
from api.v1.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for handling registration and login"""

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def register(self, db: Session, email: str, password: str, first_name: str = None, last_name: str = None, is_admin: bool = False):
        # Check if user already exists
        existing = db.query(User).filter(User.email == email.lower().strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        user = User(
            email=email.lower().strip(),
            password_hash=self.hash_password(password),
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Send welcome email
        try:
            from api.v1.services.email import send_welcome_email
            send_welcome_email(user.email, user.first_name)
        except Exception:
            pass  # Don't block registration if email fails

        return user

    def login(self, db: Session, email: str, password: str):
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not self.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        token = create_access_token(data={
            "user_id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": user.is_admin,
            }
        }

    def get_user_by_id(self, db: Session, user_id: str):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user


# Create singleton instance
auth_service = AuthService()