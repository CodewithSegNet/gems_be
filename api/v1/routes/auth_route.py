"""Auth Routes"""

from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random, time, threading

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user, create_access_token
from api.v1.schemas.auth import LoginRequest, SignUpRequest
from api.v1.services.auth import auth_service
from api.v1.services.auth import pwd_context
from api.v1.models.user import User
from api.v1.services.email import send_welcome_email, send_login_notification, send_otp_email

auth = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory OTP store: { email: { "code": "123456", "expires": timestamp } }
_otp_store: dict = {}


class OTPRequest(BaseModel):
    email: str


class OTPVerifyRequest(BaseModel):
    email: str
    otp: str


class CheckEmailRequest(BaseModel):
    email: str


@auth.post("/check-email", status_code=status.HTTP_200_OK)
def check_email(request: CheckEmailRequest, db: Session = Depends(get_db)):
    """Check if an email is registered before sending OTP."""
    email = request.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email. Please create an account first.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Email is registered",
        data={"exists": True, "email": email},
    )


@auth.post("/send-otp", status_code=status.HTTP_200_OK)
def send_otp(request: OTPRequest, background_tasks: BackgroundTasks):
    """Send a 6-digit OTP to the user's email."""
    email = request.email.strip().lower()
    code = str(random.randint(100000, 999999))
    _otp_store[email] = {"code": code, "expires": time.time() + 600}  # 10 min expiry

    # Fire SendGrid email in a separate thread so the API responds instantly
    def _send_in_thread():
        try:
            result = send_otp_email(email, code)
            if not result:
                print(f"[OTP] SendGrid thread failed for {email}, will retry in background task")
        except Exception as e:
            print(f"[OTP] SendGrid thread error for {email}: {e}")

    thread = threading.Thread(target=_send_in_thread, daemon=True)
    thread.start()

    # Also queue a BackgroundTasks retry as safety net (runs after response)
    background_tasks.add_task(_background_retry_otp, email, code)

    print(f"[OTP] Code for {email}: {code}")

    return success_response(
        status_code=status.HTTP_200_OK,
        message="OTP sent to your email",
        data={"email": email},
    )


def _background_retry_otp(email: str, code: str):
    """Background task safety net: wait a bit, then retry if the OTP is still pending."""
    import time as _time
    _time.sleep(5)  # Wait 5 seconds for the thread to finish
    # Only retry if the OTP is still in the store (not yet verified)
    if email in _otp_store and _otp_store[email].get("code") == code:
        print(f"[BACKGROUND] Retrying OTP for {email} via SendGrid as safety net...")
        try:
            send_otp_email(email, code)
        except Exception:
            pass


@auth.post("/verify-otp", status_code=status.HTTP_200_OK)
def verify_otp(request: OTPVerifyRequest):
    """Verify the OTP code."""
    email = request.email.strip().lower()
    otp = request.otp.strip()

    stored = _otp_store.get(email)
    if not stored:
        raise HTTPException(status_code=400, detail="No OTP found. Please request a new one.")
    if time.time() > stored["expires"]:
        _otp_store.pop(email, None)
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")
    if stored["code"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")

    _otp_store.pop(email, None)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="OTP verified successfully",
        data={"verified": True},
    )


@auth.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    user = auth_service.register(
        db=db,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
    )
    login_result = auth_service.login(db=db, email=request.email)
    # Send welcome email
    try:
        send_welcome_email(request.email, request.first_name)
    except Exception:
        pass
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Account created successfully",
        data=login_result,
    )


@auth.post("/login", status_code=status.HTTP_200_OK)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    result = auth_service.login(db=db, email=request.email)
    # Send login notification
    try:
        user = db.query(User).filter(User.email == request.email).first()
        send_login_notification(request.email, user.first_name if user else None)
    except Exception:
        pass
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Login successful",
        data=result,
    )


class AdminLoginRequest(BaseModel):
    email: str
    password: str


@auth.post("/admin-login", status_code=status.HTTP_200_OK)
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """Admin login with email and password."""
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access only")

    token = create_access_token(data={
        "user_id": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
    })

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Admin login successful",
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": user.is_admin,
            },
        },
    )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@auth.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(request: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Change admin password. Requires current password verification."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access only")
    if not current_user.password_hash or not pwd_context.verify(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    current_user.password_hash = pwd_context.hash(request.new_password)
    db.commit()

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Password changed successfully",
    )


class UpdateCredentialsRequest(BaseModel):
    current_password: str
    new_password: str | None = None
    new_email: str | None = None


@auth.post("/update-credentials", status_code=status.HTTP_200_OK)
def update_credentials(request: UpdateCredentialsRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update admin credentials (email and/or password). Requires current password verification."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access only")
    if not current_user.password_hash or not pwd_context.verify(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    changes = []

    # Update email if provided
    if request.new_email and request.new_email.strip().lower() != current_user.email:
        new_email = request.new_email.strip().lower()
        # Check uniqueness
        existing = db.query(User).filter(User.email == new_email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="This email is already in use by another account")
        current_user.email = new_email
        changes.append("email")

    # Update password if provided
    if request.new_password:
        if len(request.new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        current_user.password_hash = pwd_context.hash(request.new_password)
        changes.append("password")

    if not changes:
        raise HTTPException(status_code=400, detail="No changes provided")

    db.commit()
    db.refresh(current_user)

    # Issue a new JWT token with updated email
    new_token = create_access_token(data={
        "user_id": current_user.id,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
    })

    return success_response(
        status_code=status.HTTP_200_OK,
        message=f"Admin {' and '.join(changes)} updated successfully",
        data={
            "email": current_user.email,
            "access_token": new_token,
            "changes": changes,
        },
    )


@auth.get("/me", status_code=status.HTTP_200_OK)
def get_me(current_user: User = Depends(get_current_user)):
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User retrieved successfully",
        data={
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "is_admin": current_user.is_admin,
        },
    )


class GoogleAuthRequest(BaseModel):
    credential: str  # Google ID token from frontend


GOOGLE_CLIENT_ID = "2743210259-u898dfmtgclmn56ug5jbjbtvidbmfb6s.apps.googleusercontent.com"


@auth.post("/google", status_code=status.HTTP_200_OK)
def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth. Create user if doesn't exist."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    try:
        idinfo = id_token.verify_oauth2_token(
            request.credential, google_requests.Request(), GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=60
        )
    except ValueError as e:
        print(f"[GOOGLE AUTH] Token verification ValueError: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")
    except Exception as e:
        print(f"[GOOGLE AUTH] Token verification error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")

    email = idinfo.get("email", "").lower().strip()
    first_name = idinfo.get("given_name", "")
    last_name = idinfo.get("family_name", "")

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        import uuid
        user = User(
            email=email,
            password_hash=pwd_context.hash(uuid.uuid4().hex),  # random password
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # Send welcome email
        try:
            send_welcome_email(email, first_name)
        except Exception:
            pass

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_access_token(data={
        "user_id": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
    })

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Google login successful",
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": user.is_admin,
            },
        },
    )

