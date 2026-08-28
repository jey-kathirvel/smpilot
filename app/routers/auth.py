import logging

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import csrf_token, require_user, validate_csrf
from app.auth.security import hash_password, validate_password, verify_password
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.auth import authenticate, consume_password_reset, create_password_reset, normalize_email, send_password_reset

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def render(request: Request, template: str, *, status_code: int = 200, **context):
    return templates.TemplateResponse(request, template, {"csrf_token": csrf_token(request), **context}, status_code=status_code)


@router.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return render(request, "login.html", page_title="Log in")


@router.post("/login", include_in_schema=False)
async def login(request: Request, email: str = Form(), password: str = Form(), csrf: str = Form(), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    user = authenticate(db, email, password)
    if not user:
        return render(request, "login.html", page_title="Log in", error="Email or password is incorrect.", email=email, status_code=status.HTTP_400_BAD_REQUEST)
    request.session.clear()
    request.session.update({"user_id": str(user.id), "session_version": user.session_version})
    csrf_token(request)
    return RedirectResponse("/today", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/signup", include_in_schema=False)
async def signup_page(request: Request):
    return render(request, "signup.html", page_title="Sign up")


@router.post("/signup", include_in_schema=False)
async def signup(request: Request, full_name: str = Form(), email: str = Form(), password: str = Form(), confirm_password: str = Form(), csrf: str = Form(), mobile: str = Form(default=""), organization_name: str = Form(default=""), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    errors = validate_password(password)
    if password != confirm_password:
        errors.append("Passwords do not match.")
    try:
        normalized_email = normalize_email(validate_email(email, check_deliverability=False).normalized)
    except EmailNotValidError:
        normalized_email = normalize_email(email)
        errors.append("Enter a valid email address.")
    if db.scalar(select(User.id).where(User.email == normalized_email)):
        errors.append("An account with this email already exists.")
    if errors:
        return render(request, "signup.html", page_title="Sign up", errors=errors, form={"full_name": full_name, "email": email, "mobile": mobile, "organization_name": organization_name}, status_code=status.HTTP_400_BAD_REQUEST)
    user = User(full_name=full_name.strip(), email=normalized_email, password_hash=hash_password(password), mobile=mobile.strip() or None, organization_name=organization_name.strip() or None)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return render(request, "signup.html", page_title="Sign up", errors=["An account with this email already exists."], form={"full_name": full_name, "email": email}, status_code=status.HTTP_400_BAD_REQUEST)
    db.refresh(user)
    request.session.clear()
    request.session.update({"user_id": str(user.id), "session_version": user.session_version})
    csrf_token(request)
    return RedirectResponse("/today", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout", include_in_schema=False)
async def logout(request: Request, csrf: str = Form()):
    validate_csrf(request, csrf)
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/forgot-password", include_in_schema=False)
async def forgot_password_page(request: Request):
    return render(request, "forgot_password.html", page_title="Forgot password")


@router.post("/forgot-password", include_in_schema=False)
async def forgot_password(request: Request, email: str = Form(), csrf: str = Form(), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    settings = get_settings()
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if user:
        token = create_password_reset(db, user, settings.password_reset_minutes)
        reset_url = f"{settings.app_base_url.rstrip('/')}/reset-password"
        try:
            send_password_reset(settings, user.email, reset_url, token)
        except Exception:
            logger.exception("password_reset_email_failed")
    return render(request, "forgot_password.html", page_title="Forgot password", success="If that account exists, password reset instructions have been sent.")


@router.get("/reset-password", include_in_schema=False)
async def reset_password_page(request: Request):
    return render(request, "reset_password.html", page_title="Reset password")


@router.post("/reset-password", include_in_schema=False)
async def reset_password(request: Request, email: str = Form(), reset_code: str = Form(), password: str = Form(), confirm_password: str = Form(), csrf: str = Form(), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    errors = validate_password(password)
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if errors:
        return render(request, "reset_password.html", page_title="Reset password", email=email, errors=errors, status_code=400)
    if not consume_password_reset(db, reset_code.strip(), password, email):
        return render(request, "reset_password.html", page_title="Reset password", email=email, errors=["This reset code is invalid or expired."], status_code=400)
    request.session.clear()
    return RedirectResponse("/login?reset=success", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/profile", include_in_schema=False)
async def profile_page(request: Request, user: User = Depends(require_user)):
    return render(request, "profile.html", page_title="Profile", show_nav=True, user=user)


@router.post("/profile", include_in_schema=False)
async def update_profile(request: Request, full_name: str = Form(), mobile: str = Form(default=""), organization_name: str = Form(default=""), csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    user.full_name = full_name.strip()
    user.mobile = mobile.strip() or None
    user.organization_name = organization_name.strip() or None
    db.commit()
    return RedirectResponse("/profile?saved=true", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/change-password", include_in_schema=False)
async def change_password_page(request: Request, user: User = Depends(require_user)):
    return render(request, "change_password.html", page_title="Change password", show_nav=True, user=user)


@router.post("/change-password", include_in_schema=False)
async def change_password(request: Request, current_password: str = Form(), password: str = Form(), confirm_password: str = Form(), csrf: str = Form(), user: User = Depends(require_user), db: Session = Depends(get_db)):
    validate_csrf(request, csrf)
    errors = validate_password(password)
    if not verify_password(current_password, user.password_hash):
        errors.append("Current password is incorrect.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if errors:
        return render(request, "change_password.html", page_title="Change password", show_nav=True, user=user, errors=errors, status_code=400)
    user.password_hash = hash_password(password)
    user.session_version += 1
    db.commit()
    request.session.clear()
    return RedirectResponse("/login?changed=success", status_code=status.HTTP_303_SEE_OTHER)
