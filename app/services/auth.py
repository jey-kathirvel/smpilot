import logging
import smtplib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.security import hash_password, new_reset_token, token_digest, verify_password
from app.config import Settings
from app.models.user import PasswordResetToken, User

logger = logging.getLogger(__name__)
DUMMY_PASSWORD_HASH = hash_password("not-a-real-account-password-123")


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if user and user.is_active and verify_password(password, user.password_hash):
        return user
    if user is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
    return None


def create_password_reset(db: Session, user: User, minutes: int) -> str:
    raw_token = new_reset_token()
    db.execute(update(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)).values(used_at=datetime.now(UTC)))
    db.add(PasswordResetToken(user_id=user.id, token_hash=token_digest(raw_token), expires_at=datetime.now(UTC) + timedelta(minutes=minutes)))
    db.commit()
    return raw_token


def consume_password_reset(db: Session, raw_token: str, new_password: str) -> User | None:
    token = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_digest(raw_token)))
    now = datetime.now(UTC)
    if not token or token.used_at is not None:
        return None
    expires_at = token.expires_at if token.expires_at.tzinfo else token.expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        return None
    user = token.user
    user.password_hash = hash_password(new_password)
    user.session_version += 1
    token.used_at = now
    db.commit()
    return user


def send_password_reset(settings: Settings, recipient: str, reset_url: str) -> bool:
    if not settings.smtp_host or not settings.smtp_from:
        logger.warning("password_reset_email_not_sent_smtp_unconfigured")
        return False
    message = EmailMessage()
    message["Subject"] = "Reset your SMPilot AI password"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(f"Use this link within {settings.password_reset_minutes} minutes to reset your password:\n\n{reset_url}")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
    return True
