import secrets
import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.security import new_csrf_token
from app.database import get_db
from app.models.user import User


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = new_csrf_token()
        request.session["csrf_token"] = token
    return token


def validate_csrf(request: Request, submitted: str) -> None:
    expected = request.session.get("csrf_token", "")
    if not expected or not secrets.compare_digest(expected, submitted):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    raw_user_id = request.session.get("user_id")
    if not raw_user_id:
        return None
    try:
        user_id = uuid.UUID(raw_user_id)
    except (ValueError, TypeError):
        request.session.clear()
        return None
    user = db.get(User, user_id)
    if not user or not user.is_active or user.session_version != request.session.get("session_version"):
        request.session.clear()
        return None
    return user


def require_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user
